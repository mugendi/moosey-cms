<!--
 Copyright (c) 2026 Anthony Mugendi

 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# Advanced Features

This document covers the advanced capabilities of Moosey CMS that go beyond basic content rendering — including template globals, dynamic navigation, Jinja2 inside Markdown, SEO customization, reusable template macros, content grouping, draft workflows, and more.

---

## Table of Contents

1. [Template Globals](#1-template-globals)
2. [get_files — Dynamic Directory Navigation](#2-get_files--dynamic-directory-navigation)
3. [nav_items — Automatic Sidebar Navigation](#3-nav_items--automatic-sidebar-navigation)
4. [breadcrumbs — Auto-generated Breadcrumbs](#4-breadcrumbs--auto-generated-breadcrumbs)
5. [Jinja2 Inside Markdown](#5-jinja2-inside-markdown)
6. [Jinja2 Inside Frontmatter](#6-jinja2-inside-frontmatter)
7. [Reusable Template Macros](#7-reusable-template-macros)
8. [SEO Function — Advanced Usage](#8-seo-function--advanced-usage)
9. [Frontmatter-Driven Routing & Layout](#9-frontmatter-driven-routing--layout)
10. [Draft Mode & Visibility Control](#10-draft-mode--visibility-control)
11. [Content Grouping in Navigation](#11-content-grouping-in-navigation)
12. [External Links in Navigation](#12-external-links-in-navigation)
13. [date Object — File Timestamps](#13-date-object--file-timestamps)
14. [app_state — Accessing Application State](#14-app_state--accessing-application-state)
15. [debug_template_used](#15-debug_template_used)
16. [Security: The Sandboxed Jinja2 Environment](#16-security-the-sandboxed-jinja2-environment)
17. [Caching Behaviour](#17-caching-behaviour)

---

## 1. Template Globals

Every template rendered by Moosey CMS automatically receives the following variables. You do not need to pass them manually.

| Variable | Type | Description |
| :--- | :--- | :--- |
| `request` | `Request` | The FastAPI/Starlette request object. |
| `site_data` | `dict` | The `site_data` dict you passed to `init_cms()`. |
| `mode` | `str` | The current mode: `"development"` or `"production"`. |
| `title` | `str` | Page title — from frontmatter or derived from the URL slug. |
| `description` | `str` | Page description from frontmatter. |
| `content` | `str` | The rendered HTML content from the Markdown file. |
| `nav_items` | `list` | Auto-generated sibling navigation for the current page. |
| `breadcrumbs` | `list` | Auto-generated breadcrumb trail for the current URL. |
| `get_files` | `callable` | A function to scan any content directory on demand. |
| `app_state` | `State` | The full FastAPI `app.state` object. |
| `debug_template_used` | `str` | The resolved template filename for the current page. |
| `slug` | `str` | URL-friendly slug of the current page filename. |
| `date` | `dict` | Dict with `created` and `updated` datetime objects. |
| `tags` | `list` | Tags list from frontmatter (if defined). |
| `image` | `str` | Featured image URL from frontmatter (if defined). |

**Example — accessing site data:**

```jinja2
<footer>
    &copy; 2026 {{ site_data.author }}. Built with {{ site_data.name }}.
</footer>
```

**Example — conditional dev-only banner:**

```jinja2
{% if mode == 'development' %}
<div class="dev-banner">⚠️ Development Mode</div>
{% endif %}
```

---

## 2. `get_files` — Dynamic Directory Navigation

`get_files` is a callable injected into every template context. It scans any directory under your `content/` folder and returns a structured list of pages — ideal for building custom navigation, index pages, grids, or sitemaps.

### Signature

```jinja2
get_files(physical_folder, current_url, relative_to_path)
```

All three arguments have sensible defaults (the current page's folder), so calling it with no arguments returns siblings of the current page — the same as `nav_items`. Its real power is when you point it at a *different* directory.

### Basic Usage

```jinja2
{% for item in get_files('./content/guides') %}
    <a href="{{ item.url }}">{{ item.name }}</a>
{% endfor %}
```

### Return Value

Each item in the returned list is a dict with the following keys:

| Key | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Display title (from frontmatter `title` or `nav_title`, else derived from filename). |
| `url` | `str` | Absolute URL path (e.g. `/guides/farming`). |
| `is_active` | `bool` | `True` if this URL matches the current page. |
| `is_dir` | `bool` | `True` if this entry is a folder (section), not a file. |
| `order` | `int` | Sort weight from frontmatter `order` key. Default: `9999`. |
| `group` | `str` | Group name from frontmatter `group` key. |
| `target` | `str` | Link target: `"_self"` or `"_blank"` (for external links). |
| `metadata` | `dict` | Full frontmatter dict of the entry's Markdown file. |

### Full Example Output

```python
{
    'name': 'Farming Guides',
    'url': '/guides/farming',
    'is_active': False,
    'is_dir': True,
    'order': 9999,
    'group': '',
    'target': '_self',
    'metadata': {
        'title': 'Farming Guides',
        'description': 'Field-ready resources for farmers.',
        'summary': 'Checklists, calendars, and planning tools.'
    }
}
```

### Practical Example — Cross-section Navigation

Use `get_files` to render a "Related Sections" panel on any page, pulling from a completely different content directory:

```jinja2
<aside class="related-sections">
    <h3>More Topics</h3>
    <ul>
        {% for item in get_files('./content/topics') %}
        <li class="{% if item.is_active %}active{% endif %}">
            <a href="{{ item.url }}" target="{{ item.target }}">
                {% if item.is_dir %}📁{% else %}📄{% endif %}
                {{ item.name }}
            </a>
            {% if item.metadata.description %}
            <p class="desc">{{ item.metadata.description }}</p>
            {% endif %}
        </li>
        {% endfor %}
    </ul>
</aside>
```

### Practical Example — Content Grid / Card Layout

```jinja2
<div class="card-grid">
    {% for post in get_files('./content/posts') %}
    <article class="card">
        {% if post.metadata.image %}
        <img src="{{ post.metadata.image }}" alt="{{ post.name }}">
        {% endif %}
        <h2><a href="{{ post.url }}">{{ post.name }}</a></h2>
        <p>{{ post.metadata.description | default_if_none('') }}</p>
        {% if post.metadata.tags %}
        <div class="tags">
            {% for tag in post.metadata.tags %}
            <span class="tag">#{{ tag }}</span>
            {% endfor %}
        </div>
        {% endif %}
    </article>
    {% endfor %}
</div>
```

---

## 3. `nav_items` — Automatic Sidebar Navigation

`nav_items` is automatically populated with the siblings of the current page (files in the same directory, excluding `index.md`). It uses the same structure as `get_files` results.

This is most useful for building sidebars in section layouts like `page.html` or `posts.html`.

```jinja2
{% if nav_items %}
<nav class="sidebar">
    <h3>In This Section</h3>
    {% for item in nav_items %}
    <a href="{{ item.url }}"
       class="nav-link {% if item.is_active %}active{% endif %}">
        {{ item.name }}
    </a>
    {% endfor %}
</nav>
{% endif %}
```

**Grouping nav_items by their `group` key:**

```jinja2
{% set seen_groups = [] %}
{% for item in nav_items %}
    {% if item.group and item.group not in seen_groups %}
        {% if seen_groups.append(item.group) %}{% endif %}
        <h4 class="nav-group-label">{{ item.group }}</h4>
    {% endif %}
    <a href="{{ item.url }}" class="{% if item.is_active %}active{% endif %}">
        {{ item.name }}
    </a>
{% endfor %}
```

---

## 4. `breadcrumbs` — Auto-generated Breadcrumbs

`breadcrumbs` is a list of dicts automatically built from the current URL path. Each crumb has a `name` (title-cased) and a `url`.

**Example — `/pages/guides/farming` generates:**

```python
[
    {"name": "Home",    "url": "/"},
    {"name": "Pages",   "url": "/pages"},
    {"name": "Guides",  "url": "/pages/guides"},
    {"name": "Farming", "url": "/pages/guides/farming"},
]
```

**Usage:**

```jinja2
<nav aria-label="breadcrumb">
    {% for crumb in breadcrumbs %}
        <a href="{{ crumb.url }}">{{ crumb.name }}</a>
        {% if not loop.last %} › {% endif %}
    {% endfor %}
</nav>
```

**With structured data for SEO:**

```jinja2
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {% for crumb in breadcrumbs %}
    {
      "@type": "ListItem",
      "position": {{ loop.index }},
      "name": "{{ crumb.name }}",
      "item": "{{ request.base_url }}{{ crumb.url.lstrip('/') }}"
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ]
}
</script>
```

---

## 5. Jinja2 Inside Markdown

Moosey CMS renders Jinja2 expressions inside Markdown files **before** converting them to HTML. This means you can use template variables, filters, and logic directly in your content.

This runs inside a **sandboxed environment** (see [Section 16](#16-security-the-sandboxed-jinja2-environment)), so it is safe for user-editable content.

### Accessing Site Data

```markdown
---
title: About the Author
---

This site is maintained by **{{ site_data.author }}**, published under
the name **{{ site_data.name }}**.
```

### Using Filters in Markdown

```markdown
---
date: 2026-01-21
---

*Published: {{ date.created | fancy_date }}*

*Reading time: {{ content | read_time }}*
```

### Conditional Content

```markdown
{% if mode == 'development' %}
> **Note:** This is a draft section visible only in development mode.
{% endif %}

Welcome to the public content visible in all modes.
```

### Looping Over Data from Frontmatter

```markdown
---
team:
  - name: Alice
    role: Developer
  - name: Bob
    role: Designer
---

## Our Team

{% for member in team %}
- **{{ member.name }}** — {{ member.role }}
{% endfor %}
```

---

## 6. Jinja2 Inside Frontmatter

Frontmatter string values are also processed through the Jinja2 sandbox before being passed to templates. This lets you build dynamic page titles, descriptions, and other metadata.

```yaml
---
title: "Building Apps with {{ site_data.name }}"
description: "A guide for {{ site_data.author }}'s readers on modern FastAPI patterns."
---
```

This is especially powerful for auto-generating SEO descriptions that reference global site data without repeating yourself across files.

---

## 7. Reusable Template Macros

Because Jinja2's `{% include %}` does not support passing variables (unlike Twig or Nunjucks), the idiomatic Moosey approach for reusable partials with parameters is **macros**.

### Defining a Macro

Create a file such as `templates/macros/cards.html`:

```jinja2
{# templates/macros/cards.html #}

{% macro post_card(title, url, description='', image='', tags=[]) %}
<article class="card">
    {% if image %}
    <img src="{{ image }}" alt="{{ title }}" class="card-image">
    {% endif %}
    <div class="card-body">
        <h2><a href="{{ url }}">{{ title }}</a></h2>
        {% if description %}
        <p>{{ description }}</p>
        {% endif %}
        {% if tags %}
        <div class="tags">
            {% for tag in tags %}<span class="tag">#{{ tag }}</span>{% endfor %}
        </div>
        {% endif %}
    </div>
</article>
{% endmacro %}

{% macro section_header(title, subtitle='') %}
<header class="section-header">
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
</header>
{% endmacro %}
```

### Using the Macro

```jinja2
{% from 'macros/cards.html' import post_card, section_header %}

{{ section_header('Our Blog', 'The latest from our team') }}

<div class="card-grid">
    {% for post in get_files('./content/posts') %}
        {{ post_card(
            title=post.name,
            url=post.url,
            description=post.metadata.description | default(''),
            image=post.metadata.image | default(''),
            tags=post.metadata.tags | default([])
        ) }}
    {% endfor %}
</div>
```

### Sharing Macros Across Multiple Templates

Import the same macro file in `base.html` or any layout, and it becomes available throughout that template's `{% block %}` regions via template inheritance.

---

## 8. SEO Function — Advanced Usage

The `seo()` function is a Jinja2 global registered on every template. In its simplest form, calling `{{ seo() }}` with no arguments auto-detects everything from the current page context.

### Signature

```jinja2
{{ seo(
    title=None,
    description=None,
    image=None,
    canonical_url=None,
    keywords=None,
    author=None,
    publish_date=None,
    noindex=False
) }}
```

### Auto-detection Priority

For each field, the resolution order is:

1. Explicit argument passed to `seo()`
2. Frontmatter variable in the current page context
3. Global `site_data` fallback

### Basic Usage in `base.html`

```jinja2
<head>
    {{ seo() }}
</head>
```

### Overriding for a Specific Template

```jinja2
{# Force a specific title and description for a landing page #}
{{ seo(
    title="Special Offer — " ~ site_data.name,
    description="Exclusive pricing for the next 24 hours.",
    noindex=True
) }}
```

### Blog Post with Publish Date (Article Schema)

When `publish_date` is provided, the generated JSON-LD schema changes from `WebSite` to `Article`, which gives better indexing for blog content:

```jinja2
{{ seo(publish_date=date.created | iso_date) }}
```

### What `seo()` Generates

A single call produces all of the following, fully populated:

- `<title>` tag
- `<meta name="description">`
- `<meta name="keywords">`
- `<meta name="author">`
- `<link rel="canonical">`
- `<meta name="robots">`
- OpenGraph tags (`og:title`, `og:description`, `og:image`, `og:type`, `og:url`, `og:site_name`)
- Twitter Card tags (`twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`)
- JSON-LD structured data (`Article` or `WebSite`)

---

## 9. Frontmatter-Driven Routing & Layout

### Force a Specific Template

Override the Waterfall template resolution for any page by setting the `template` key in frontmatter:

```yaml
---
title: Product Launch
template: landing.html
---
```

Moosey CMS will use `templates/landing.html` directly, skipping the normal resolution cascade. The `.html` extension is optional.

### External Links in the Sidebar

Make a sidebar entry link to an external URL instead of the page itself:

```yaml
---
title: API Reference
external_link: https://api.mysite.com/docs
---
```

### Redirect Alias

`redirect` is an alias for `external_link`:

```yaml
---
title: Old Page
redirect: /new-location
---
```

---

## 10. Draft Mode & Visibility Control

### Drafts

Mark any page as a draft. It will be visible in `development` mode but return a 404 in `production`:

```yaml
---
title: Work in Progress
draft: true
---
```

### Hidden Pages

Keep a page accessible by direct URL but hide it from all navigation lists:

```yaml
---
title: Thank You
visible: false
---
```

This is useful for confirmation pages, hidden landing pages, or admin-only content that shouldn't appear in sidebars or `get_files()` results.

### Combining Draft + Order

```yaml
---
title: Upcoming Feature Guide
draft: true
order: 1
group: "New Features"
---
```

In development, this page will appear at the top of its group. In production, it will be completely hidden.

---

## 11. Content Grouping in Navigation

Use the `group` frontmatter key to cluster sidebar items under a heading. Items with the same `group` value are sorted together.

**`content/docs/install.md`:**

```yaml
---
title: Installation
group: "Getting Started"
order: 1
---
```

**`content/docs/quickstart.md`:**

```yaml
---
title: Quick Start
group: "Getting Started"
order: 2
---
```

**`content/docs/filters.md`:**

```yaml
---
title: Template Filters
group: "Reference"
order: 1
---
```

**Template rendering grouped nav:**

```jinja2
{% set seen_groups = namespace(value=[]) %}
{% for item in nav_items %}
    {% if item.group and item.group not in seen_groups.value %}
        {% set _ = seen_groups.value.append(item.group) %}
        <h4 class="nav-group">{{ item.group }}</h4>
    {% endif %}
    <a href="{{ item.url }}" class="nav-link {% if item.is_active %}active{% endif %}">
        {{ item.name }}
    </a>
{% endfor %}
```

The sorting algorithm accounts for groups automatically — the group whose items have the lowest `order` values floats to the top.

---

## 12. External Links in Navigation

To add an external link into a content section's sidebar (alongside real pages), create a placeholder Markdown file with `external_link` in its frontmatter. The file body can be empty.

**`content/guides/github.md`:**

```yaml
---
title: Source Code
external_link: https://github.com/mugendi/moosey-cms
order: 99
---
```

This file will never render as a page (visiting `/guides/github` will serve this file's content normally), but in the sidebar it appears as an outbound link that opens in a new tab (`target: "_blank"`).

---

## 13. `date` Object — File Timestamps

Every page automatically receives a `date` dict with two datetime objects derived from the file system. These complement any date you set manually in frontmatter.

| Key | Source | Description |
| :--- | :--- | :--- |
| `date.created` | `os.stat().st_ctime` | File creation time. |
| `date.updated` | `os.stat().st_mtime` | Last modified time. |

If you also set `date:` in frontmatter (e.g. `date: 2026-01-21`), that value is available directly as the raw YAML value, while `date.created` and `date.updated` always reflect the actual file system timestamps.

**Usage in templates:**

```jinja2
<time datetime="{{ date.created | iso_date }}">
    Published {{ date.created | fancy_date }}
</time>

<span>Updated {{ date.updated | relative_time }}</span>
```

**Tip:** Use `date.updated | relative_time` in footers to automatically show when content was last refreshed.

---

## 14. `app_state` — Accessing Application State

The full `request.app.state` object is exposed as `app_state` in every template. This gives access to anything you have stored on the application state from FastAPI.

```jinja2
{# Access site_data via app_state (same as the site_data global) #}
{{ app_state.site_data.name }}

{# Access the current mode #}
{{ app_state.mode }}
```

This is most useful in edge cases where you need to access custom data you have attached to `app.state` yourself outside of `init_cms()`:

```python
# In main.py, before or after init_cms()
app.state.feature_flags = {"new_editor": True, "beta_api": False}
```

```jinja2
{# In a template #}
{% if app_state.feature_flags.new_editor %}
    <a href="/editor">Try the New Editor</a>
{% endif %}
```

---

## 15. `debug_template_used`

In development, every template context includes `debug_template_used` — a string showing exactly which template file was resolved for the current page. This is invaluable for debugging the Waterfall resolution logic.

```jinja2
{% if mode == 'development' %}
<div style="position:fixed; bottom:0; right:0; background:#000; color:#0f0;
            font-family:monospace; font-size:11px; padding:4px 8px; z-index:9999;">
    🗂 {{ debug_template_used }}
</div>
{% endif %}
```

Add this to the bottom of `base.html` during development to always see which template is active.

---

## 16. Security: The Sandboxed Jinja2 Environment

When Moosey CMS renders Jinja2 inside Markdown files or frontmatter strings, it uses Jinja2's `SandboxedEnvironment` — not the main application environment. This prevents Server-Side Template Injection (SSTI) attacks.

**What the sandbox blocks:**

```jinja2
{# These will raise errors in the sandbox — good! #}
{{ ''.__class__.__mro__ }}
{{ config.__class__.__init__.__globals__ }}
{{ ''.__class__.__bases__[0].__subclasses__() }}
```

**What the sandbox allows:**

- All registered custom filters (`fancy_date`, `currency`, `slugify`, etc.)
- Global variables whitelisted explicitly: `site_data`, `mode`
- Standard Jinja2 logic: `if`, `for`, `set`, `filter`

**What is NOT available in Markdown:**

- The `request` object (intentionally excluded for security)
- `app` or `app_state`
- Any function or filter not explicitly registered

This means content authors can use template logic freely without being able to read server environment variables, access the database layer, or execute arbitrary Python code.

---

## 17. Caching Behaviour

Moosey CMS uses an in-memory TTL cache (30-day expiry, 1000 item max) to avoid re-parsing Markdown and re-scanning directories on every request.

### Development Mode

In `development` mode, **the cache is cleared on every request.** You will always see live changes without needing to restart the server. Hot reload via WebSocket then triggers a browser refresh automatically.

### Production Mode

In `production` mode, parsed content and directory listings are cached for up to 30 days. The cache is invalidated automatically by the file watcher whenever a file is created, modified, or deleted — even in production. This means a `git pull` that updates content files will reflect immediately on the next page load.

### Manual Cache Control

If you need to clear the cache programmatically (e.g. from a webhook), the `clear_cache` function is exported from the package:

```python
from moosey_cms import clear_cache

@app.post("/admin/cache/clear")
async def bust_cache():
    clear_cache()
    return {"status": "cache cleared"}
```

### What is Cached

- Parsed Markdown files (frontmatter + HTML output)
- Template existence checks
- Directory navigation scans (`get_files` / `nav_items` results)
- Secure path resolution results
- Breadcrumb generation

The cache key for each item is derived from its arguments, so the same function called with different paths produces independently cached results.

---

*For filter documentation, see [filters.md](filters.md).*
*For the main setup guide, see the [README](../README.md).*