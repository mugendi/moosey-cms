<!--
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# Moosey CMS 🫎

**A lightweight, drop-in Markdown CMS for FastAPI.**

Moosey CMS transforms your FastAPI application into a content-driven website without the need for a database. It bridges the gap between static site generators and dynamic web servers, offering hot-reloading, intelligent caching, SEO management, and a powerful templating hierarchy.

---

## 🚀 Features

*   **No Database Required:** Content is managed via Markdown files with YAML Frontmatter.
*   **Intelligent Routing:** URL paths automatically map to your content directory structure.
*   **Smart Templating:** "Waterfall" inheritance logic (Singular/Plural) to automatically find the best layout for every page.
*   **Hot Reloading:** Instant browser refresh when Content or Templates change (Development mode only).
*   **High Performance:** Built-in caching (TTL-based) that auto-clears on file changes.
*   **SEO Ready:** Automatic OpenGraph, Twitter Cards, JSON-LD, and Meta tags generation.
*   **Rich Markdown:** Supports tables, emojis, task lists, and syntax highlighting out of the box.
*   **Jinja2 Power:** Use Jinja2 logic directly inside your Markdown files.

---

## 📦 Installation

### Using UV (Recommended)
```bash
uv add moosey-cms
```

### Using Pip
```bash
pip install moosey-cms
```

---

## ⚡ Quick Start

Integrate Moosey CMS into your existing FastAPI app in just a few lines.

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from moosey_cms import init_cms

app = FastAPI()

# 1. Define your paths
BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
TEMPLATES_DIR = BASE_DIR / "templates"

# 2. Mount static files (Optional, but recommended for CSS/Images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. Initialize the CMS
init_cms(
    app,
    host="localhost",
    port=8000,
    dirs={
        "content": CONTENT_DIR, 
        "templates": TEMPLATES_DIR
    },
    mode="development",  # Enables hot-reloading
    site_data={
        "name": "My Awesome Site",
        "description": "A site built with Moosey CMS",
        "author": "Jane Doe",
        "keywords": ["fastapi", "cms", "python"],
        "open_graph": {
             "og_image": "/static/cover.jpg"
        },
        "social": {
            "twitter": "https://x.com/myhandle",
            "github": "https://github.com/myhandle"
        }
    }
)
```

---

## 📂 Directory Structure

Moosey CMS relies on a convention-over-configuration file structure.

```text
.
├── main.py
├── content/               <-- Your Markdown Files
│   ├── index.md           <-- Homepage (/)
│   ├── about.md           <-- About Page (/about)
│   └── blog/
│       ├── index.md       <-- Blog Listing (/blog)
│       ├── post-1.md      <-- Blog Post (/blog/post-1)
│       └── post-2.md
└── templates/             <-- Your Jinja2 Templates
    ├── base.html          <-- Base layout
    ├── page.html          <-- Default fallback
    ├── blog.html          <-- Layout for /blog (Listing)
    └── post.html          <-- Layout for /blog/post-1 (Single Item)
```

---

## 🎨 Templating Logic (The Waterfall)

When a user visits a URL, Moosey CMS searches for templates in a specific order to allow for granular control with minimal effort.

**Example URL:** `/projects/web/portfolio`

1.  **Exact Match:** `templates/projects/web/portfolio.html`
2.  **Singular Parent:** `templates/projects/web/project.html` (Perfect for item views)
3.  **Plural Parent:** `templates/projects/web.html` (Perfect for section views)
4.  **...Recursive Upward Search:**
    *   `templates/projects/project.html`
    *   `templates/projects.html`
5.  **Fallback:** `templates/page.html`

### Inside a Template

Your templates have access to powerful context variables:

*   `content`: The rendered HTML from your Markdown.
*   `metadata`: The YAML frontmatter from the markdown file.
*   `site_data`: Global site configuration.
*   `breadcrumbs`: Auto-generated breadcrumb navigation.
*   `nav_items`: List of sibling pages/folders for sidebar navigation.

**Example `page.html`:**

```html
{% extends "base.html" %}

{% block content %}
    <h1>{{ title }}</h1>
    
    <!-- Render Breadcrumbs -->
    <nav>
        {% for crumb in breadcrumbs %}
            <a href="{{ crumb.url }}">{{ crumb.name }}</a> /
        {% endfor %}
    </nav>

    <!-- Render Content -->
    <article>
        {{ content | safe }}
    </article>
    
    <!-- Automatic Sidebar -->
    <aside>
        {% for item in nav_items %}
            <a href="{{ item.url }}" class="{% if item.is_active %}active{% endif %}">
                {{ item.name }}
            </a>
        {% endfor %}
    </aside>
{% endblock %}
```

---

## 📝 Markdown Features

### Frontmatter
You can define metadata at the top of any Markdown file. These values are passed to your template.

```markdown
---
title: My Amazing Post
date: 2024-01-01
tags: [fastapi, python]
layout: custom-layout.html  # Optional: force a specific template
---

# Hello World

This is content.
```

### Dynamic Content in Markdown
You can use Jinja2 syntax **inside** your Markdown content!

```markdown
# Welcome {{ site_data.author }}

Today is {{ metadata.date.created | fancy_date }}
```

### Included Extensions
Moosey includes `pymdown-extensions` to provide:
*   Tables
*   Task Lists `[x]`
*   Emojis `:smile:`
*   Code Fences with highlighting
*   Admonitions (Alerts/Callouts)
*   Math/Arithmatex

---

## 🛠️ SEO & Metadata

Moosey CMS includes a robust SEO helper. In your `base.html` `<head>`, simply add:

```html
<head>
    <!-- Automatically generates Title, Meta Description, OpenGraph, 
         Twitter Cards, and JSON-LD Structured Data -->
    {{ seo() }}
    
    <!-- Or override specific values -->
    {{ seo(title="Custom Title", image="/static/custom.jpg") }}
</head>
```

---

## 🧩 Custom Filters

We provide a suite of jinja filters for common tasks:

| Filter | Usage | Output |
| :--- | :--- | :--- |
| `fancy_date` | `{{ date | fancy_date }}` | 13th Jan, 2026 at 6:00 PM |
| `relative_time` | `{{ date | relative_time }}` | 2 hours ago |
| `currency` | `{{ 1200 | currency('USD') }}` | $1,200.00 |
| `read_time` | `{{ content | read_time }}` | 5 min read |
| `truncate_words`| `{{ content | truncate_words(20) }}` | First 20 words... |
| `country_flag` | `{{ 'US' | country_flag }}` | 🇺🇸 |

---

## ⚙️ Configuration Reference

The `init_cms` function accepts the following parameters:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `app` | `FastAPI` | Your FastAPI application instance. |
| `host` | `str` | Server host (used for hot-reload script injection). |
| `port` | `int` | Server port. |
| `dirs` | `dict` | Dictionary containing `content` and `templates` Paths. |
| `mode` | `str` | `"development"` (enables hot reload/no cache) or `"production"`. |
| `site_data` | `dict` | Global data (Name, Author, Social Links). |
| `site_code` | `dict` | Inject custom HTML (e.g., analytics) via `{{ site_code.footer_code }}`. |

---

## 🛡️ Security

Moosey CMS includes built-in path traversal protection. It securely resolves requested paths and ensures they are strictly contained within the defined `content` directory, preventing access to sensitive system files.

---

## License

MIT License. Copyright (c) 2026 Anthony Mugendi.