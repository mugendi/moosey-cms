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

### 1. Create a FastAPI app

```python
# main.py
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
    mode="development",
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
uvicorn main:app --reload
```

Opens a hot-reloading server at `http://localhost:8000`.

## Next Steps

- Browse the [Filters Reference](filters.md) for all available Jinja2 filters.
- Learn about [Image Processing](images.md) for responsive images.
- See [Templates](templates.md) for drafts, tags, and template waterfall.
