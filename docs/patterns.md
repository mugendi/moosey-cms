# Patterns & Project Structure

Real-world conventions for organizing moosey-cms projects.

## Example Site Structure

```
mysite/
├── content/
│   ├── index.md              # Homepage
│   ├── about.md              # About page
│   ├── blog/
│   │   ├── first-post.md
│   │   └── second-post.md
│   └── projects/
│       ├── project-a.md
│       └── project-b.md
├── templates/
│   ├── base.html             # Shared layout
│   ├── index.html            # Homepage template
│   ├── page.html             # Default page template
│   ├── post.html             # Single post template
│   ├── posts.html            # Blog listing
│   └── 404.html              # Error page
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── main.py                   # FastAPI app + init_cms
```

## Path Convention

Content paths match their URLs automatically:

| File | URL |
|------|-----|
| `content/index.md` | `/` |
| `content/about.md` | `/about` |
| `content/blog/first-post.md` | `/blog/first-post` |
| `content/blog/index.md` | `/blog` (section listing) |

## Templates

- Templates live in the `templates/` directory and use Jinja2 syntax
- `base.html` — shared layout with `{% block %}` for child templates
- Template names are resolved via the [waterfall](templates.md#template-waterfall): frontmatter override → exact match → singular → plural/folder → fallback to `page.html`
- `404.html` — rendered when a page is not found

## Navigation

Directory-based navigation is auto-generated. Use `{{ nav_items }}` in templates:

```jinja2
<nav>
{% for item in nav_items %}
    <a href="{{ item.url }}" class="{{ 'active' if item.is_active }}">
        {{ item.name }}
    </a>
{% endfor %}
</nav>
```

Control navigation per page via frontmatter:

```yaml
---
nav_title: Overview
order: 1
group: Getting Started
visible: true
---
```

Features: sorting by `order`, grouping by `group`, external links via `external_link`, visibility toggle via `visible`.

## Static Files

Mount a static directory in FastAPI and optionally configure it for the image pipeline:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

init_cms(
    app,
    ...,
    dirs={
        "static": BASE_DIR / "static",
        ...
    },
)
```

Images in your static directory can be processed on-the-fly — see [Images](images.md).

## Drafts

Prevent pages from appearing in production:

```yaml
---
draft: true
---
```

Drafts are rendered in development mode only.

## Sitemap & Feeds

Built-in routes for `/sitemap.xml`, `/robots.txt`, and `/feed.xml` are auto-registered when configured via `site_data.web`. See [SEO](seo.md) for configuration.

## Custom Routes

After `init_cms()`, you can register custom FastAPI routes that use the Moosey template environment:

```python
@app.get("/custom-greeting")
async def custom_greeting(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "page.html",
        {
            "request": request,
            "title": "Custom Route Demo",
            "content": "<p>This uses the Moosey template environment.</p>",
        },
    )
```

---

← [Previous: Security](security.md) →
