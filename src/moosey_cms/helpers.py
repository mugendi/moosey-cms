"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import os
import frontmatter
from pathlib import Path
from typing import List, Dict, Any, Optional
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
def find_best_template(templates, path_str: str, is_index_file: bool = False, frontmatter: Optional[dict] = None) -> str:
    """
    Determines the best template based on hierarchy or Frontmatter override.
    """
    
    # 0. Check Frontmatter Override First
    if frontmatter and frontmatter.get('template'):
        candidate = frontmatter.get('template')
        # Ensure it ends with .html if user forgot
        if not candidate.endswith('.html'):
            candidate += '.html'
        
        if template_exists(templates, candidate):
            return candidate

    parts = [p for p in path_str.strip("/").split("/") if p]

    if len(parts) == 0:
        index_candidate = 'index.html'
        if template_exists(templates, index_candidate):
            return index_candidate

    # 1. Exact Match
    if not is_index_file:
        candidate = "/".join(parts) + ".html"
        if template_exists(templates, candidate):
            return candidate
        if parts:
            parts.pop()

    # 2. Recursive Parent Search
    while len(parts) > 0:
        current_folder = parts[-1]
        parent_path = parts[:-1]

        # A. Singular Check
        if not is_index_file:
            singular_name = singularize(current_folder)
            singular_candidate = "/".join(parent_path + [singular_name]) + ".html"
            if template_exists(templates, singular_candidate):
                return singular_candidate

        # B. Plural/Folder Check
        plural_candidate = "/".join(parts) + ".html"
        if template_exists(templates, plural_candidate):
            return plural_candidate

        parts.pop()

    # 3. Final Fallback
    return "page.html"


@cache_fn(debug=cache_debug)
def parse_markdown_file(file):
    data = frontmatter.load(file)
    stats = file.stat()
    
    # Ensure date metadata exists
    if "date" not in data.metadata or not isinstance(data.metadata["date"], dict):
        data.metadata["date"] = {}
        
    data.metadata["date"]["updated"] = datetime.fromtimestamp(stats.st_mtime)
    data.metadata["date"]["created"] = datetime.fromtimestamp(stats.st_ctime)
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
    if not content: return ""

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
    physical_folder: Path, current_url: str, relative_to_path: Path, mode: str = "production"
) -> List[Dict[str, Any]]:
    """
    Scans folder for sidebar menu. Supports advanced frontmatter features.
    """
    if not physical_folder.exists() or not physical_folder.is_dir():
        return []

    items = []
    try:
        for entry in physical_folder.iterdir():
            if entry.name.startswith("."): continue
            if entry.name == "index.md": continue  
            if entry.is_dir() and not (entry / 'index.md').exists(): continue

            # Determine Metadata Source
            meta_file = entry / 'index.md' if entry.is_dir() else entry
            
            # Defaults
            sort_order = 9999
            display_title = entry.stem.replace("-", " ").title()
            nav_group = None
            external_url = None
            is_visible = True
            target = "_self"

            try:
                # Load minimal metadata
                post = frontmatter.load(meta_file)
                meta = post.metadata

                # 1. Visibility & Draft Check
                if meta.get('visible') is False:
                    is_visible = False
                
                if meta.get('draft') is True and mode != 'development':
                    is_visible = False

                
                if not is_visible:
                    continue

                # 2. Ordering
                if 'order' in meta: sort_order = int(meta['order'])
                
                # 3. Titles & Grouping
                if 'nav_title' in meta: display_title = meta['nav_title']
                elif 'title' in meta: display_title = meta['title']
                
                nav_group = meta.get('group') or "" 

                # 4. External Links
                if 'external_link' in meta:
                    external_url = meta['external_link']
                    target = "_blank"
                elif 'redirect' in meta:
                    external_url = meta['redirect']

            except Exception:
                pass 

            # Build URL
            if external_url:
                entry_url = external_url
                is_active = False # External links are never 'active' page
            else:
                try:
                    rel_path = entry.relative_to(relative_to_path)
                    url_slug = str(rel_path).replace(".md", "").replace("\\", "/")
                    entry_url = f"/{url_slug}"
                    is_active = (entry_url == current_url)
                except ValueError:
                    continue

            items.append({
                "name": display_title,
                "url": entry_url,
                "is_active": is_active,
                "is_dir": entry.is_dir(),
                "order": sort_order,
                "group": nav_group,
                "target": target
            })
            
        # Sorting: order first, then Name
        # items.sort(key=lambda x: (x['order'], x['name']))
        group_min_orders = {}
    
        for item in items:
            g = item['group']
            w = item['order']
            # If we haven't seen this group, or if this item is lighter (more important)
            if g not in group_min_orders or w < group_min_orders[g]:
                group_min_orders[g] = w

        # 2. Sort the list with a Tuple Key
        items.sort(key=lambda x: (
            # Primary: Group order (Groups with important items float to top)
            group_min_orders[x['group']], 
            
            # Secondary: Group Name (Keep groups clustered together)
            x['group'], 
            
            # Tertiary: Item order (Sort items inside the group)
            x['order'],
            
            # Quaternary: Item Name (Alphabetical fallback)
            x['name']
        ))

    except OSError:
        pass 

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
