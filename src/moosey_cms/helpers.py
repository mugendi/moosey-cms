"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import os
import frontmatter
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import TemplateNotFound, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
from datetime import datetime
from slugify import slugify
from inflection import singularize
from pprint import pprint
from markupsafe import Markup
from urllib.parse import urlencode

from .models import Dirs
from .md import parse_markdown
from .lib.cache import cache
from .lib.path import get_secure_target, get_directory_navigation
from .lib.urls import get_breadcrumbs, build_lock_params_url, check_lock_params

from .seo import seo_tags
from . import filters

# We initialize this once. It denies access to dangerous attributes like __class__
_safe_env = SandboxedEnvironment(
    trim_blocks=True, lstrip_blocks=True, enable_async=True
)


def validate_model(MyModel, data):
    if not isinstance(data, MyModel):
        MyModel(**data)
    return data


@cache(ttl=3600 * 24 * 30, maxsize=10000)
def template_exists(templates, name: str) -> bool:
    try:
        templates.get_template(name)
        return True
    except TemplateNotFound as e:
        return False
    except TemplateSyntaxError as e:
        import logging
        logging.error(f"Template syntax error in '{name}': {e}")
        # Re-raise so the developer sees the real error clearly
        raise


@cache(ttl=3600 * 24 * 30, maxsize=10000)
def find_best_template(
    templates,
    path_str: str,
    is_index_file: bool = False,
    frontmatter: Optional[dict] = None,
) -> str:
    """
    Determines the best template based on hierarchy or Frontmatter override.
    """

    # 0. Check Frontmatter Override First
    if frontmatter and frontmatter.get("template"):
        candidate = frontmatter.get("template")
        # Ensure it ends with .html if user forgot
        if not candidate.endswith(".html"):
            candidate += ".html"

        if template_exists(templates, candidate):
            return candidate

    parts = [p for p in path_str.strip("/").split("/") if p]

    if len(parts) == 0:
        index_candidate = "index.html"
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


@cache(ttl=3600 * 24 * 30, maxsize=10000)
def parse_markdown_file(file):
    data = frontmatter.load(file)
    stats = file.stat()

    # Ensure date metadata exists
    if "date" not in data.metadata or not isinstance(data.metadata["date"], dict):
        data.metadata["date"] = {}

    data.metadata["date"].setdefault(
        "updated", datetime.fromtimestamp(stats.st_mtime)
    )
    data.metadata["date"].setdefault(
        "created", datetime.fromtimestamp(stats.st_ctime)
    )
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
            k: v
            for k, v in main_templates.env.globals.items()
            if k in ["site_data", "site_code", "mode"]  # Whitelist specific globals
        }
        _safe_env.globals.update(safe_globals)


# template_render_content only in sandbox mode
@cache(ttl=3600 * 24 * 30, maxsize=10000)
async def template_render_content(templates, content, data, safe=True):
    if not content:
        return ""

    try:
        # Sync filters/globals from the main app to our sandbox
        ensure_sandbox_filters(templates)

        # Use the SAFE environment, not the main one
        template = _safe_env.from_string(content)

        # Render
        rendered = await template.render_async(**data)
        return Markup(rendered) if safe else rendered
    except Exception as e:
        traceback.print_exc()
        print(f"⚠️ Template Rendering Error: {e}")
        # Fallback: Return raw content if injection fails, rather than crashing
        return content


