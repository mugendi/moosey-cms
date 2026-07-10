"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import asyncio
from pathlib import Path
from inflection import singularize
from fastapi import APIRouter, Request
from pprint import pprint

from fastapi.templating import Jinja2Templates

from . import filters
from . import helpers
from . import site
from . import schemas
from . import admin
from . import images as images_module

from .cache import clear_cache_on_file_change, clear_cache
from .file_watcher import start_watching
from .hot_reload_script import inject_script_middleware


from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.ext import Extension
from markupsafe import Markup
import re


async def async_template_response(templates, name, context, status_code=200):
    template = templates.get_template(name)
    rendered = await template.render_async(context)
    return HTMLResponse(content=rendered, status_code=status_code)



class AutoRemoveCommentsExtension(Extension):
    """Automatically removes HTML comments from all included files"""

    def __init__(self, environment):
        super().__init__(environment)

        # Store original include function
        original_include = environment.globals["include"]

        # Create wrapper that removes comments
        def include_no_comments(template_name, **kwargs):
            # Get the included template
            included = environment.get_template(template_name)
            rendered = included.render(**kwargs)
            # Remove comments
            return re.sub(r"<!--.*?-->", "", rendered, flags=re.DOTALL)

        # Replace include function
        environment.globals["include_no_comments"] = include_no_comments


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Iterate over a copy to avoid modification errors
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


from .models import CMSConfig, Dirs, SiteData


def init_cms(
    app,
    host: str,
    port: int,
    dirs: Dirs,
    mode: str,
    site_data: SiteData = {},
    reload_delay: float = 0,
    admin_prefix: str = None,
):
    """
    Initialize the Moosey CMS.

    Args:
        app:          Your FastAPI application instance.
        host:         Server host (used for hot-reload script injection).
        port:         Server port.
        dirs:         Dictionary containing ``content`` and ``templates`` Paths.
        mode:         ``"development"`` (enables hot reload / no cache) or
                      ``"production"``.
        site_data:    Global data (name, author, social links, …).
        reload_delay: Seconds to wait before sending the hot-reload signal to
                      connected browsers.  Useful when a build step runs after
                      a file change and you want the browser to wait until the
                      build has finished before refreshing.  Defaults to ``0``
                      (immediate reload).  Only has an effect in
                      ``"development"`` mode.
        admin_prefix: Route prefix for the admin content-editing API
                      (e.g. ``"admin/content"``).  When set, CRUD endpoints
                      are registered at ``/<prefix>/list``,
                      ``/<prefix>/file/…``, ``/<prefix>/dir/…``.
                      Disabled by default (``None``).
    """

    # validate dirs inputs
    CMSConfig(
        host=host,
        port=port,
        dirs=dirs,
        mode=mode,
        site_data=site_data,
        reload_delay=reload_delay,
        admin_prefix=admin_prefix,
    )

    # Normalise admin_prefix: strip slashes, treat empty string as None
    if admin_prefix:
        admin_prefix = admin_prefix.strip().strip("/") or None

    # resolve paths (static may be a dict with "dir"/"route" keys)
    def _resolve(v):
        if isinstance(v, dict):
            return {**v, "dir": Path(v["dir"]).resolve()}
        return Path(v).resolve()
    dirs = {k: _resolve(v) for k, v in dirs.items()}

    # create templates
    # templates = Jinja2Templates(directory=str(dirs["templates"]))
    templates = Jinja2Templates(
        env=Environment(
            loader=FileSystemLoader(str(dirs["templates"])),
            autoescape=select_autoescape(["html"]),
            enable_async=True,
        ),
    )

    # Important for filters like seo to access them
    app.state.site_data = site_data
    app.state.mode = mode

    # This ensures site_data is available in 404.html and base.html automatically
    templates.env.globals["site_data"] = site_data
    templates.env.globals["mode"] = mode

    # Register all custom filters once
    filters.register_filters(templates.env)

    # Register JSON-LD / schema builders as globals + json_ld filter
    schemas.register(templates.env)

    app.state.moosey_env = templates.env
    app.state.templates = templates

    # Record the user's static dir (if provided) on app.state so the image
    # pipeline route and image-related filters can look source files up.
    # Accept either a Path/str or a dict {"dir": Path, "route": str}.
    static_cfg = dirs.get("static")
    if static_cfg is not None:
        if isinstance(static_cfg, dict):
            static_dir = static_cfg["dir"]
            image_route = static_cfg.get("route", "/__moosey/img")
        else:
            static_dir = static_cfg
            image_route = "/__moosey/img"
        app.state.moosey_static_dir = Path(static_dir).resolve()
        app.state.moosey_image_route_prefix = image_route.rstrip("/") + "/"
        # Register the on-disk image pipeline route.
        images_module.register_routes(app, app.state.moosey_static_dir,
                                      route_prefix=image_route)

    # We need to capture the current event loop to schedule the broadcast
    loop = asyncio.get_event_loop()

    # we want to watch even in production mode
    # The logic is if one does a 'git pull' we want the site content to update
    def on_change_callback(file_path, event_type):
        # 1. Clear the cache (Sync)
        clear_cache_on_file_change(file_path, event_type)

        # 1b. Invalidate image derivatives derived from this file (no-op on
        # non-image files). Wrapped so a non-image path never crashes the
        # watcher.
        try:
            images_module.invalidate(Path(file_path))
        except Exception:
            pass

        # 2. Trigger WebSocket Broadcast (Thread-safe Async call)
        # This tells FastAPI loop to run the broadcast coroutine
        if loop.is_running() and reloader is not None:

            async def _delayed_broadcast():
                if reload_delay > 0:
                    await asyncio.sleep(reload_delay)
                await reloader.broadcast("reload")

            asyncio.run_coroutine_threadsafe(_delayed_broadcast(), loop)

    # start watching dirs with the NEW combined callback
    # (static entry may be a dict with "dir" key - extract the path)
    for d in dirs:
        val = dirs[d]
        if isinstance(val, dict):
            val = val["dir"]
        start_watching(val, on_change_callback)

    reloader = None
    # init manage hot reloading
    if mode == "development":
        reloader = ConnectionManager()
        inject_script_middleware(app, host, port)

    init_routes(
        app=app,
        dirs=dirs,
        templates=templates,
        reloader=reloader,
        mode=mode,
        admin_prefix=admin_prefix,
    )

    return app


def init_routes(app, dirs: Dirs, templates, mode, reloader, admin_prefix=None):

    # init router
    router = APIRouter()

    # middleware to add security headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        # Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Enable XSS protection in older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        return response

    site.register_web_routes(router=router, dirs=dirs, mode=mode, site_data=app.state.site_data)

    # only init hot reload websocket route in dvt mode
    if mode == "development":

        @app.websocket("/ws/hot-reload")
        async def websocket_endpoint(websocket: WebSocket):
            await reloader.connect(websocket)
            try:
                while True:
                    # Keep connection open. We don't really care what the client sends
                    # but we must await receive to keep the socket alive.
                    await websocket.receive_text()
            except WebSocketDisconnect:
                reloader.disconnect(websocket)

    # ------------------------------------------------------------------
    # Admin content-editing API (registered BEFORE the catch-all so
    # its more-specific patterns take priority).
    # ------------------------------------------------------------------
    if admin_prefix:
        admin_router = APIRouter()
        admin.register_admin_routes(
            router=admin_router,
            dirs=dirs,
            mode=mode,
            prefix=admin_prefix,
        )
        app.include_router(admin_router, prefix="")

        # Store the prefix on app.state so downstream code can query it.
        app.state.admin_prefix = admin_prefix

    @router.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(request: Request, full_path: str):

        # If admin routes are enabled, let the admin router handle its
        # own paths — never fall through to the catch-all.
        if admin_prefix and full_path.startswith(admin_prefix):
            return await async_template_response(
                templates, "404.html", {"request": request}, status_code=404
            )

        app = request.app

        mode = app.state.mode

        # if dvt mode, no caches
        if mode == "development":
            clear_cache()

        # 1. Normalize Path
        clean_path = full_path.strip("/")
        if clean_path == "":
            clean_path = "index"

        # 2. Security: Resolve Path
        try:
            target_path_base = helpers.get_secure_target(
                clean_path, relative_to_path=dirs["content"]
            )
        except ValueError:
            # Path traversal detected or invalid chars
            return await async_template_response(
                templates, "404.html", {"request": request}, status_code=404
            )

        # 3. File Resolution Logic
        target_file: Path = None
        is_index: bool = False

        if target_path_base.is_dir():
            target_file = target_path_base / "index.md"
            is_index = True
        else:
            try:
                target_file = helpers.get_secure_target(
                    f"{clean_path}.md", relative_to_path=dirs["content"]
                )
                is_index = False
            except ValueError:
                return await async_template_response(
                    templates, "404.html", {"request": request}, status_code=404
                )

        # 4. Existence Check
        if not target_file.exists():
            return await async_template_response(
                templates, "404.html", {"request": request}, status_code=404
            )

        # 5. Load Content
        # We use utf-8 strictly.
        html_content = None

        # Base template data (globals will be merged by Jinja automatically)
        template_data = {}

        try:
            md_data = helpers.parse_markdown_file(target_file)
            front_matter = md_data.metadata

            # lock_params access control
            lock_params = front_matter.get("lock_params")
            if isinstance(lock_params, dict):
                if not helpers.check_lock_params(lock_params, dict(request.query_params)):
                    return await async_template_response(
                        templates, "404.html", {"request": request}, status_code=404
                    )

            # never render drafts in production
            if front_matter.get("draft") is True and mode != "development":
                return await async_template_response(
                    templates, "404.html", {"request": request}, status_code=404
                )

            # Merge front matter
            template_data = {
                **template_data,
                **front_matter,
                "site_data": app.state.site_data,
            }

            # Render jinja inside frontmatter strings
            for k in front_matter:
                if isinstance(front_matter[k], str):
                    front_matter[k] = await helpers.template_render_content(
                        templates, front_matter[k], template_data, False
                    )

            html_content = md_data.html

            # Render jinja inside markdown body
            html_content = await helpers.template_render_content(
                templates, html_content, template_data, False
            )

            # Always-on sanitize of the rendered body HTML. Honors
            # site_data.sanitize (False = opt-out, dict = overrides). The
            # result is markup so templates can render it raw without ``| safe``,
            # though ``| safe`` remains harmless.
            sanitize_cfg = filters.get_sanitize_config(app.state.site_data)
            if sanitize_cfg and sanitize_cfg.get("auto", True):
                styles = sanitize_cfg.get("styles")
                html_content = filters.sanitize(
                    html_content,
                    **sanitize_cfg["bleach_kwargs"],
                    styles=styles,
                )
            html_content = Markup(html_content)

        except Exception as e:
            print(f"Error rendering content: {e}")
            return await async_template_response(
                templates, "404.html", {"request": request}, status_code=404
            )

        # 6. Determine Context Data (Nav, Breadcrumbs)
        nav_folder = target_file.parent
        current_url = f"/{clean_path}" if clean_path != "index" else "/"
        nav_items = helpers.get_directory_navigation(
            physical_folder=nav_folder,
            current_url=current_url,
            relative_to_path=dirs["content"],
            mode=mode,
        )
        breadcrumbs = helpers.get_breadcrumbs(full_path)

        # 7. Find Template
        search_path = "" if clean_path == "index" else clean_path
        template_name = helpers.find_best_template(
            templates, search_path, is_index_file=is_index, frontmatter=front_matter
        )

        template_data = {**template_data, **md_data}

        def get_files(
            physical_folder=nav_folder,
            current_url=current_url,
            relative_to_path=dirs["content"],
        ):
            physical_folder = Path(physical_folder).resolve()

            return helpers.get_directory_navigation(
                physical_folder=physical_folder,
                current_url=current_url,
                relative_to_path=relative_to_path,
                mode=mode,
            )

        # 8. Render

        context = {
            "app_state": request.app.state,
            "request": request,
            "content": html_content,
            "title": template_data.get(
                "title", clean_path.split("/")[-1].replace("-", " ").title()
            ),
            "breadcrumbs": breadcrumbs,
            "nav_items": nav_items,
            "debug_template_used": template_name,
            "get_files": get_files,
            **template_data,
        }

        return await async_template_response(templates, template_name, context)

    app.include_router(router, prefix="")

    return router


