"""
Website-management helpers for Moosey CMS.

This module keeps publishable-content discovery, sitemap generation, robots.txt,
and RSS generation in one place so templates, routes, and user code can share
the same rules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import frontmatter
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response
from slugify import slugify

from .lib.cache import cache
from .lib.text import _coerce_datetime, format_rfc822_date, plain_text
from .lib.urls import (
    _as_dict,
    absolute_url,
    build_lock_params_url,
    get_site_url,
    get_web_config,
)
from .md import parse_markdown


def get_feature_config(
    site_data: Optional[Dict[str, Any]], name: str, default_enabled: bool = True
) -> Dict[str, Any]:
    """
    Read feature config from site_data.web.<name>, falling back to site_data.<name>.

    Boolean values are accepted as shorthand:
      sitemap: false -> {"enabled": False}
      sitemap: true  -> {"enabled": True}
    """
    data = _as_dict(site_data)
    web = get_web_config(data)
    raw = web.get(name, data.get(name, {}))

    if raw is False:
        return {"enabled": False}
    if raw is True:
        return {"enabled": True}
    if isinstance(raw, dict):
        return {**raw}
    return {"enabled": default_enabled}


def feature_enabled(
    site_data: Optional[Dict[str, Any]], name: str, default: bool = True
) -> bool:
    return get_feature_config(site_data, name, default).get("enabled", default) is not False


def feature_path(
    site_data: Optional[Dict[str, Any]], name: str, default: str
) -> str:
    config = get_feature_config(site_data, name)
    path = str(config.get("path") or default)
    return path if path.startswith("/") else f"/{path}"


def _date_info(metadata: Dict[str, Any], file: Path) -> Dict[str, Any]:
    raw_date = metadata.get("date")
    date_info = {**raw_date} if isinstance(raw_date, dict) else {}

    if raw_date and not isinstance(raw_date, dict):
        date_info.setdefault("published", raw_date)
    if "published" in metadata:
        date_info.setdefault("published", metadata["published"])

    stats = file.stat()
    date_info["created"] = datetime.fromtimestamp(stats.st_ctime)
    date_info["updated"] = datetime.fromtimestamp(stats.st_mtime)
    return date_info


def _page_datetime(page: Dict[str, Any], *keys: str) -> Optional[datetime]:
    metadata = _as_dict(page.get("metadata"))
    date_info = _as_dict(metadata.get("date"))

    for key in keys:
        if key in date_info:
            parsed = _coerce_datetime(date_info[key])
            if parsed:
                return parsed
        if key in metadata:
            parsed = _coerce_datetime(metadata[key])
            if parsed:
                return parsed
    return None


def _format_sitemap_date(value: Any) -> Optional[str]:
    parsed = _coerce_datetime(value)
    return parsed.date().isoformat() if parsed else None


def _url_for_file(file: Path, content_dir: Path) -> str:
    rel = file.relative_to(content_dir)
    if rel.name == "index.md":
        if rel.parent == Path("."):
            return "/"
        return "/" + rel.parent.as_posix()
    return "/" + rel.with_suffix("").as_posix()


def _fallback_title(file: Path, content_dir: Path) -> str:
    rel = file.relative_to(content_dir)
    if rel.name == "index.md" and rel.parent != Path("."):
        source = rel.parent.name
    elif rel.name == "index.md":
        source = "Home"
    else:
        source = file.stem
    return source.replace("-", " ").replace("_", " ").title()


def _is_skipped_dir(path: Path) -> bool:
    return path.name.startswith(".") or path.name in {"__pycache__", ".git"}


def _iter_markdown_files(content_dir: Path):
    for file in content_dir.rglob("*.md"):
        if any(_is_skipped_dir(part) for part in file.relative_to(content_dir).parents):
            continue
        if file.name.startswith("."):
            continue
        yield file


@cache(ttl=3600 * 24 * 30, maxsize=10000)
def get_content_index(
    content_dir: Path,
    mode: str = "production",
    include_hidden: bool = False,
    include_drafts: Optional[bool] = None,
    include_noindex: bool = True,
    include_external: bool = False,
    render_html: bool = True,
) -> List[Dict[str, Any]]:
    """
    Return a flat index of publishable Markdown content.

    The result is useful for sitemaps, feeds, search indexes, related-post
    blocks, archives, and custom routes.
    """
    content_dir = Path(content_dir).resolve()
    if include_drafts is None:
        include_drafts = mode == "development"

    if not content_dir.exists() or not content_dir.is_dir():
        return []

    pages: List[Dict[str, Any]] = []

    for file in _iter_markdown_files(content_dir):
        try:
            post = frontmatter.load(file)
            metadata = {**post.metadata}
            url = _url_for_file(file, content_dir)

            if metadata.get("draft") is True and not include_drafts:
                continue
            if metadata.get("visible") is False and not include_hidden:
                continue
            if (metadata.get("external_link") or metadata.get("redirect")) and not include_external:
                continue
            if not include_noindex and metadata.get("noindex") is True:
                continue

            date_info = _date_info(metadata, file)
            metadata["date"] = date_info
            metadata.setdefault("slug", slugify(file.parent.name if file.name == "index.md" else file.stem))

            html = parse_markdown(post.content) if render_html else ""
            title = metadata.get("nav_title") or metadata.get("title") or _fallback_title(file, content_dir)
            description = metadata.get("description") or metadata.get("summary") or ""
            excerpt_source = description or html or post.content

            pages.append(
                {
                    "name": title,
                    "title": title,
                    "description": description,
                    "excerpt": plain_text(excerpt_source),
                    "url": url,
                    "is_dir": file.name == "index.md" and url != "/",
                    "source_path": file,
                    "slug": metadata.get("slug"),
                    "metadata": metadata,
                    "date": date_info,
                    "content": post.content,
                    "html": html,
                    "published": _page_datetime({"metadata": metadata}, "published"),
                    "updated": _page_datetime({"metadata": metadata}, "updated"),
                }
            )
        except Exception as exc:
            print(f"Moosey CMS: skipped {file}: {exc}")

    pages.sort(key=lambda page: page["url"])
    return pages


def _sitemap_metadata(page: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    metadata = _as_dict(page.get("metadata"))
    page_config = metadata.get("sitemap")
    page_config = page_config if isinstance(page_config, dict) else {}

    return {
        "changefreq": page_config.get("changefreq")
        or metadata.get("changefreq")
        or config.get("default_changefreq"),
        "priority": page_config.get("priority")
        or metadata.get("priority")
        or ("1.0" if page.get("url") == "/" else config.get("default_priority", "0.5")),
    }


@cache(maxsize=500)
def _build_sitemap_xml(
    content_dir: Path,
    mode: str,
    config: Dict[str, Any],
    base_url: str,
) -> bytes:
    pages = get_content_index(
        content_dir=content_dir,
        mode=mode,
        include_hidden=bool(config.get("include_hidden", False)),
        include_drafts=bool(config.get("include_drafts", False)),
        include_noindex=False,
        render_html=False,
    )

    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    for page in pages:
        metadata = _as_dict(page.get("metadata"))
        if metadata.get("sitemap") is False:
            continue

        lock_params = _as_dict(metadata.get("lock_params"))
        if isinstance(lock_params, dict):
            active_params = {k for k in lock_params if k not in ("_sitemap_list_", "_fileset_list_")}
            if active_params:
                if lock_params.get("_sitemap_list_"):
                    page_url = build_lock_params_url(page["url"], lock_params)
                else:
                    continue
            else:
                page_url = page["url"]
        else:
            page_url = page["url"]

        url_el = ET.SubElement(root, "url")
        ET.SubElement(url_el, "loc").text = absolute_url(page_url, base_url)

        lastmod = _format_sitemap_date(_page_datetime(page, "updated", "published", "created"))
        if lastmod:
            ET.SubElement(url_el, "lastmod").text = lastmod

        sitemap_meta = _sitemap_metadata(page, config)
        if sitemap_meta.get("changefreq"):
            ET.SubElement(url_el, "changefreq").text = str(sitemap_meta["changefreq"])
        if sitemap_meta.get("priority") is not None:
            ET.SubElement(url_el, "priority").text = str(sitemap_meta["priority"])

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


async def sitemap_response(request: Request, content_dir: Path, mode: str) -> Response:
    site_data = request.app.state.site_data
    config = get_feature_config(site_data, "sitemap")
    base_url = get_site_url(request, site_data)
    xml = _build_sitemap_xml(content_dir, mode, config, base_url)
    return Response(content=xml, media_type="application/xml")


async def robots_response(request: Request, mode: str) -> PlainTextResponse:
    site_data = request.app.state.site_data
    config = get_feature_config(site_data, "robots")
    sitemap_config = get_feature_config(site_data, "sitemap")
    mode_config = config.get(mode) if isinstance(config.get(mode), dict) else None

    if mode_config is None:
        mode_config = {"disallow": ["/"]} if mode in {"staging", "testing"} else {"allow": ["/"], "disallow": []}

    user_agent = mode_config.get("user_agent") or config.get("user_agent") or "*"
    lines = [f"User-agent: {user_agent}"]

    disallow = mode_config.get("disallow", config.get("disallow", []))
    allow = mode_config.get("allow", config.get("allow", []))

    if not disallow and not allow:
        lines.append("Disallow:")
    for path in disallow:
        lines.append(f"Disallow: {path}")
    for path in allow:
        lines.append(f"Allow: {path}")

    for line in mode_config.get("extra_lines", config.get("extra_lines", [])):
        lines.append(str(line))

    if sitemap_config.get("enabled", True) is not False:
        sitemap_path = feature_path(site_data, "sitemap", "/sitemap.xml")
        lines.append(f"Sitemap: {absolute_url(sitemap_path, get_site_url(request, site_data))}")

    return PlainTextResponse(content="\n".join(lines) + "\n", media_type="text/plain")


def _filter_feed_pages(pages: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    collection = config.get("collection") or config.get("content_path")
    include_sections = bool(config.get("include_sections", False))

    if collection:
        prefix = "/" + str(collection).strip("/")
        if prefix == "/.":
            prefix = "/"
        pages = [
            page
            for page in pages
            if page["url"] == prefix or page["url"].startswith(prefix.rstrip("/") + "/")
        ]

    filtered = []
    for page in pages:
        metadata = _as_dict(page.get("metadata"))
        if page.get("is_dir") and not include_sections:
            continue
        if metadata.get("feed") is False or metadata.get("rss") is False:
            continue
        filtered.append(page)

    filtered.sort(
        key=lambda page: _page_datetime(page, "published", "updated", "created") or datetime.min,
        reverse=True,
    )

    limit = int(config.get("limit", 50))
    return filtered[:limit]


@cache(maxsize=500)
def _build_feed_xml(
    content_dir: Path,
    mode: str,
    config: Dict[str, Any],
    base_url: str,
    site_name: str,
    site_description: str,
    site_author: Any,
) -> bytes:
    pages = get_content_index(
        content_dir=content_dir,
        mode=mode,
        include_hidden=bool(config.get("include_hidden", False)),
        include_drafts=bool(config.get("include_drafts", False)),
        include_noindex=False,
        render_html=config.get("content", "excerpt") == "full",
    )
    pages = _filter_feed_pages(pages, config)

    rss = ET.Element("rss")
    rss.set("version", "2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = str(config.get("title") or f"{site_name} Feed")
    ET.SubElement(channel, "link").text = absolute_url(config.get("link", "/"), base_url)
    ET.SubElement(channel, "description").text = str(
        config.get("description") or site_description or ""
    )
    ET.SubElement(channel, "generator").text = "Moosey CMS"

    if pages:
        newest = _page_datetime(pages[0], "published", "updated", "created")
        if newest:
            ET.SubElement(channel, "lastBuildDate").text = format_rfc822_date(newest)

    for page in pages:
        metadata = _as_dict(page.get("metadata"))
        item = ET.SubElement(channel, "item")
        page_url = absolute_url(page["url"], base_url)

        ET.SubElement(item, "title").text = str(page.get("title") or page.get("name") or page["url"])
        ET.SubElement(item, "link").text = page_url
        ET.SubElement(item, "guid", isPermaLink="true").text = page_url

        description = page.get("description") or page.get("excerpt") or ""
        if config.get("content") == "full" and page.get("html"):
            description = page["html"]
        ET.SubElement(item, "description").text = str(description)

        author = metadata.get("author") or site_author
        if author:
            ET.SubElement(item, "author").text = str(author)

        pub_date = _page_datetime(page, "published", "updated", "created")
        if pub_date:
            ET.SubElement(item, "pubDate").text = format_rfc822_date(pub_date)

        for tag in metadata.get("tags", []) or []:
            ET.SubElement(item, "category").text = str(tag)

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)


async def feed_response(request: Request, content_dir: Path, mode: str) -> Response:
    site_data = request.app.state.site_data
    config = get_feature_config(site_data, "feed")
    base_url = get_site_url(request, site_data)
    xml = _build_feed_xml(
        content_dir,
        mode,
        config,
        base_url,
        str(site_data.get("name") or "Moosey CMS Site"),
        str(site_data.get("description") or ""),
        site_data.get("author"),
    )
    return Response(content=xml, media_type="application/rss+xml")


def register_web_routes(
    router: APIRouter,
    dirs: Dict[str, Path],
    mode: str,
    site_data: Optional[Dict[str, Any]],
) -> None:
    """Register built-in website-management routes before the catch-all route."""
    content_dir = dirs["content"]

    if feature_enabled(site_data, "sitemap", True):
        sitemap_path = feature_path(site_data, "sitemap", "/sitemap.xml")

        @router.get(sitemap_path, include_in_schema=False)
        async def moosey_sitemap(request: Request):
            return await sitemap_response(request, content_dir, mode)

    if feature_enabled(site_data, "robots", True):
        robots_path = feature_path(site_data, "robots", "/robots.txt")

        @router.get(robots_path, include_in_schema=False)
        async def moosey_robots(request: Request):
            return await robots_response(request, mode)

    if feature_enabled(site_data, "feed", True):
        feed_path = feature_path(site_data, "feed", "/feed.xml")

        @router.get(feed_path, include_in_schema=False)
        async def moosey_feed(request: Request):
            return await feed_response(request, content_dir, mode)

        feed_config = get_feature_config(site_data, "feed")
        if feed_config.get("rss_alias", True) and feed_path != "/rss.xml":

            @router.get("/rss.xml", include_in_schema=False)
            async def moosey_rss(request: Request):
                return await feed_response(request, content_dir, mode)
