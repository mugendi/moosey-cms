# Templates

moosey-cms uses Jinja2 for templating. Templates live in the directory passed via `dirs["templates"]`.

## Template Syntax

Standard Jinja2 syntax:

```jinja2
{% extends "base.html" %}

{% block content %}
  <h1>{{ title }}</h1>
  {{ content }}
{% endblock %}
```

## Available Variables

| Variable | Description |
|----------|-------------|
| `site_data` | Global site configuration from `init_cms(site_data=...)` |
| `request` | The FastAPI `Request` object |
| `content` | Rendered HTML of the current Markdown page |
| `title` | Page title (from frontmatter or auto-generated) |
| `description` | Page description (from frontmatter) |
| `breadcrumbs` | List of `{"name": ..., "url": ...}` objects |
| `nav_items` | Directory-based navigation for the current folder |
| `mode` | `"development"` or `"production"` |
| `get_files` | Callable to get navigation for a different folder |
| `app_state` | `request.app.state` (access `app.state.templates`, etc.) |
| `debug_template_used` | Name of the template that was resolved |

Any keys in the page's YAML frontmatter are also available as variables (e.g., `{{ author }}`).

## Available Filters

All filters are automatically registered. See the [Filters Reference](filters.md).

## Available Globals

| Global | Description |
|--------|-------------|
| `{{ seo(title, description, image, ...) }}` | Renders full SEO/OG/Twitter/JSON-LD meta tags |
| `{{ schema_article(...) }}` | Returns a dict for JSON-LD article schema |
| `{{ schema_breadcrumbs(items) }}` | Returns a dict for breadcrumb list schema |
| `{{ schema_faqpage(faqs) }}` | Returns a dict for FAQPage schema |
| `{{ schema_howto(name, steps) }}` | Returns a dict for HowTo schema |
| `{{ schema_product(...) }}` | Returns a dict for Product schema |
| `{{ schema_event(...) }}` | Returns a dict for Event schema |
| `{{ schema_organization(name, url) }}` | Returns a dict for Organization schema |
| `{{ schema_website(name, url) }}` | Returns a dict for WebSite schema |
| `{{ schema_person(name) }}` | Returns a dict for Person schema |
| `{{ schema_localbusiness(...) }}` | Returns a dict for LocalBusiness schema |
| `{{ json_ld(schema_dict) }}` | Renders a schema dict as `<script type="application/ld+json">` |

Pass any schema builder dict through `json_ld` to render it:

```jinja2
{{ schema_article(title="My Post", author="Jane") | json_ld | safe }}
```

## Template Waterfall

When a page is requested, moosey-cms resolves the template in this order:

1. **Frontmatter override** — `template: custom.html` in page frontmatter
2. **Exact match** — `post.html` for `/my-post`, `index.html` for `/`
3. **Singular parent** — `post.html` for `/posts/hello`
4. **Plural/folder** — `posts.html` for `/posts/hello`
5. **Recursive parent** — walks up path segments
6. **Fallback** — `page.html`

## Drafts

Mark pages as drafts to exclude from production builds:

```yaml
---
draft: true
---
```

Drafts are only rendered in development mode.

## Tags & Categories

Filter pages by tag or category in templates:

```yaml
---
tags: [python, tutorial]
category: guides
---
```

```jinja2
{% for page in nav_items | selectattr("metadata.tags", "contains", "python") %}
  <a href="{{ page.url }}">{{ page.name }}</a>
{% endfor %}
```

## Static Files

Mount a static directory in your FastAPI app. Access files at `/static/path/to/file`:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
```

For image processing, pass a `static` dir to `init_cms`:

```python
init_cms(
    ...,
    dirs={
        "static": BASE_DIR / "static",
        ...
    },
)
```

See [Images](images.md) for the full image pipeline.

## 404 Pages

Create a `404.html` template in your templates directory. It receives `request` and `site_data`.

## Site Management Routes

The following routes are automatically registered when configured via `site_data.web`:

| Route | Feature | Config key |
|-------|---------|------------|
| `/sitemap.xml` | XML Sitemap | `site_data.web.sitemap` |
| `/robots.txt` | Robots exclusion | `site_data.web.robots` |
| `/feed.xml` | RSS 2.0 feed | `site_data.web.feed` |
| `/rss.xml` | RSS alias | auto (when feed is enabled) |

Example config:

```python
site_data = {
    "web": {
        "site_url": "https://example.com",
        "sitemap": {
            "default_changefreq": "weekly",
            "default_priority": "0.5",
        },
        "feed": {
            "collection": "/posts",
            "title": "My Blog Feed",
            "limit": 20,
        },
    },
}
```

See [SEO](seo.md) for details.
