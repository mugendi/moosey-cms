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

from .cache import clear_cache_on_file_change, clear_cache
from .file_watcher import start_watching
from .hot_reload_script import inject_script_middleware


from fastapi import WebSocket, WebSocketDisconnect


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


from .models import CMSConfig, Dirs,  SiteData


def init_cms(
    app,
    host: str,
    port: int,
    dirs: Dirs,
    mode: str,
    site_data: SiteData = {},
):

    # validate dirs inputs
    CMSConfig(
        host=host,
        port=port,
        dirs=dirs,
        mode=mode,
        site_data=site_data
    )

    # resolve paths
    dirs = {k: p.resolve() for k, p in dirs.items()}

    # create templates
    # templates = Jinja2Templates(directory=str(dirs["templates"]))
    templates = Jinja2Templates(directory=str(dirs["templates"]), extensions=[])

    # Important for filters like seo to access them
    app.state.site_data = site_data
    app.state.mode = mode

    # This ensures site_data is available in 404.html and base.html automatically
    templates.env.globals["site_data"] = site_data
    templates.env.globals["mode"] = mode

    # Register all custom filters once
    filters.register_filters(templates.env)

    # We need to capture the current event loop to schedule the broadcast
    loop = asyncio.get_event_loop()

    # we want to watch even in production mode
    # The logic is if one does a 'git pull' we want the site content to update
    def on_change_callback(file_path, event_type):
        # 1. Clear the cache (Sync)
        clear_cache_on_file_change(file_path, event_type)

        # 2. Trigger WebSocket Broadcast (Thread-safe Async call)
        # This tells FastAPI loop to run the broadcast coroutine
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(reloader.broadcast("reload"), loop)

    # start watching dirs with the NEW combined callback
    for d in dirs:
        start_watching(dirs[d], on_change_callback)

    reloader = None
    # init manage hot reloading
    if mode == "development":
        reloader = ConnectionManager()
        inject_script_middleware(app, host, port)

    init_routes(app=app, dirs=dirs, templates=templates, reloader=reloader, mode=mode)

    return app


def init_routes(app, dirs: Dirs, templates, mode, reloader):

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

    @router.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(request: Request, full_path: str):

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
            return templates.TemplateResponse(
                "404.html", {"request": request}, status_code=404
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
                return templates.TemplateResponse(
                    "404.html", {"request": request}, status_code=404
                )

        # 4. Existence Check
        if not target_file.exists():
            return templates.TemplateResponse(
                "404.html", {"request": request}, status_code=404
            )

        # 5. Load Content
        # We use utf-8 strictly.
        html_content = None

        # Base template data (globals will be merged by Jinja automatically)
        template_data = {}

        try:
            md_data = helpers.parse_markdown_file(target_file)
            front_matter = md_data.metadata

            # never render drafts in production
            if front_matter.get("draft") is True and mode != "development":
                return templates.TemplateResponse(
                    "404.html", {"request": request}, status_code=404
                )

            # Merge front matter
            template_data = {
                **template_data,
                **front_matter,
                "site_data": app.state.site_data
            }

            # Render jinja inside frontmatter strings
            for k in front_matter:
                if isinstance(front_matter[k], str):
                    front_matter[k] = helpers.template_render_content(
                        templates, front_matter[k], template_data, False
                    )

            html_content = md_data.html

            # Render jinja inside markdown body
            html_content = helpers.template_render_content(
                templates, html_content, template_data, False
            )

        except Exception as e:
            print(f"Error rendering content: {e}")
            return templates.TemplateResponse(
                "404.html", {"request": request}, status_code=404
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

        # pprint(nav_items)

        # 8. Render
        return templates.TemplateResponse(
            template_name,
            {
                "app_state": request.app.state,
                "request": request,
                "content": html_content,
                "title": template_data.get(
                    "title", clean_path.split("/")[-1].replace("-", " ").title()
                ),
                "breadcrumbs": breadcrumbs,
                "nav_items": nav_items,
                "debug_template_used": template_name,
                **template_data,
            },
        )

    app.include_router(router, prefix="")

    return router
