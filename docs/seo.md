# SEO

Search engine optimization helpers for meta tags, structured data, and more.

## Meta Tags

Set per-page meta descriptions and Open Graph fields in frontmatter:

```yaml
---
title: About Us
description: Learn more about our team and mission.
og_image: /images/about-hero.jpg
og_type: website
---
```

Available frontmatter fields:

| Field | Purpose |
|-------|---------|
| `description` | Meta description (also used for OG) |
| `og_image` | Open Graph image URL |
| `og_type` | OG type (website, article, etc.) |
| `seo_title` | Override `<title>` separately from `h1` |
| `noindex` | Set `true` to exclude from search engines |
| `canonical` | Custom canonical URL |

## Template Example

```jinja2
<head>
    <title>{{ page.seo_title or page.title }} - {{ config.title }}</title>
    {% if page.description %}
    <meta name="description" content="{{ page.description }}">
    <meta property="og:description" content="{{ page.description }}">
    {% endif %}
    {% if page.og_image %}
    <meta property="og:image" content="{{ page.og_image }}">
    {% endif %}
    {% if page.noindex %}
    <meta name="robots" content="noindex">
    {% endif %}
    {% if page.canonical %}
    <link rel="canonical" href="{{ page.canonical }}">
    {% endif %}
</head>
```

## Structured Data (JSON-LD)

Use the `to_json` filter to inject schema.org structured data:

```jinja2
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": {{ page.title | to_json | safe }},
    "description": {{ page.description | to_json | safe }},
    "datePublished": {{ page.date | date_iso | to_json | safe }}
}
</script>
```

### Common Schema Types

| Type | When to Use |
|------|-------------|
| `Article` | Blog posts and news |
| `Organization` | Company homepage |
| `WebPage` | Generic pages |
| `BreadcrumbList` | Navigation paths |

### BreadcrumbList Example

```jinja2
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "{{ config.base_url }}"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": "{{ config.base_url }}/blog"},
        {"@type": "ListItem", "position": 3, "name": "{{ page.title }}"}
    ]
}
</script>
```

## robots.txt

moosey-cms generates `robots.txt` automatically from `pyproject.toml` settings:

```toml
[tool.moosey-cms.seo]
sitemap = "sitemap.xml"
```

Default disallows nothing. To block paths:

```toml
[tool.moosey-cms.seo]
disallow = ["/admin", "/draft"]
```

## Canonical URLs

Set a global canonical pattern, or override per page:

```toml
[tool.moosey-cms]
canonical = "always"  # Always include canonical link
```

Per-page frontmatter:

```yaml
---
canonical: https://example.com/ultimate-guide/
---
```

## Sitemaps

Enable XML sitemap generation:

```toml
[tool.moosey-cms]
sitemap = true
```

Generates `sitemap.xml` at the site root. Configure:

```toml
[tool.moosey-cms.seo]
sitemap = "sitemap.xml"
changefreq = "weekly"
priority = 0.8
```

Per-page overrides in frontmatter:

```yaml
---
sitemap:
    changefreq: daily
    priority: 1.0
---
```

Exclude from sitemap:

```yaml
---
sitemap: false
---
```
