"""
Path utilities for Moosey CMS.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

import frontmatter
from slugify import slugify

from .cache import cache
from .urls import build_lock_params_url


def make_asset_normalizer(static_dir: str):
    """
    static_dir can be a bare name ("static") or a full absolute
    filesystem path (e.g. "/media/.../backhome-construction/static").
    Either way, incoming asset paths may reference it via:
      - the full absolute path
      - just the basename ("static" / "/static")
      - or already be normalized ("/images/...")
    """
    static_dir = static_dir.rstrip('/')
    static_name = os.path.basename(static_dir)

    candidates = sorted({static_dir, static_name}, key=len, reverse=True)
    alternation = '|'.join(re.escape(c) for c in candidates)
    pattern = re.compile(rf'^/?(?:{alternation})/')

    def normalize(path: str) -> str:
        p = pattern.sub('', path, count=1).strip('/')
        if not p:
            raise ValueError(f"empty asset path after normalization: {path!r}")
        return f'/{p}'

    return normalize


@cache(ttl=3600 * 24 * 30, maxsize=10000)
def get_secure_target(user_path: str, relative_to_path: Path) -> Path:
    """
    Safely resolves a user-provided path against the relative_to_path.

    1. Checks for null bytes (C-string exploit).
    2. Resolves '..' and symlinks to finding the absolute path.
    3. Ensures the resolved path is still inside relative_to_path.
    """
    if "\0" in user_path:
        raise ValueError("Security Alert: Null byte detected in path.")

    clean_path = user_path.strip("/")
    naive_path = relative_to_path / clean_path

    try:
        resolved_path = naive_path.resolve()
    except OSError:
        raise ValueError("Invalid characters in path.")

    if not resolved_path.is_relative_to(relative_to_path):
        raise ValueError(f"Path Traversal Attempt: {user_path}")

    return resolved_path


@cache(ttl=3600 * 24 * 30, maxsize=10000)
def get_directory_navigation(
    physical_folder: Path,
    current_url: str = "/",
    relative_to_path: Path = "/",
    mode: str = "production",
) -> List[Dict[str, Any]]:
    """
    Scans folder for sidebar menu. Supports advanced frontmatter features.
    """
    if not physical_folder.exists() or not physical_folder.is_dir():
        return []

    items = []
    try:
        for entry in physical_folder.iterdir():
            if entry.name.startswith("."):
                continue
            if entry.name == "index.md":
                continue
            if entry.is_dir() and not (entry / "index.md").exists():
                continue

            meta_file = entry / "index.md" if entry.is_dir() else entry

            sort_order = 9999
            display_title = entry.stem.replace("-", " ").title()
            nav_group = None
            external_url = None
            is_visible = True
            target = "_self"
            meta = {}

            try:
                post = frontmatter.load(meta_file)
                meta = post.metadata

                if meta.get("visible") is False:
                    is_visible = False

                if meta.get("draft") is True and mode != "development":
                    is_visible = False

                if not is_visible:
                    continue

                lock_params = meta.get("lock_params")
                if isinstance(lock_params, dict):
                    active_params = {k for k in lock_params if k not in ("_sitemap_list_", "_fileset_list_")}
                    if active_params and not lock_params.get("_fileset_list_"):
                        continue

                if "order" in meta:
                    sort_order = int(meta["order"])

                if "nav_title" in meta:
                    display_title = meta["nav_title"]
                elif "title" in meta:
                    display_title = meta["title"]

                nav_group = meta.get("group") or ""

                if "external_link" in meta:
                    external_url = meta["external_link"]
                    target = "_blank"
                elif "redirect" in meta:
                    external_url = meta["redirect"]

            except Exception:
                pass

            if external_url:
                entry_url = external_url
                is_active = False
            else:
                try:
                    rel_path = entry.relative_to(relative_to_path)
                    url_slug = str(rel_path).replace(".md", "").replace("\\", "/")
                    entry_url = f"/{url_slug}"
                    is_active = entry_url == current_url
                except ValueError:
                    continue

            lock_params = meta.get("lock_params")
            if isinstance(lock_params, dict) and lock_params.get("_fileset_list_"):
                entry_url = build_lock_params_url(entry_url, lock_params)

            items.append(
                {
                    "name": display_title,
                    "url": entry_url,
                    "is_active": is_active,
                    "is_dir": entry.is_dir(),
                    "order": sort_order,
                    "group": nav_group,
                    "target": target,
                    "metadata": meta,
                }
            )

        group_min_orders = {}
        for item in items:
            g = item["group"]
            w = item["order"]
            if g not in group_min_orders or w < group_min_orders[g]:
                group_min_orders[g] = w

        items.sort(
            key=lambda x: (
                group_min_orders[x["group"]],
                x["group"],
                x["order"],
                x["name"],
            )
        )

    except OSError:
        pass

    return items
