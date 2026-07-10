# Getting Started

## Installation

```bash
pip install moosey-cms
```

### Installing Extras

moosey-cms has optional dependency groups for advanced features:

| Extra | Dependencies | Features Enabled |
|-------|-------------|-----------------|
| `images` | Pillow | Image resize, responsive `srcset` |
| `faces` | Pillow, OpenCV | Face-detection crop |
| `all` | Pillow, OpenCV | All optional features |

Install with extras:

```bash
pip install moosey-cms[images]
# or
pip install moosey-cms[all]
```

See [Images](images.md) for usage details.

## Quick Start

### 1. Scaffold a new site

```bash
moosey-cms init ./my-site
cd my-site
```

This copies the example app with all templates, content, and config. Then run the dev server:

```bash
moosey-cms dev
```

Opens a hot-reloading server at `http://localhost:8000`.

### 2. Add admin templates (optional)

```bash
moosey-cms admin --templates ./templates
```

This creates a `templates/admin/` directory with a ready-to-use dashboard, file browser, and editor. Then add `admin={"prefix": "admin/content", "templates": "admin"}` to your `init_cms()` call. See [CLI Reference](cli.md) for details.

### 3. Manual setup (without `init`)

If you prefer to set up manually, create a FastAPI app:

```python
# main.py
import os
from pathlib import Path
from fastapi import FastAPI
from moosey_cms import init_cms

app = FastAPI()

BASE_DIR = Path(__file__).parent

init_cms(
    app=app,
    host="localhost",
    port=8000,
    dirs={
        "content": BASE_DIR / "content",
        "templates": BASE_DIR / "templates",
    },
    mode=os.environ.get("MOOSEY_MODE", "development"),
    site_data={
        "name": "My Site",
        "description": "A site built with Moosey CMS",
    },
)
```

### 2. Create a page

`content/index.md`:

```markdown
---
title: Hello, World!
---

Welcome to my site built with moosey-cms.
```

### 3. Create a template

`templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{{ site_data.name }} - {{ title }}</title>
    {{ seo() }}
</head>
<body>
    <main>
        {{ content }}
    </main>
</body>
</html>
```

`templates/index.html`:

```jinja2
{% extends "base.html" %}

{% block content %}
    <h1>{{ title }}</h1>
    {{ content }}
{% endblock %}
```

### 4. Run

```bash
moosey-cms dev
```

Opens a hot-reloading server at `http://localhost:8000`. For production:

```bash
moosey-cms prod
```

## Running Tests

Install dev dependencies and run the test suite:

### Using UV (Recommended)

```bash
uv add moosey-cms --dev
uv sync
```

### Using Pip

```bash
pip install -e ".[dev]"
```

### Running

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_schemas.py

# Run with verbose output
pytest -v tests/test_schemas.py
```

## Example App

A fully-commented reference app lives in `example/`. It demonstrates:

- Basic Moosey CMS initialization
- Custom Jinja2 globals via `app.state.moosey_env`
- Custom FastAPI routes using the Moosey template environment
- Lifespan-safe init guard (runs `init_cms` once per process)
- Static file mounting
- Content index for custom archives/search

Run it:

```bash
# From the project root
uv run uvicorn example.main:app --reload
```

Visit `http://localhost:8000` to see the demo site.

## Configuration Reference

The `init_cms()` function accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | `FastAPI` | Your FastAPI application instance |
| `host` | `str` | Server host (used for hot-reload script injection) |
| `port` | `int` | Server port |
| `dirs` | `dict` | Dictionary containing `content` and `templates` Paths |
| `mode` | `str` | `"development"`, `"production"`, `"staging"`, or `"testing"` |
| `site_data` | `dict` | Global data (name, author, social links, `web` config for sitemap/robots/RSS) |
| `reload_delay` | `float` | Seconds to delay hot-reload after file change. Default: `0` |
| `admin` | `dict` | Admin content-editing config with keys `prefix` (route prefix) and `templates` (admin templates subdirectory). No admin routes if omitted |

## Documentation

| Doc | What you'll learn |
|-----|-------------------|
| **[Templates](templates.md)** | Template waterfall, layouts, static files, pagination, collections |
| **[Filters Reference](filters.md)** | All 54 built-in Jinja2 filters for dates, text, numbers, images, and more |
| **[Markdown Rendering](markdown.md)** | Using the `markdown` and `markdown_inline` filters, enabled extensions |
| **[Image Processing](images.md)** | Responsive images, `srcset`, face detection, CDN support |
| **[SEO](seo.md)** | Meta tags, Open Graph, structured data, robots.txt, canonical URLs |
| **[Admin API](admin.md)** | Programmatic content management — create, update, delete files and directories |
| **[Security](security.md)** | HTML sanitization, Content Security Policy, sandboxed templates |
| **[Patterns](patterns.md)** | Real-world project structures and conventions |

**[Read Next: Templates →](templates.md)**
