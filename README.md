<!--
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# Moosey CMS 🫎

**A lightweight, drop-in Markdown CMS for FastAPI.**

Moosey CMS transforms your FastAPI application into a content-driven website without the need for a database. It bridges the gap between static site generators and dynamic web servers, offering hot-reloading, intelligent caching, SEO management, and a powerful templating hierarchy.

![Example Screenshot](/example/assets/example-1.jpeg)

![Example Screenshot](/example/assets/example-2.jpeg)

Check out the [/example](/example/) for templating and content samples used to generate the images above.

---

## 🚀 Features

*   **No Database Required:** Content is managed via Markdown files with YAML Frontmatter.
*   **Intelligent Routing:** URL paths automatically map to your content directory structure.
*   **Smart Templating:** "Waterfall" inheritance logic (Singular/Plural) to automatically find the best layout for every page.
*   **Hot Reloading:** Instant browser refresh when Content or Templates change (Development mode only).
*   **High Performance:** Built-in caching (TTL-based) that auto-clears on file changes.
*   **SEO Ready:** Automatic OpenGraph, Twitter Cards, JSON-LD, and Meta tags generation.
*   **Rich Markdown:** Supports tables, emojis, task lists, and syntax highlighting out of the box.
*   **Jinja2 Power:** Use Jinja2 logic directly inside your Markdown files (Securely Sandboxed).

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
└── templates/ 
    ├── layout          
        ├── base.html          <-- Base layout
    ├── index.html         <-- Home Page layout
    ├── page.html          <-- Default fallback
    ├── blog.html          <-- Layout for /blog (Listing)
    └── post.html          <-- Layout for /blog/post-1 (Single Item)
```

---

## 🎨 Templating Logic (The Waterfall)

When a user visits a URL, Moosey CMS searches for templates in a specific cascading order. This allows you to set global defaults while retaining the ability to customize specific pages or sections.

**Example Scenario:**
A user visits **`/posts/post-1`**.

**Directory Structure:**

```text
.
├── content/
│   └── posts/
│       ├── index.md        <-- Required for the '/posts' listing page to work
│       ├── post-1.md       <-- The article being requested
│       └── post-2.md
└── templates/
    ├── posts/
    │   └── post-1.html     <-- 1. Specific Override
    ├── post.html           <-- 2. Singular (Item) Layout
    ├── posts.html          <-- 3. Plural (Section) Layout
    └── page.html           <-- 4. Global Fallback
```

**Resolution Order:**

1.  **Frontmatter Override:** If `post-1.md` contains `template: special.html`, that template is used immediately.
2.  **Exact Match:** `templates/posts/post-1.html`.
3.  **Singular Parent:** `templates/post.html` (Perfect for generic blog posts).
4.  **Plural Parent:** `templates/posts.html` (Perfect for section indexes).
5.  **Fallback:** `templates/page.html`.

---

## 📝 Frontmatter Configuration

You can control routing, visibility, and layout directly from the Markdown file YAML frontmatter.

### Basic Metadata
```yaml
title: My Amazing Post
date: 2024-01-01
description: A short summary for SEO.
```

### Organization & Navigation
| Key | Type | Description |
| :--- | :--- | :--- |
| `order` | `int` | Sort order in sidebars. Lower numbers appear first. Default: `9999`. |
| `nav_title` | `str` | Short title to display in sidebars (if different from `title`). |
| `visible` | `bool` | Set to `false` to hide from sidebars/menus (page remains accessible via URL). |
| `draft` | `bool` | If `true`, the page is only visible in `development` mode. |
| `group` | `str` | Group sidebar items under a heading (requires template support). |

### Advanced Routing
| Key | Type | Description |
| :--- | :--- | :--- |
| `template` | `str` | Force a specific template file (e.g., `template: landing.html`). |
| `external_link` | `str` | The sidebar link will point to this external URL instead of the page itself. |
| `redirect` | `str` | Alias for `external_link`. |

**Example:**
```yaml
---
title: API Documentation
nav_title: API Docs
weight: 1
group: "Developer Tools"
external_link: "https://api.mysite.com"
---
```

---

## 🧩 Custom Filters & Logic

Moosey CMS comes packed with a comprehensive library of Jinja2 filters to help you format your data effortlessly.

### Date & Time
| Filter | Usage | Output |
| :--- | :--- | :--- |
| `fancy_date` | <code>{{ date &#124; fancy_date }}</code> | 13th Jan, 2026 at 6:00 PM |
| `short_date` | <code>{{ date &#124; short_date }}</code> | Jan 13, 2026 |
| `iso_date` | <code>{{ date &#124; iso_date }}</code> | 2026-01-13 |
| `time_only` | <code>{{ date &#124; time_only }}</code> | 6:00 PM |
| `relative_time` | <code>{{ date &#124; relative_time }}</code> | 2 hours ago / yesterday |

### Currency & Numbers
| Filter | Usage | Output |
| :--- | :--- | :--- |
| `currency` | <code>{{ 1234.5 &#124; currency('USD') }}</code> | $1,234.50 |
| `compact_currency` | <code>{{ 1500000 &#124; compact_currency }}</code> | $1.5M |
| `currency_name` | <code>{{ 'KES' &#124; currency_name }}</code> | Kenyan Shilling |
| `number_format` | <code>{{ 1000 &#124; number_format }}</code> | 1,000 |
| `percentage` | <code>{{ 50.5 &#124; percentage }}</code> | 50.5% |
| `ordinal` | <code>{{ 3 &#124; ordinal }}</code> | 3rd |

### Geography & Locale
| Filter | Usage | Output |
| :--- | :--- | :--- |
| `country_flag` | <code>{{ 'US' &#124; country_flag }}</code> | 🇺🇸 |
| `country_name` | <code>{{ 'DE' &#124; country_name }}</code> | Germany |
| `language_name` | <code>{{ 'fr' &#124; language_name }}</code> | French |

### Text Formatting
| Filter | Usage | Output |
| :--- | :--- | :--- |
| `truncate_words` | <code>{{ text &#124; truncate_words(10) }}</code> | Truncates text to 10 words... |
| `excerpt` | <code>{{ text &#124; excerpt(150) }}</code> | Smart excerpt breaking at sentences. |
| `read_time` | <code>{{ content &#124; read_time }}</code> | 5 min read |
| `slugify` | <code>{{ 'Hello World' &#124; slugify }}</code> | hello-world |
| `title_case` | <code>{{ 'a tale of two cities' &#124; title_case }}</code> | A Tale of Two Cities |
| `smart_quotes` | <code>{{ '"Hello"' &#124; smart_quotes }}</code> | “Hello” |

### Utilities
| Filter | Usage | Output |
| :--- | :--- | :--- |
| `filesize` | <code>{{ 1024 &#124; filesize }}</code> | 1.0 KB |
| `yesno` | <code>{{ True &#124; yesno }}</code> | Yes |
| `default_if_none` | <code>{{ val &#124; default_if_none('N/A') }}</code> | Returns default if None |

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

---

## 🛡️ Security & Mitigation

Moosey CMS takes security seriously. We have implemented several layers of protection to ensure your site remains safe:

1.  **Path Traversal Protection:** All URL requests are securely resolved against the content root using strict `pathlib` checks. It is impossible to access files outside the `content` directory (e.g., `../../etc/passwd`).
2.  **SSTI Sandbox:** While we allow Jinja2 logic inside Markdown files, this is executed in a **Sandboxed Environment**. Dangerous attributes (like `__class__`, `__subclasses__`) are stripped, preventing Remote Code Execution (RCE) attacks.
3.  **DoS Prevention:** The Hot-Reload middleware includes size checks to prevent memory exhaustion attacks from large file uploads/downloads.

### 🐛 Bug Reporting
Security is an ongoing process. If you discover a vulnerability, bug, or potential risk, please **open an issue** on our GitHub repository immediately. We appreciate community feedback to keep Moosey secure for everyone.

---

## Gratitude
This project is inspired by [fastapi-blog](https://github.com/pydanny/fastapi-blog) by [Daniel](https://github.com/pydanny). Initially, I wanted to use **fastapi-blog** and it worked really well till I needed features like hot-reloading. 

## License

MIT License. Copyright (c) 2026 Anthony Mugendi.