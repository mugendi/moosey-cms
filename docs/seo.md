# SEO

Search engine optimization helpers for meta tags, structured data, and more.

## Meta Tags with `seo()`

The `{{ seo() }}` global renders a full suite of SEO, Open Graph, and Twitter Card meta tags. Call it in the `<head>` of your template:

```jinja2
<head>
    {{ seo() }}
</head>
```

### Arguments

All arguments are optional. Values fall back to frontmatter fields, then `site_data`.

| Argument | Type | Fallback | Purpose |
|----------|------|----------|---------|
| `title` | str | `page.title` → `site_data.name` | `<title>`, `og:title`, `twitter:title` |
| `description` | str | `page.description` → `site_data.description` | `<meta name="description">`, `og:description` |
| `image` | str | `site_data.open_graph.og_image` | `og:image`, `twitter:image` (auto-absolutized) |
| `canonical_url` | str | `page.canonical` → current URL | `<link rel="canonical">` |
| `keywords` | str/list | `page.keywords` → `site_data.keywords` → `page.tags` | `<meta name="keywords">` |
| `author` | str | `page.author` → `site_data.name` | `<meta name="author">`, `article:author` |
| `publish_date` | str (ISO 8601) | — | Sets `og:type=article`, `article:published_time`, JSON-LD `datePublished` |
| `noindex` | bool | `page.noindex` → `False` | `<meta name="robots" content="noindex">` |

### Example

```jinja2
{{ seo(
    title=title,
    description=description,
    image="/static/cover.jpg",
    publish_date="2026-01-13",
) }}
```

This generates: `<title>`, meta description, keywords, author, canonical, robots, `og:site_name`, `og:type`, `og:title`, `og:description`, `og:url`, `og:image`, `twitter:card`, `twitter:site`, `twitter:title`, `twitter:description`, `twitter:image`, `article:published_time`, `article:author`, and JSON-LD structured data.

## Structured Data (JSON-LD)

Use the schema builders in combination with the `json_ld` filter:

```jinja2
{{ schema_article(title=title, description=description, author="Jane") | json_ld | safe }}
```

### `schema_article()` Reference

| Parameter | Type | Schema.org Prop | Description |
|-----------|------|-----------------|-------------|
| `title` *(required)* | `str` | `headline` | Article headline |
| `description` | `str` | `description` | Short description |
| `image` | `str` | `image` | Image URL |
| `author` | `str` | `author` | Author name (wraps in `Person`) |
| `date_published` | `str` | `datePublished` | ISO 8601 publish date |
| `date_modified` | `str` | `dateModified` | ISO 8601 modify date |
| `url` | `str` | `mainEntityOfPage` | Page URL |
| `keywords` | `str` / `list[str]` | `keywords` | Comma-joined if list |
| `in_language` | `str` | `inLanguage` | IETF BCP 47 language code |
| `article_section` | `str` | `articleSection` | Section (e.g. "Tech") |
| `article_body` | `str` | `articleBody` | Full body text |
| `word_count` | `int` | `wordCount` | Auto-calc from `article_body` if omitted |
| `speakable` | `list[str]` | `speakable` | CSS selectors for voice highlight |
| `backstory` | `str` | `backstory` | Context for how article was created |
| `date_created` | `str` | `dateCreated` | ISO 8601 creation date |
| `publisher` | `str` / `dict` | `publisher` | Name string or `{"name", "logo"}` dict |
| `comment_count` | `int` | `commentCount` | Number of comments |
| `about` | `str` / `list[str]` | `about` | Subject matter keywords |
| `abstract` | `str` | `abstract` | Brief summary |
| `alternative_headline` | `str` | `alternativeHeadline` | Secondary headline |
| `genre` | `str` / `list[str]` | `genre` | Genre/category |
| `license` | `str` | `license` | License URL |
| `is_part_of` | `dict` | `isPartOf` | Parent work `{"name", "url"}` |
| `is_accessible_for_free` | `bool` | `isAccessibleForFree` | Free access flag |
| `copyright_year` | `int` | `copyrightYear` | Copyright year |
| `copyright_holder` | `str` / `dict` | `copyrightHolder` | Name string or `{"name", "url"}` dict |
| `discussion_url` | `str` | `discussionUrl` | Link to comment page |

### Other Schema Builders

`schema_breadcrumbs`, `schema_faqpage`, `schema_howto`, `schema_localbusiness`, `schema_product`, `schema_event`, `schema_organization`, `schema_website`, `schema_person`.

You can also pass raw dicts:

```jinja2
{{ {"@context": "https://schema.org", "@type": "Thing", "name": "Custom"} | json_ld | safe }}
```

### Per-Page Frontmatter

```yaml
---
title: About Us
description: Learn more about our team and mission.
seo_title: About - My Site
noindex: false
canonical: https://example.com/about
og_image: /images/about-hero.jpg
sitemap:
    changefreq: monthly
    priority: 0.8
---
```

## robots.txt

Moosey generates `/robots.txt` automatically. Configure it via `site_data.web.robots`:

```python
site_data = {
    "web": {
        "robots": {
            "production": {"disallow": []},
            "staging": {"disallow": ["/"]},
        },
    },
}
```

Default: `Disallow:` (allow everything) in production; `Disallow: /` in staging/testing.

## Sitemap

Generate `/sitemap.xml` by enabling it in `site_data.web.sitemap`:

```python
site_data = {
    "web": {
        "sitemap": {
            "default_changefreq": "weekly",
            "default_priority": "0.5",
        },
    },
}
```

Per-page overrides in frontmatter:

```yaml
sitemap:
    changefreq: daily
    priority: 1.0
```

Exclude from sitemap:

```yaml
sitemap: false
```

## RSS Feed

Generate `/feed.xml` (RSS 2.0) by enabling it in `site_data.web.feed`:

```python
site_data = {
    "web": {
        "feed": {
            "collection": "/posts",
            "title": "My Blog Feed",
            "description": "Latest posts",
            "limit": 20,
        },
    },
}
```

Exclude individual pages from the feed:

```yaml
---
rss: false
---
```

## site_data Reference

The full `site_data` dict structure for SEO:

```python
site_data = {
    "name": "Your Site Name",
    "description": "Site description",
    "author": "Author Name",
    "keywords": ["keyword1", "keyword2"],
    "open_graph": {
        "og_image": "/static/og-image.jpg",
    },
    "social": {
        "twitter": "https://x.com/handle",
        "github": "https://github.com/handle",
    },
    "web": {
        "site_url": "https://example.com",
        "sitemap": {...},
        "robots": {...},
        "feed": {...},
    },
}
```
