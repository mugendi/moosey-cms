"""
example/advanced/main.py - Advanced Moosey CMS Usage Patterns
===============================================================

This example demonstrates real-world patterns that build on Moosey CMS
without modifying the package itself. Each pattern is self-contained
and heavily documented.

Patterns covered:
  1. Custom sitemap.xml route using app.state.templates
  2. Custom robots.txt route (environment-aware)
  3. Content index helper - walks the full content tree
  4. Custom Jinja2 filters registered at runtime
  5. site_data as a layout config hub
  6. Lifespan-safe initialisation
  7. Nested frontmatter as page-builder data

Run with:
  uv run uvicorn example.advanced.main:app --reload
"""

# ---------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# FastAPI / Starlette
# ---------------------------------------------------------------------------
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Moosey CMS
# ---------------------------------------------------------------------------
from moosey_cms import init_cms, get_files

# ===========================================================================
# DIRECTORY LAYOUT
# ===========================================================================
BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"       # Markdown files in content/
TEMPLATES_DIR = BASE_DIR / "templates"   # Jinja2 templates

# ===========================================================================
# APPLICATION SETUP
# ===========================================================================
app = FastAPI()

# ===========================================================================
# STATIC FILES
# ===========================================================================
STATIC_DIR = BASE_DIR.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ===========================================================================
# SITE DATA - LAYOUT CONFIG HUB
# ===========================================================================
# site_data can hold more than strings.  It is the right place for nav trees,
# CTA configuration, brand fragments, social links, and small helper functions
# that many templates need - all accessible as {{ site_data.key }} everywhere.
site_data = {
    # -- Core branding ---------------------------------------------------
    "name": "Moosey Advanced Demo",
    "description": "Advanced patterns built on Moosey CMS",
    "author": "Jane Doe",
    "keywords": ["fastapi", "cms", "python", "advanced"],

    # -- OpenGraph -------------------------------------------------------
    "open_graph": {"og_image": "/static/cover.jpg"},

    # -- Social ----------------------------------------------------------
    "social": {
        "twitter": "https://x.com/myhandle",
        "github": "https://github.com/myhandle",
    },

    # -- Site URL (used by sitemap and canonical generation) -------------
    "site_url": "http://localhost:8000",

    # -- Navigation tree (used in base.html and custom routes) -----------
    "navs": [
        {"href": "/", "label": "Home"},
        {"href": "/about", "label": "About"},
        {"href": "/posts", "label": "Blog"},
    ],

    # -- CTA configuration -----------------------------------------------
    "cta": {
        "label": "Get Started",
        "href": "https://github.com/mugendi/moosey-cms",
    },

    # -- Robots configuration (environment-aware) ------------------------
    "robots": {
        # In production, allow everything.
        # In staging/testing, disallow all (prevent indexing by search engines).
        # In development, no restrictions.
        "production": {
            "allow": ["/"],
            "disallow": [],
        },
        "staging": {
            "allow": [],
            "disallow": ["/"],
        },
        "testing": {
            "allow": [],
            "disallow": ["/"],
        },
        "development": {
            "allow": ["/"],
            "disallow": [],
        },
    },
}


# ===========================================================================
# LIFESPAN-SAFE INITIALISATION
# ===========================================================================
# When running behind uvicorn --reload or inside an ASGI lifespan context,
# module-level code can execute more than once per process. This guard
# ensures init_cms runs exactly one time, avoiding duplicate routes,
# middleware, watcher threads, or WebSocket connections.

def init_cms_once(app):
    """
    Wrapper that calls init_cms exactly once per process.
    Usage with FastAPI lifespan:
        @app.on_event("startup")
        async def startup():
            init_cms_once(app)
    """
    if not getattr(app.state, "cms_initialized", False):
        init_cms(
            app=app,
            host="localhost",
            port=8000,
            dirs={"content": CONTENT_DIR, "templates": TEMPLATES_DIR},
            mode="development",
            site_data=site_data,
        )
        app.state.cms_initialized = True


init_cms_once(app)


# ===========================================================================
# CUSTOM JINJA2 FILTERS (registered at runtime via moosey_env)
# ===========================================================================
# After init_cms, app.state.moosey_env holds the raw Jinja2 Environment.
# You can register additional filters or globals here - they become available
# in every template automatically.

env = app.state.moosey_env

# -- strip_html: removes all HTML tags from a string ------------------------
# Useful for generating plain-text excerpts for RSS, meta tags, etc.
def strip_html(text):
    import re
    return re.sub(r"<[^>]+>", "", text) if text else ""

env.filters["strip_html"] = strip_html

# -- rfc822_date: formats a datetime for RSS feeds --------------------------
def rfc822_date(dt):
    """Format datetime as RFC 822 string: 'Mon, 15 Jan 2026 18:00:00 GMT'"""
    if not dt:
        return ""
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

env.filters["rfc822_date"] = rfc822_date

# -- absolute_url: resolves a relative path to an absolute URL --------------
def absolute_url(path, base_url=None):
    """Convert relative path to absolute URL using site_data.site_url."""
    if not path:
        return ""
    if path.startswith("http"):
        return path
    if base_url is None:
        base_url = site_data.get("site_url", "http://localhost:8000")
    base = base_url.rstrip("/")
    path = path.lstrip("/")
    return f"{base}/{path}"

env.filters["absolute_url"] = absolute_url

# -- Global helper: current year -------------------------------------------
env.globals["current_year"] = datetime.now().year


# ===========================================================================
# PATTERN 1: CUSTOM SITEMAP.XML ROUTE
# ===========================================================================
# This route walks the content directory and generates a sitemap.xml that
# search engines can use to discover all pages on the site.
#
# It uses get_files() - the same function Moosey uses internally for
# navigation - to enumerate all content paths.

@app.get("/sitemap.xml")
async def sitemap(request: Request):
    """
    Generate a sitemap.xml from all Markdown files in the content directory.

    Uses Moosey's get_files() to walk the content tree and extract:
      - URL (loc)
      - Last modified date (lastmod) -- from file system timestamp
      - Change frequency (changefreq)
      - Priority (priority)

    Returns: XML response with proper content-type.
    """
    # -- Obtain the base URL for constructing absolute URLs --------------
    base_url = str(request.base_url).rstrip("/")

    # -- Build a list of all pages to include in the sitemap ------------
    # We scan the root content directory recursively.
    # get_files returns a list of dicts with .url, .metadata, etc.
    pages = get_files(
        physical_folder=CONTENT_DIR,
        current_url="/",
        relative_to_path=CONTENT_DIR,
    )

    # ====================================================================
    # Build the XML using Python's ElementTree API.
    # We construct:
    #   <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    #     <url>
    #       <loc>https://example.com/page</loc>
    #       <lastmod>2026-01-15</lastmod>
    #       <changefreq>weekly</changefreq>
    #       <priority>0.8</priority>
    #     </url>
    #     ...
    #   </urlset>
    # ====================================================================
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Always include the homepage
    homepage = ET.SubElement(root, "url")
    ET.SubElement(homepage, "loc").text = f"{base_url}/"
    ET.SubElement(homepage, "changefreq").text = "daily"
    ET.SubElement(homepage, "priority").text = "1.0"

    for page in pages:
        # Skip external links (they are not pages on this site)
        if page.get("target") == "_blank":
            continue

        url_elem = ET.SubElement(root, "url")
        ET.SubElement(url_elem, "loc").text = f"{base_url}{page['url']}"

        # lastmod from file system via metadata.date.updated
        date_info = page.get("metadata", {}).get("date", {})
        if date_info and date_info.get("updated"):
            lastmod = date_info["updated"].strftime("%Y-%m-%d")
            ET.SubElement(url_elem, "lastmod").text = lastmod

        # changefreq: daily for sections, monthly for pages
        changefreq = "daily" if page.get("is_dir") else "monthly"
        ET.SubElement(url_elem, "changefreq").text = changefreq

        # priority: sections higher than pages
        priority = "0.8" if page.get("is_dir") else "0.5"
        ET.SubElement(url_elem, "priority").text = priority

    # -- Render the XML tree to a string ---------------------------------
    xml_bytes = ET.tostring(root, encoding="unicode", xml_declaration=True)

    return PlainTextResponse(content=xml_bytes, media_type="application/xml")


# ===========================================================================
# PATTERN 2: CUSTOM ROBOTS.TXT ROUTE
# ===========================================================================
# Generates an environment-aware robots.txt. In production all pages are
# indexable. In staging/testing everything is disallowed to prevent
# inadvertent search-engine indexing of test content.
#
# The rules are read from site_data.robots.

@app.get("/robots.txt")
async def robots(request: Request):
    """
    Generate robots.txt based on the current mode and site_data.robots config.

    The rules differ by environment:
      - production: Allow all
      - staging:    Disallow all
      - testing:    Disallow all
      - development: Allow all
    """
    # -- Determine the current mode (development, production, etc.) ------
    current_mode = request.app.state.mode

    # -- Look up the robot rules for this mode ---------------------------
    # Fall back to a safe default (disallow all) if mode not configured.
    mode_rules = site_data.get("robots", {}).get(
        current_mode,
        {"allow": [], "disallow": ["/"]},
    )

    lines = ["User-agent: *"]
    for path in mode_rules.get("disallow", []):
        lines.append(f"Disallow: {path}")
    for path in mode_rules.get("allow", []):
        lines.append(f"Allow: {path}")

    # -- Always point to the sitemap -------------------------------------
    base_url = str(request.base_url).rstrip("/")
    lines.append(f"Sitemap: {base_url}/sitemap.xml")

    return PlainTextResponse(content="\n".join(lines), media_type="text/plain")


# ===========================================================================
# PATTERN 3: CONTENT INDEX HELPER
# ===========================================================================
# A higher-level wrapper around get_files() that returns all content pages
# in a flat, queryable structure. This is useful for:
#   - Building a search index
#   - Generating RSS feeds
#   - Creating "recent posts" widgets
#   - Building tag/category archive pages
#
# The helper handles draft filtering, visibility, and external link exclusion
# automatically - mirroring Moosey's own navigation logic.

def get_all_content(content_dir=None, mode=None):
    """
    Walk the entire content tree and return a flat list of all pages.

    Each item in the returned list is a dict with:
      .url         – Absolute URL path
      .title       – Page title (nav_title > title > filename-derived)
      .description – From frontmatter
      .slug        – URL-friendly filename stem
      .source_path – Absolute filesystem path to the Markdown file
      .metadata    – Full frontmatter dict
      .date        – Dict with .created and .updated datetimes
      .tags        – List of tags (from frontmatter)
      .image       – Featured image URL (from frontmatter)
      .is_dir      – True if this is a section (directory with index.md)

    Usage:
        pages = get_all_content()
        for p in pages:
            print(p.title, p.url)
    """
    content_dir = content_dir or CONTENT_DIR
    mode = mode or "development"

    # get_files returns already-filtered nav items (drafts hidden in prod,
    # invisible items excluded). We call with the root content dir.
    items = get_files(
        physical_folder=content_dir,
        current_url="/",
        relative_to_path=content_dir,
    )

    # We also discover section indexes (directories) since get_files
    # only returns siblings. We traverse manually to find nested dirs.
    result = []
    for item in items:
        result.append(item)
        # If an item is a directory, recurse into it
        if item.get("is_dir"):
            sub_items = get_files(
                physical_folder=Path(content_dir) / item["url"].lstrip("/"),
                current_url=item["url"],
                relative_to_path=content_dir,
            )
            result.extend(sub_items)

    return result


# ===========================================================================
# PATTERN 4: CUSTOM ROUTE USING CONTENT INDEX
# ===========================================================================
# Demonstrate using the content index to build a JSON endpoint that could
# power client-side search or a dynamic archive page.

@app.get("/api/content-index.json")
async def content_index(request: Request):
    """
    Return all content pages as JSON - useful for client-side search.

    This endpoint:
      1. Walks the full content tree via get_all_content()
      2. Returns a JSON array with URL, title, description, tags, date

    Frontend usage:
      fetch('/api/content-index.json')
        .then(r => r.json())
        .then(pages => { /* build a search UI */ })
    """
    from fastapi.responses import JSONResponse

    mode = request.app.state.mode
    pages = get_all_content(mode=mode)

    output = []
    for page in pages:
        entry = {
            "url": page["url"],
            "title": page.get("name", ""),
            "description": page.get("metadata", {}).get("description", ""),
            "tags": page.get("metadata", {}).get("tags", []),
            "slug": page.get("metadata", {}).get("slug", ""),
        }
        # Include dates if available
        date_info = page.get("metadata", {}).get("date", {})
        if date_info:
            if date_info.get("created"):
                entry["date_created"] = date_info["created"].isoformat()
            if date_info.get("updated"):
                entry["date_updated"] = date_info["updated"].isoformat()
        output.append(entry)

    return JSONResponse(content=output)


# ===========================================================================
# PATTERN 5: NESTED FRONTMATTER - PAGE-BUILDER DATA
# ===========================================================================
# Frontmatter can hold arbitrary nested structures, not just flat metadata.
# This enables page-builder patterns where a Markdown file defines
# structured content (hero sections, card grids, testimonials, process steps)
# that templates can iterate over.
#
# See example/advanced/content/pages/process.md for a live example.

@app.get("/page-builder-demo")
async def page_builder_demo(request: Request):
    """
    Render a page that uses nested frontmatter as structured page data.

    This route loads a Markdown file and passes its nested frontmatter
    arrays to a template that renders hero, cards, process tabs, etc.

    The frontmatter might look like:
    ```yaml
    hero:
      heading: "Build Better"
      cta_label: "Start Now"
    cards:
      - title: "Fast"
        body: "Built on FastAPI"
    ```
    """
    import frontmatter as fm

    md_file = CONTENT_DIR / "pages" / "process.md"
    if not md_file.exists():
        return HTMLResponse("<h1>Page not found</h1>", status_code=404)

    post = fm.load(md_file)

    templates = request.app.state.templates
    context = {
        "request": request,
        "title": post.metadata.get("title", "Page Builder Demo"),
        "description": post.metadata.get("description", ""),
        "hero": post.metadata.get("hero", {}),
        "cards": post.metadata.get("cards", []),
        "process_tabs": post.metadata.get("process_tabs", []),
        "testimonials": post.metadata.get("testimonials", []),
        "content": post.content,  # raw Markdown body (not rendered by Moosey
                                  # in this custom route; use | markdown if
                                  # you need conversion)
    }

    return templates.TemplateResponse("page-builder.html", context)


# ===========================================================================
# SUMMARY OF PATTERNS
# ===========================================================================
# | Pattern                        | File                               |
# |--------------------------------|-------------------------------------|
# | Lifespan-safe init             | init_cms_once() in main.py          |
# | Custom Jinja2 filters          | strip_html, rfc822_date, absolute_url|
# | site_data as config hub        | navs, cta, robots config in dict    |
# | Sitemap.xml                    | /sitemap.xml route                  |
# | Robots.txt (env-aware)         | /robots.txt route                   |
# | Content index / JSON API       | /api/content-index.json route       |
# | Nested frontmatter page data   | /page-builder-demo + templates      |
# | Production deployment pattern  | Makefile with MODE=production        |
#
# To deploy in production:
#   MODE=production uvicorn example.advanced.main:app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("example.advanced.main:app", host="0.0.0.0", port=8000, reload=True)
