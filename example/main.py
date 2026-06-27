"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT

 example/main.py
 ===============

 A fully-commented reference implementation showing how to integrate
 Moosey CMS into a FastAPI application.

 This file covers:
   - Basic Moosey CMS initialisation
   - Custom Jinja2 globals registered via moosey_env
   - A custom FastAPI route that renders through the Moosey template
     environment (getting all filters, globals, and the seo() helper)
   - Lifespan-safe guard so init_cms only runs once per process
   - Static file mounting
   - Reload delay for build-step coordination in development
"""

# ---------------------------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------------------------
from pathlib import Path

# ---------------------------------------------------------------------------
# FastAPI – ASGI web framework
# ---------------------------------------------------------------------------
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Moosey CMS – the one import you need
# ---------------------------------------------------------------------------
from moosey_cms import init_cms

# ===========================================================================
# APPLICATION SETUP
# ===========================================================================

# Create the FastAPI application instance.
# Moosey CMS plugs into this instance by registering routes, middleware,
# the hot-reload WebSocket (in development mode), and the file watcher.
app = FastAPI()

# ===========================================================================
# DIRECTORY LAYOUT
# ===========================================================================
# Moosey uses a convention-over-configuration file structure.
#
#   example/
#   ├── main.py               <-- This file
#   ├── content/              <-- Markdown files with YAML frontmatter
#   │   ├── index.md          <-- Homepage (served at /)
#   │   ├── about.md          <-- Served at /about
#   │   ├── pages/            <-- Section with its own index
#   │   │   └── features.md   <-- Served at /pages/features
#   │   └── posts/            <-- Blog section
#   │       ├── index.md      <-- Blog listing (served at /posts)
#   │       └── building-modern-apps.md
#   └── templates/            <-- Jinja2 templates matched by the Waterfall
#       ├── layout/
#       │   └── base.html     <-- Shared base layout (extends from here)
#       ├── index.html        <-- Homepage layout
#       ├── page.html         <-- Generic fallback page layout
#       ├── post.html         <-- Single blog-post layout
#       ├── posts.html        <-- Blog listing layout
#       └── 404.html          <-- 404 error page

BASE_DIR = Path(__file__).resolve().parent         # example/
CONTENT_DIR = BASE_DIR / "content"                  # example/content/
TEMPLATES_DIR = BASE_DIR / "templates"              # example/templates/

# ===========================================================================
# STATIC FILES
# ===========================================================================
# Mount a static-files directory so CSS, images, and client-side JS can be
# served at /static/<path>.
#
# Note: The Moosey hot-reload script (moosey_cms/static/js/reload-script.js)
# is injected automatically by init_cms in development mode. You do NOT
# need to serve it yourself.

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ===========================================================================
# GLOBAL SITE DATA
# ===========================================================================
# The site_data dictionary is injected into every template as a Jinja2 global.
# You can access it as {{ site_data }} anywhere in your templates or Markdown.
#
# Recommended keys:
#   name         – Site name (used in {{ seo() }} as og:site_name)
#   description  – Default meta description
#   author       – Default author (used in JSON-LD and Twitter Cards)
#   keywords     – Default SEO keywords (comma-separated string or list)
#   open_graph   – Dict with at least og_image for social preview images
#   social       – Dict with twitter, github, etc. (URLs -> template links)
#
# You can add ANY custom keys here. They are all available as template globals.
# For example, navigation trees, brand colours, CTA config, or helper
# functions (see the country_lookup pattern in advanced-features.md).

site_data = {
    # -- Core branding --------------------------------------------------
    "name": "Moosey",
    "description": "A site built with Moosey CMS",
    "author": "Jane Doe",
    "keywords": ["fastapi", "cms", "python"],

    # -- OpenGraph / Social preview -------------------------------------
    # Used by {{ seo() }} to generate og:image, twitter:image, etc.
    "open_graph": {
        "og_image": "/static/cover.jpg",
    },

    # -- Social profile links -------------------------------------------
    # Rendered in the footer or header of base.html.
    "social": {
        "twitter": "https://x.com/myhandle",
        "github": "https://github.com/myhandle",
    },

    # -- Custom: navigation tree for the header -------------------------
    # These are iterated in layout/base.html to build the nav bar.
    # Putting navs in site_data means you can edit them in one place
    # without touching every content file.
    "navs": [
        {"href": "/about", "label": "About"},
        {"href": "/pages/features", "label": "Features"},
        {"href": "/posts", "label": "Blog"},
    ],
}

# ===========================================================================
# LIFESPAN-SAFE INITIALISATION GUARD
# ===========================================================================
# Wrapping app construction in a FastAPI lifespan context or running behind
# hot-reload (uvicorn --reload) can call module-level code more than once.
# This guard ensures init_cms runs exactly one time per process, avoiding
# duplicate middleware, routes, watcher threads, or WebSocket connections.
#
# Usage (modern FastAPI lifespan):
#
#   @app.on_event("startup")
#   async def startup():
#       init_cms_once(app)
#
# or the newer @asynccontextmanager lifespan.
#
# For simple scripts you can call init_cms directly without the guard.

def init_cms_once(app):
    """Call init_cms only once per process. Idempotent."""
    if not getattr(app.state, "cms_initialized", False):
        init_cms(
            app=app,
            host="localhost",
            port=8000,
            dirs={
                "content": CONTENT_DIR,
                "templates": TEMPLATES_DIR,
            },
            # mode="production" disables hot-reload and enables the
            # 30-day TTL cache. mode="development" (shown here) clears
            # the cache on every request and registers the /ws/hot-reload
            # WebSocket for instant browser refreshes.
            mode="development",

            # site_data is injected as a Jinja2 global into every template.
            # See the dict above for what it contains.
            site_data=site_data,

            # reload_delay: seconds to wait between a file change and the
            # hot-reload broadcast.  Bump this if a build step (Tailwind,
            # esbuild) runs after save and you want the browser to wait
            # until assets are ready.
            reload_delay=0.0,
        )
        app.state.cms_initialized = True

# ===========================================================================
# BOOTSTRAP MOOSEY CMS
# ===========================================================================
# This call registers everything Moosey needs:
#   - The catch-all route at /{full_path:path}
#   - The file watcher (all content & template dirs)
#   - Security headers middleware (X-Content-Type-Options, etc.)
#   - Hot-reload middleware + WebSocket (only in development mode)
#   - All Jinja2 filters (fancy_date, slugify, read_time, seo, …)
#   - Template globals (site_data, mode, seo, …)

init_cms_once(app)

# ===========================================================================
# CUSTOM FASTAPI ROUTE (Optional – demonstrates app.state.templates)
# ===========================================================================
# After init_cms runs, app.state.templates holds the fully configured
# Jinja2Templates instance.  You can use it in your own routes to get
# all Moosey filters (fancy_date, slugify, read_time, …) and the
# seo() global for free – without re-registering anything.
#
# This is useful for:
#   - Pages served from a database instead of Markdown files
#   - JSON API endpoints that return rendered HTML fragments
#   - Hybrid apps that mix CMS-managed content with custom views

@app.get("/custom-greeting")
async def custom_greeting(request: Request):
    """
    Render a custom page using the Moosey template environment.

    Because we use app.state.templates (set by init_cms), this template
    can extend layout/base.html, use {{ seo() }}, apply Moosey filters,
    and access {{ site_data }} – exactly like any Moosey-managed page.
    """
    # Retrieve the Moosey-configured Jinja2Templates instance.
    # Only available *after* init_cms has been called.
    templates = request.app.state.templates

    # We must always pass 'request' to TemplateResponse.
    context = {
        "request": request,
        "title": "Custom Route Demo",
        "description": "This page is rendered by a hand-written FastAPI route, "
                       "but it uses the Moosey template environment so all "
                       "filters (fancy_date, read_time, slugify, …), globals "
                       "(site_data, mode, …), and {{ seo() }} work out of the box.",
    }

    return templates.TemplateResponse(
        name="page.html",   # Any template in TEMPLATES_DIR
        context=context,
    )

# ===========================================================================
# ADDING RUNTIME JINJA2 GLOBALS
# ===========================================================================
# If you need to register additional globals or filters after init_cms,
# access the raw Jinja2 environment via app.state.moosey_env.

env = app.state.moosey_env  # The Jinja2 Environment object
env.globals["current_year"] = 2026  # Available in all templates as {{ current_year }}

# ===========================================================================
# RUN
# ===========================================================================
# Start the server:
#   $ uvicorn example.main:app --reload
#
# Or from the project root:
#   $ uv run uvicorn example.main:app --reload
#
# Visit http://localhost:8000 to see the demo site.
