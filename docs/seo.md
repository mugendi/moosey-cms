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

### `schema_breadcrumbs()` Reference

Builds a `BreadcrumbList` for navigation paths.

```jinja2
{{ schema_breadcrumbs([
    {"name": "Home", "url": "/"},
    {"name": "Blog", "url": "/blog"},
    {"name": "My Post", "url": "/blog/my-post"}
]) | json_ld | safe }}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `items` *(required)* | `list[dict]` | List of `{"name": str, "url": str}` objects |

Each item gets an auto-incremented `position` starting at 1.

---

### `schema_faqpage()` Reference

Builds an `FAQPage` with question/answer pairs.

```jinja2
{{ schema_faqpage([
    {"question": "What is Moosey CMS?", "answer": "A lightweight Markdown CMS for FastAPI."},
    {"question": "Does it need a database?", "answer": "No, content lives in Markdown files."}
]) | json_ld | safe }}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `faqs` *(required)* | `list[dict]` | List of `{"question": str, "answer": str}` objects |

---

### `schema_howto()` Reference

Builds a `HowTo` guide with named steps.

```jinja2
{{ schema_howto(
    name="How to Install Moosey CMS",
    steps=[
        {"name": "Install the package", "text": "pip install moosey-cms"},
        {"name": "Create your app", "text": "Set up a FastAPI app and call init_cms()."},
        {"name": "Run the server", "text": "uvicorn main:app --reload"}
    ],
    description="A quick guide to getting started with Moosey CMS."
) | json_ld | safe }}
```

| Parameter | Type | Schema.org Prop | Description |
|-----------|------|-----------------|-------------|
| `name` *(required)* | `str` | `name` | HowTo title |
| `steps` *(required)* | `list[dict]` | `step` | List of `{"name": str, "text": str}` objects (auto-numbered) |
| `description` | `str` | `description` | Short description of the guide |
| `image` | `str` | `image` | Image URL for the guide |

---

### `schema_localbusiness()` Reference

Builds a `LocalBusiness` with contact info, address, and hours.

```jinja2
{{ schema_localbusiness(
    name="Acme Coffee Shop",
    url="https://example.com",
    telephone="+1-555-123-4567",
    email="hello@example.com",
    address={
        "streetAddress": "123 Main St",
        "addressLocality": "Portland",
        "addressRegion": "OR",
        "postalCode": "97201",
        "addressCountry": "US"
    },
    hours=[
        {"dayOfWeek": ["Monday", "Friday"], "opens": "08:00", "closes": "18:00"},
        {"dayOfWeek": ["Saturday", "Sunday"], "opens": "09:00", "closes": "14:00"}
    ],
    image="https://example.com/photo.jpg",
    same_as=["https://facebook.com/acmecoffee", "https://instagram.com/acmecoffee"]
) | json_ld | safe }}
```

| Parameter | Type | Schema.org Prop | Description |
|-----------|------|-----------------|-------------|
| `name` *(required)* | `str` | `name` | Business name |
| `url` *(required)* | `str` | `url` | Business URL |
| `telephone` | `str` | `telephone` | Phone number |
| `email` | `str` | `email` | Contact email |
| `address` | `dict` | `address` | `PostalAddress` dict with `streetAddress`, `addressLocality`, `addressRegion`, `postalCode`, `addressCountry` |
| `hours` | `list[dict]` | `openingHoursSpecification` | List of `OpeningHoursSpecification` dicts with `dayOfWeek`, `opens`, `closes` |
| `image` | `str` | `image` | Photo URL |
| `same_as` | `list[str]` | `sameAs` | Social media profile URLs |

---

### `schema_product()` Reference

Builds a `Product` with optional pricing and ratings.

```jinja2
{{ schema_product(
    name="Moosey Pro License",
    image="https://example.com/pro.jpg",
    description="Lifetime license for Moosey CMS Pro features.",
    sku="MOOSEY-PRO-001",
    price=49.00,
    currency="USD",
    availability="https://schema.org/InStock",
    rating={
        "ratingValue": "4.8",
        "reviewCount": "120"
    }
) | json_ld | safe }}
```

| Parameter | Type | Schema.org Prop | Description |
|-----------|------|-----------------|-------------|
| `name` *(required)* | `str` | `name` | Product name |
| `image` | `str` | `image` | Product image URL |
| `description` | `str` | `description` | Product description |
| `sku` | `str` | `sku` | Stock keeping unit |
| `price` | `float` | `offers.price` | Price (requires `currency`) |
| `currency` | `str` | `offers.priceCurrency` | ISO 4217 currency code (e.g. `"USD"`) |
| `availability` | `str` | `offers.availability` | Schema.org availability URL (e.g. `"https://schema.org/InStock"`) |
| `rating` | `dict` | `aggregateRating` | `AggregateRating` dict with `ratingValue`, `reviewCount`, etc. |

---

### `schema_event()` Reference

Builds an `Event` with date, location, and organizer.

```jinja2
{{ schema_event(
    name="Moosey CMS Meetup",
    start_date="2026-09-15T18:00",
    end_date="2026-09-15T21:00",
    location={"name": "Portland Convention Center", "address": "1000 NE Grand Ave"},
    url="https://example.com/events/meetup",
    image="https://example.com/event.jpg",
    organizer="Moosey Community"
) | json_ld | safe }}
```

| Parameter | Type | Schema.org Prop | Description |
|-----------|------|-----------------|-------------|
| `name` *(required)* | `str` | `name` | Event name |
| `start_date` *(required)* | `str` | `startDate` | ISO 8601 start date/time |
| `end_date` | `str` | `endDate` | ISO 8601 end date/time |
| `location` | `dict` | `location` | `Place` dict with `name`, `address`, etc. |
| `url` | `str` | `url` | Event page URL |
| `image` | `str` | `image` | Event image URL |
| `organizer` | `str` | `organizer` | Organizer name (wraps in `Organization`) |

---

### `schema_organization()` Reference

Builds an `Organization` with logo and social profiles.

```jinja2
{{ schema_organization(
    name="Moosey Inc",
    url="https://example.com",
    logo="https://example.com/logo.png",
    same_as=["https://twitter.com/moosey", "https://github.com/moosey"]
) | json_ld | safe }}
```

| Parameter | Type | Schema.org Prop | Description |
|-----------|------|-----------------|-------------|
| `name` *(required)* | `str` | `name` | Organization name |
| `url` *(required)* | `str` | `url` | Organization URL |
| `logo` | `str` | `logo` | Logo URL (wraps in `ImageObject`) |
| `same_as` | `list[str]` | `sameAs` | Social media profile URLs |

---

### `schema_website()` Reference

Builds a `WebSite` with optional search action.

```jinja2
{{ schema_website(
    name="My Site",
    url="https://example.com",
    publisher="My Company",
    potential_action={
        "@type": "SearchAction",
        "target": "https://example.com/search?q={search_term_string}",
        "query-input": "required name=search_term_string"
    }
) | json_ld | safe }}
```

| Parameter | Type | Schema.org Prop | Description |
|-----------|------|-----------------|-------------|
| `name` *(required)* | `str` | `name` | Site name |
| `url` *(required)* | `str` | `url` | Site URL |
| `publisher` | `str` | `publisher` | Publisher name (wraps in `Organization`) |
| `potential_action` | `dict` | `potentialAction` | Action dict (e.g. `SearchAction` for sitelinks search box) |

---

### `schema_person()` Reference

Builds a `Person` with profile info.

```jinja2
{{ schema_person(
    name="Jane Doe",
    url="https://example.com/jane",
    job_title="Lead Developer",
    image="https://example.com/jane.jpg",
    same_as=["https://twitter.com/janedoe", "https://github.com/janedoe"]
) | json_ld | safe }}
```

| Parameter | Type | Schema.org Prop | Description |
|-----------|------|-----------------|-------------|
| `name` *(required)* | `str` | `name` | Person's name |
| `url` | `str` | `url` | Profile page URL |
| `job_title` | `str` | `jobTitle` | Job title |
| `image` | `str` | `image` | Photo URL |
| `same_as` | `list[str]` | `sameAs` | Social media profile URLs |

---

### Raw Dicts

You can bypass the builders and pass any dict directly:

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

---

← [Previous: Images](images.md) | [Next: Admin API](admin.md) →
