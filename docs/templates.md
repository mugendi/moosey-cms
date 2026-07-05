# Templates

moosey-cms uses Jinja2 for templating. Templates live in the directory specified by `dirs.templates` (default: `templates/`).

## Template Syntax

Standard Jinja2 syntax:

```jinja2
{% extends "base.html" %}

{% block content %}
  <h1>{{ page.title }}</h1>
  {{ page.content | safe }}
{% endblock %}
```

## Available Variables

| Variable | Description |
|----------|-------------|
| `config` | Site configuration from `pyproject.toml` |
| `page` | Current page with `title`, `content`, `date`, and frontmatter fields |
| `pages` | All pages in the site (for listings) |
| `site` | Site metadata object |
| `data` | Custom data from `data/` directory |
| `now` | Current datetime (for cache busting, footers) |

## Available Filters

See the [Filters Reference](filters.md) for all built-in filters.

## Static File Helpers

`{{ static("css/style.css") }}` - resolves to the static file URL with optional cache-busting hash.

Configure in `pyproject.toml`:

```toml
[tool.moosey-cms]
dirs.static = "static"
```

### Cache Busting

```jinja2
<link rel="stylesheet" href="{{ static('css/style.css', v=now.timestamp()) }}">
```

Or enable automatic hash-based cache busting:

```toml
[tool.moosey-cms]
cache_bust = true
```

This appends a content hash to static URLs.

## URL Helpers

Resolve internal links:

```jinja2
<a href="{{ url('about') }}">About</a>
```

<!-- TODO: document url_for if that exists -->

## Pagination

Configure pagination in frontmatter or `pyproject.toml`:

```yaml
---
pagination:
    items: pages
    per_page: 10
    sort_by: date
    reverse: true
---
```

Available in templates:

| Variable | Description |
|----------|-------------|
| `paginator.items` | Items on current page |
| `paginator.total` | Total items |
| `paginator.page` | Current page number (1-based) |
| `paginator.pages` | Total pages |
| `paginator.has_prev` | `True` if not on first page |
| `paginator.has_next` | `True` if not on last page |
| `paginator.prev_url` | URL to previous page |
| `paginator.next_url` | URL to next page |

### Pagination Template Example

```jinja2
{% for post in paginator.items %}
  <article>
    <h2><a href="{{ url(post.path) }}">{{ post.title }}</a></h2>
    <p>{{ post.date | date("%B %d, %Y") }}</p>
  </article>
{% endfor %}

{% if paginator.pages > 1 %}
<nav class="pagination">
  {% if paginator.has_prev %}
    <a href="{{ paginator.prev_url }}">Previous</a>
  {% endif %}
  <span>Page {{ paginator.page }} of {{ paginator.pages }}</span>
  {% if paginator.has_next %}
    <a href="{{ paginator.next_url }}">Next</a>
  {% endif %}
</nav>
{% endif %}
```

## RSS / Atom Feeds

Enable feed generation:

```toml
[tool.moosey-cms]
feed = true
feed_type = "atom"  # or "rss"
feed_title = "My Blog"
feed_description = "Latest posts"
feed_items = 20
```

Configure which pages appear in the feed:

```yaml
---
feed: true
---
```

## Sitemaps

Enable auto-generated XML sitemap:

```toml
[tool.moosey-cms]
sitemap = true
```

See [SEO](seo.md) for detailed configuration.

## Search

Add search to your site with `search.index`:

```jinja2
<script>
const searchIndex = {{ search.index | to_json | safe }};
</script>
```

The search index is auto-generated from page content.

## Drafts

Mark pages as drafts to exclude from builds:

```yaml
---
draft: true
---
```

Drafts are only rendered in development mode (`moosey serve`).

## Tags & Categories

Filter pages by tag or category in templates:

```yaml
---
tags: [python, tutorial]
category: guides
---
```

```jinja2
{% for page in pages | selectattr("tags", "contains", "python") %}
  <a href="{{ url(page.path) }}">{{ page.title }}</a>
{% endfor %}
```

## Custom Data Files

Place YAML or JSON files in `data/`. Access them as `data.filename.key`:

```jinja2
{% for member in data.team.members %}
  {{ member.name }}
{% endfor %}
```

## Collections

Group related content with collections:

```toml
[tool.moosey-cms.collections]
projects = { path = "projects", template = "project.html" }
```

Pages in `content/projects/` are automatically part of the `projects` collection.

## Overrides

Place templates in `overrides/` to replace built-in template rendering. See [Patterns](patterns.md) for the directory structure.

## Custom Pages

Define extra pages in `pyproject.toml`:

```toml
[tool.moosey-cms.pages]
archive = { template = "archive.html", paginate = { items = "data.team.members", per_page = 10 } }
```
