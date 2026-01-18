"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import os
import frontmatter
from pathlib import Path
from typing import List, Dict, Any
from jinja2 import TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment 
from datetime import datetime
from slugify import slugify
from inflection import singularize
from pprint import pprint
from markupsafe import Markup

from .models import Dirs
from .md import parse_markdown
from .cache import cache, cache_fn

from .seo import seo_tags
from . import filters

# We initialize this once. It denies access to dangerous attributes like __class__
_safe_env = SandboxedEnvironment(
    trim_blocks=True,
    lstrip_blocks=True
)

cache_debug = True


def validate_model(MyModel, data):
    if not isinstance(data, MyModel):
        MyModel(**data)
    return data

@cache_fn(debug=cache_debug)
def template_exists(templates, name: str) -> bool:
    try:
        templates.get_template(name)
        return True
    except TemplateNotFound as e:
        return False


@cache_fn(debug=cache_debug)
def get_secure_target(user_path: str, relative_to_path: Path) -> Path:
    """
    Safely resolves a user-provided path against the relative_to_path.

    1. Checks for null bytes (C-string exploit).
    2. Resolves '..' and symlinks to finding the absolute path.
    3. Ensures the resolved path is still inside relative_to_path.
    """
    # Prevent Null Byte Injection
    if "\0" in user_path:
        raise ValueError("Security Alert: Null byte detected in path.")

    # Convert to path and strip leading slashes to ensure it joins correctly
    # e.g., "/etc/passwd" becomes "etc/passwd" (relative)
    clean_path = user_path.strip("/")

    # Create the naive path
    naive_path = relative_to_path / clean_path

    try:
        # Resolve: This converts symlinks and '..' to their real physical location
        resolved_path = naive_path.resolve()
    except OSError:
        # Happens on Windows if path contains illegal chars like < > :
        raise ValueError("Invalid characters in path.")

    # The Firewall: strict check if the result is inside the jail
    if not resolved_path.is_relative_to(relative_to_path):
        raise ValueError(f"Path Traversal Attempt: {user_path}")

    return resolved_path


@cache_fn(debug=cache_debug)
def find_best_template(templates, path_str: str, is_index_file: bool = False) -> str:
    """
    Determines the best template based on the path hierarchy.
    path_str: The clean relative path (e.g. 'posts/stories/my-story')
    is_index_file: True if we are rendering a directory index (e.g. 'posts/stories/index.md')
    """

    parts = [p for p in path_str.strip("/").split("/") if p]

    # use index,html for home...
    if len(parts)==0:
        index_candidate = 'index.html'
        if template_exists(templates, index_candidate):
            return index_candidate


    # 1. Exact Match (Specific File Override)
    # We skip this for index files, as their "Exact Match" is essentially
    # the folder name check in step 2B.
    if not is_index_file:
        candidate = "/".join(parts) + ".html"

        if template_exists(templates, candidate):
            return candidate

        # If we didn't find specific 'my-story.html',
        # pop the filename so we start searching from parent 'stories'
        if parts:
            parts.pop()

    # 2. Recursive Parent Search
    while len(parts) > 0:
        current_folder = parts[-1]  # e.g. "stories"
        parent_path = parts[:-1]  # e.g. ["posts"]

        # A. Singular Check (The "Item" Template)
        # e.g. "posts/story.html"
        # Only valid if we are NOT rendering a directory list (index file)
        if not is_index_file:
            singular_name = singularize(current_folder)
            singular_candidate = "/".join(parent_path + [singular_name]) + ".html"

            print('>>>>parts', parts)

            if template_exists(templates, singular_candidate):
                return singular_candidate

        # B. Plural/Folder Check (The "Section" Template)
        # e.g. "posts/stories.html"
        plural_candidate = "/".join(parts) + ".html"
        if template_exists(templates, plural_candidate):
            return plural_candidate

        # Traverse up
        parts.pop()


    # 3. Final Fallback
    return "page.html"


@cache_fn(debug=cache_debug)
def parse_markdown_file(file):
    data = frontmatter.load(file)
    stats = file.stat()
    # Last date
    data.metadata["date"] = {
        "updated": datetime.fromtimestamp(stats.st_mtime),
        "created": datetime.fromtimestamp(stats.st_ctime),
    }
    # add slug
    data.metadata["slug"] = slugify(str(file.stem))

    data.html = parse_markdown(data.content)


    return data


# We need the sandbox to have the same filters (fancy_date, etc) as the main app
def ensure_sandbox_filters(main_templates):
    if not _safe_env.filters:
        _safe_env.filters.update(main_templates.env.filters)
        # Also copy globals if they are safe data (like site_data)
        # BUT be careful not to copy 'request' or 'app' objects
        safe_globals = {
            k: v for k, v in main_templates.env.globals.items() 
            if k in ['site_data', 'site_code', 'mode'] # Whitelist specific globals
        }
        _safe_env.globals.update(safe_globals)

# template_render_content only in sandbox mode
@cache_fn(debug=cache_debug) 
def template_render_content(templates, content, data, safe=True):
    if not content:
        return ""

    try:
        # Sync filters/globals from the main app to our sandbox
        ensure_sandbox_filters(templates)
        
        # Use the SAFE environment, not the main one
        template = _safe_env.from_string(content)
        
        # Render
        rendered = template.render(**data)
        return Markup(rendered) if safe else rendered
    except Exception as e:
        print(f"⚠️ Template Rendering Error: {e}")
        # Fallback: Return raw content if injection fails, rather than crashing
        return content

@cache_fn(debug=cache_debug)
def get_directory_navigation(
    physical_folder: Path, current_url: str, relative_to_path: Path
) -> List[Dict[str, Any]]:
    """
    Scans the folder containing the current file to generate a sidebar menu.
    """
    if not physical_folder.exists() or not physical_folder.is_dir():
        return []

    items = []
    try:
        # Iterate over files in the folder
        for entry in sorted(
            physical_folder.iterdir(), key=lambda x: (not x.is_dir(), x.name)
        ):
            if entry.name.startswith("."):
                continue  # Skip hidden

            # Skip self-reference if inside index
            if entry.name == "index.md":
                continue  

            # if dir only list if it has an index.md
            if  entry.is_dir() and not (entry / 'index.md').exists() :
                continue


            # Build URL
            try:
                rel_path = entry.relative_to(relative_to_path)
                # Strip .md for URL, keep pure for directories
                url_slug = str(rel_path).replace(".md", "").replace("\\", "/")
                entry_url = f"/{url_slug}"
            except ValueError:
                continue

            items.append(
                {
                    "name": entry.stem.replace("-", " ").title(),
                    "url": entry_url,
                    "is_active": entry_url == current_url,
                    "is_dir": entry.is_dir(),
                }
            )
    except OSError:
        pass  # Ignore permission errors

    return items


@cache_fn(debug=cache_debug)
def get_breadcrumbs(url_path: str) -> List[Dict[str, str]]:
    parts = [p for p in url_path.strip("/").split("/") if p]
    crumbs = [{"name": "Home", "url": "/"}]
    current = ""
    for p in parts:
        current += f"/{p}"
        crumbs.append({"name": p.replace("-", " ").title(), "url": current})
    return crumbs
