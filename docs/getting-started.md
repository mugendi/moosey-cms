# Getting Started

## Installation

```bash
pip install moosey-cms
```

### Installing Extras

moosey-cms has optional dependency groups for advanced features:

| Extra | Dependencies | Features Enabled |
|-------|-------------|-----------------|
| `images` | Pillow, OpenCV | Image resize, responsive `srcset`, face detection |
| `markdown` | markdown, pygments, bleach | `markdown` / `markdown_inline` filters |
| `all` | Everything above | All optional features |

Install with extras:

```bash
pip install moosey-cms[images]
# or
pip install moosey-cms[all]
```

See [Images](images.md) and [Markdown](markdown.md) for usage details.

## Quick Start

### 1. Configure `pyproject.toml`

```toml
[tool.moosey-cms]
title = "My Site"
base_url = "https://example.com"
dirs.source = "content"
dirs.output = "_site"
dirs.templates = "templates"
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
<html>
<head>
    <title>{{ config.title }} - {{ page.title }}</title>
</head>
<body>
    <main>
        {{ page.content | safe }}
    </main>
</body>
</html>
```

### 4. Build

```bash
moosey build
```

Output goes to `_site/`.

### 5. Development server

```bash
moosey serve
```

Opens a hot-reloading server at `http://localhost:8080`.

## Next Steps

- Browse the [Filters Reference](filters.md) for all available Jinja2 filters.
- Learn about [Image Processing](images.md) for responsive images.
- See [Templates](templates.md) for pagination, RSS, collections, and more.
