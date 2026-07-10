<!--
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# Moosey CMS 🫎

**A lightweight, drop-in Markdown CMS for FastAPI.**

<p align="center">
  <a href="https://pypi.org/project/moosey-cms/">
    <img src="https://img.shields.io/pypi/v/moosey-cms" alt="PyPI version">
  </a>
  <a href="https://pypi.org/project/moosey-cms/">
    <img src="https://img.shields.io/pypi/pyversions/moosey-cms" alt="Python versions">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/pypi/l/moosey-cms" alt="MIT License">
  </a>
  <a href="https://pypi.org/project/moosey-cms/">
    <img src="https://img.shields.io/pypi/dm/moosey-cms" alt="Downloads">
  </a>
  <a href="https://github.com/mugendi/moosey-cms">
    <img src="https://img.shields.io/github/last-commit/mugendi/moosey-cms" alt="Last commit">
  </a>
  <img src="https://img.shields.io/github/repo-size/mugendi/moosey-cms" alt="Repo size">
</p>

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
*   **Site Management:** Built-in `sitemap.xml`, `robots.txt`, RSS feeds, and a reusable content index.
*   **Rich Markdown:** Supports tables, emojis, task lists, and syntax highlighting out of the box.
*   **Jinja2 Power:** Use Jinja2 logic directly inside your Markdown files (Securely Sandboxed).
*   **Admin API:** Built-in REST API for programmatic content management (create, update, delete files and directories).

## 🛠️ Features That Replace Paid Services

| Moosey CMS Feature | Replaces Paid Services |
|---|---|
| `image()` filter with responsive `srcset` and CDN transforms | Cloudinary, Imgix |
| `schema_article()` + OpenGraph + Twitter Cards + meta tags | Yoast SEO, Rank Math |
| `sanitize()` HTML sanitizer (Bleach-based) | DOMPurify, HTML sanitization APIs |
| `embed()` (YouTube, Twitter/X, Vimeo, CodePen, Gist) | Embedly, oEmbed API services |
| `sitemap.xml` + `robots.txt` + RSS/Atom feed | Google XML Sitemaps, Feedburner |
| `country_flag`, `country_name`, `language_name`, `currency_name` (pycountry) | RestCountries API, currency data APIs |
| `dominant_color()` from local images | ColorThief, LCP placeholder services |
| `inline()` + `cache_bust()` | Critical CSS tools, Webpack/Gulp cache busting |
| `headings()` + `toc_from_html()` | Table of Contents plugins |
| `markdown` with pymdown-extensions | Contentful, Sanity (content authoring) |
| Hot-reload browser refresh | BrowserSync, LiveReload |
| No-database flat-file CMS | WordPress, Strapi, Ghost |

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

## 💻 CLI

moosey-cms ships with a CLI for scaffolding sites, installing admin templates, and running servers.

```bash
# Scaffold a new site from the example app
moosey-cms init ./my-site

# Install admin templates into your project
moosey-cms admin --templates ./templates

# Run dev server (hot-reload)
moosey-cms dev

# Run production server
moosey-cms prod
```

See [CLI Reference](docs/cli.md) for all commands and options.

---

## 🧪 Running Tests

```bash
# Install dev dependencies (pip)
pip install -e ".[dev]"

# Install dev dependencies (uv)
uv add moosey-cms --dev
uv sync

# Run all tests
pytest

# Run a specific test file
pytest tests/test_schemas.py

# Run a specific test class
pytest tests/test_schemas.py::TestSchemaArticle

# Run with verbose output
pytest -v tests/test_schemas.py
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
        },
        "web": {
            "site_url": "https://example.com",
            "feed": {
                "collection": "/blog",
                "title": "My Awesome Site Feed"
            }
        }
    },
    reload_delay=2.5 # Triggers hot-reload after this duration
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

### Publishing, SEO & Feeds
| Key | Type | Description |
| :--- | :--- | :--- |
| `canonical` / `canonical_url` | `str` | Canonical URL used by `{{ seo() }}`. |
| `noindex` | `bool` | Adds `noindex, nofollow` via `{{ seo() }}` and excludes the page from sitemap/feed output. |
| `sitemap` | `bool` or `dict` | Set `false` to exclude from `/sitemap.xml`, or provide `changefreq` / `priority`. |
| `feed` / `rss` | `bool` | Set `false` to exclude a page from RSS feeds. |
| `date.published` | `date` | Preferred publish date for sorting and RSS `pubDate`. |

**Example:**
```yaml
---
title: API Documentation
nav_title: API Docs
order: 1
group: "Developer Tools"
external_link: "https://api.mysite.com"
---
```

---


## 🕸️ Built-in Website Routes

Moosey automatically registers everyday site-management routes before the content catch-all route:

| Route | Purpose |
| :--- | :--- |
| `/sitemap.xml` | Autogenerated XML sitemap from publishable Markdown pages. |
| `/robots.txt` | Environment-aware robots rules with a sitemap pointer. |
| `/feed.xml` | RSS 2.0 feed generated from your content index. |
| `/rss.xml` | Alias for `/feed.xml` unless disabled. |

Configure them in `site_data.web`:

```python
site_data = {
    "name": "My Site",
    "web": {
        "site_url": "https://example.com",
        "sitemap": {
            "default_changefreq": "weekly",
            "default_priority": "0.5",
        },
        "robots": {
            "production": {"allow": ["/"], "disallow": []},
            "staging": {"disallow": ["/"]},
            "testing": {"disallow": ["/"]},
        },
        "feed": {
            "collection": "/blog",
            "limit": 50,
            "title": "My Site Blog",
            "description": "Latest articles from My Site",
        },
    },
}
```

Set any feature to `false` to disable it, for example `"feed": false`.

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
| `rfc822_date` | <code>{{ date &#124; rfc822_date }}</code> | Thu, 15 Jan 2026 00:00:00 GMT |

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
| `strip_html` | <code>{{ content &#124; strip_html }}</code> | Plain text without HTML tags |
| `markdown` | <code>{{ bio &#124; markdown &#124; safe }}</code> | Renders Markdown to HTML (inline mode: `markdown(inline=True)`) |

### Utilities
| Filter | Usage | Output |
| :--- | :--- | :--- |
| `filesize` | <code>{{ 1024 &#124; filesize }}</code> | 1.0 KB |
| `yesno` | <code>{{ True &#124; yesno }}</code> | Yes |
| `default_if_none` | <code>{{ val &#124; default_if_none('N/A') }}</code> | Returns default if None |
| `absolute_url` | <code>{{ '/about' &#124; absolute_url }}</code> | Absolute URL using `site_data.web.site_url` or the request base URL |

### 🛡 Sanitize
| Filter | Usage | Notes |
| :--- | :--- | :--- |
| `sanitize` | <code>{{ html &#124; sanitize &#124; safe }}</code> | Run `bleach.clean` with sane CMS defaults. **Always on** for rendered Markdown bodies. Override via `site_data.sanitize`; opt out with `site_data.sanitize = False`. |

### 🔧 SEO & Data
| Filter | Usage | Output |
| :--- | :--- | :--- |
| `json_ld` | <code>{{ schema_article(...) &#124; json_ld &#124; safe }}</code> | Renders a Python dict as a `<script type="application/ld+json">` block. Schema builders (`schema_article`, `schema_breadcrumbs`, `schema_faqpage`, `schema_howto`, `schema_localbusiness`, `schema_product`, `schema_event`, `schema_organization`, `schema_website`, `schema_person`) are registered as Jinja globals - see [`docs/seo-advanced.md`](docs/seo-advanced.md). |
| `cache_bust` | <code>{{ '/static/site.css' &#124; cache_bust }}</code> | Appends `?v=<mtime>` so browsers re-fetch after every change. |
| `pluralize` | <code>{{ 'review' &#124; pluralize(reviews_count) }}</code> | `1 review` / `2 reviews`. Custom: `pluralize(count, 'mice')`. |
| `word_count` | <code>{{ body &#124; word_count }}</code> | Number of words (strips HTML if any). |
| `inline` | <code>{{ '/static/logo.svg' &#124; inline &#124; safe }}</code> | Inline the contents of a static asset into the page. Pass `encode='data-uri'` for base64. |

### 🖼 Images
| Filter | Description | Install |
| :--- | :--- | :--- |
| `img_attrs` | Build `src … loading=… decoding=…` attribute string. | core |
| `lazy_image` | Inject lazy/async attrs into existing `<img>`. | core |
| `image` | Build an image URL (simple) or a full `<img srcset sizes>` tag (with `widths`). | `moosey-cms[images]` |
| `image_dimensions` | Read `width="…" height="…"` from local image. | `moosey-cms[images]` |
| `dominant_color` | Most-common hex color (for LQIP backgrounds). | `moosey-cms[images]` |
| `image_cdn` | URL-rewriting adapter for Cloudflare / Cloudinary / imgix / ImageKit. | core |

**Enabling on-disk processing** requires passing `"static": <path>` in `dirs` to `init_cms`. Full reference: [`docs/images.md`](docs/images.md). Face detection via `focus=face` requires `moosey-cms[faces]` (~30MB).

**Path convention:** image source paths passed to `image` should omit the `/static/` prefix. Since the static directory is already configured in `dirs`, use paths relative to it - e.g. `/images/team/martin.jpg` instead of `/static/images/team/martin.jpg`. The filter will resolve these against the configured `static_dir` automatically.

### 🔗 Content Helpers
| Filter | Usage | Output |
| :--- | :--- | :--- |
| `embed` | <code>{{ 'https://youtu.be/...' &#124; embed &#124; safe }}</code> | oEmbed-lite for YouTube/Vimeo/Twitter/Gist/CodePen. Unknown URLs fall back to a plain `<a>`. |
| `headings` | <code>{{ content &#124; headings }}</code> | `[(id, text, level), ...]` for in-page TOC. |
| `toc_from_html` | <code>{{ content &#124; toc_from_html &#124; safe }}</code> | Renders a `<nav class="prose-toc"><ul>…</ul></nav>`. |
| `gravatar` | <code>{{ user.email &#124; gravatar(size=200, default='mp') }}</code> | Gravatar URL. |

---

[More On Filters](docs/filters.md) and how to use some interesting ones such as stripping comments.


## ⚙️ Configuration Reference

The `init_cms` function accepts the following parameters:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `app` | `FastAPI` | Your FastAPI application instance. |
| `host` | `str` | Server host (used for hot-reload script injection). |
| `port` | `int` | Server port. |
| `dirs` | `dict` | Dictionary containing `content` and `templates` Paths. |
| `mode` | `str` | `"development"` (enables hot reload/no cache), `"production"`, `"staging"`, or `"testing"`. |
| `site_data` | `dict` | Global data (name, author, social links, optional `web` config for sitemap/robots/RSS). |
| `reload_delay` | `float` | Seconds to delay hot-reload broadcast after a file change. Useful when a build step runs post-save. Default: `0` (immediate). Development mode only. |
| `admin` | `dict` | Admin content-editing config with keys `prefix` (route prefix) and `templates` (admin templates subdirectory). No admin routes if omitted. |

---

## 🛡️ Security & Mitigation

Moosey CMS takes security seriously. We have implemented several layers of protection to ensure your site remains safe:

1.  **Path Traversal Protection:** All URL requests are securely resolved against the content root using strict `pathlib` checks. It is impossible to access files outside the `content` directory (e.g., `../../etc/passwd`).
2.  **SSTI Sandbox:** While we allow Jinja2 logic inside Markdown files, this is executed in a **Sandboxed Environment**. Dangerous attributes (like `__class__`, `__subclasses__`) are stripped, preventing Remote Code Execution (RCE) attacks.
3.  **DoS Prevention:** The Hot-Reload middleware includes size checks to prevent memory exhaustion attacks from large file uploads/downloads.

### 🐛 Bug Reporting
Security is an ongoing process. If you discover a vulnerability, bug, or potential risk, please **open an issue** on our GitHub repository immediately. We appreciate community feedback to keep Moosey secure for everyone.

---

## Documentation

**[Get Started →](docs/getting-started.md)**

## Gratitude
This project is inspired by [fastapi-blog](https://github.com/pydanny/fastapi-blog) by [Daniel](https://github.com/pydanny). Initially, I wanted to use **fastapi-blog** and it worked really well till I needed features like hot-reloading. 

## License

MIT License. Copyright (c) 2026 Anthony Mugendi.