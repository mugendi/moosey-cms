"""
URL utilities for Moosey CMS.
"""
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlencode

from fastapi import Request


def absolute_url(value: str, base_url: str) -> str:
    """Resolve a relative site path against a base URL."""
    if not value:
        return ""
    value = str(value)
    if re.match(r"^[a-z][a-z0-9+.-]*:", value, re.IGNORECASE):
        return value
    if value.startswith("#"):
        return value
    return urljoin(base_url.rstrip("/") + "/", value.lstrip("/"))


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def get_web_config(site_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the nested website-management config from site_data."""
    return _as_dict(_as_dict(site_data).get("web"))


def get_site_url(
    request: Optional[Request] = None, site_data: Optional[Dict[str, Any]] = None
) -> str:
    """Resolve the public site URL from config, falling back to the request."""
    data = _as_dict(site_data)
    web = get_web_config(data)
    configured = (
        web.get("site_url")
        or data.get("site_url")
        or data.get("base_url")
        or data.get("url")
    )
    if configured:
        return str(configured).rstrip("/")
    if request is not None:
        return str(request.base_url).rstrip("/")
    return ""


def get_breadcrumbs(url_path: str) -> List[Dict[str, str]]:
    parts = [p for p in url_path.strip("/").split("/") if p]
    crumbs = [{"name": "Home", "url": "/"}]
    current = ""
    for p in parts:
        current += f"/{p}"
        crumbs.append({"name": p.replace("-", " ").title(), "url": current})
    return crumbs


def build_lock_params_url(base_url: str, lock_params: dict) -> str:
    """Append lock_params as query string to base_url (excludes special params)."""
    params = {
        k: str(v) for k, v in lock_params.items()
        if k not in ("_sitemap_list_", "_fileset_list_")
    }
    if not params:
        return base_url
    return f"{base_url}?{urlencode(params)}"


def check_lock_params(lock_params: dict, query_params: dict) -> bool:
    """Return True if query_params satisfies lock_params requirements."""
    required = {
        k: str(v) for k, v in lock_params.items()
        if k not in ("_sitemap_list_", "_fileset_list_")
    }
    if not required:
        return True
    return all(query_params.get(k) == v for k, v in required.items())
