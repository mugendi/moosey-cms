# Frontmatter fields

The admin editor's **Add metadata** menu is generated from Moosey's built-in registry and advertises only fields consumed by the current runtime. It never overwrites existing values.

## Project overrides

Moosey automatically loads `<project>/.moosey/frontmatter_fields.yaml` beside the content directory. No `init_cms()` option is required. Definitions merge over built-ins by field ID:

```yaml
version: 1
fields:
  draft:
    default: true
  redirect:
    hidden: true
  client:
    label: Client
    type: text
    default: ""
    group: Projects
    description: Client displayed by project.html.
```

Project-added fields are template data; registration does not give them new runtime behavior. Supported definition properties are `label`, `path`, `type`, `default`, `default_factory`, `group`, `description`, `options`, `minimum`, `maximum`, `advanced`, `generated`, `alias_for`, and `hidden`. The `today` default factory and dotted insertion paths such as `sitemap.priority` are supported.

The built-in nested sitemap presets also replace a scalar `sitemap: false` with a mapping. Adding `sitemap.priority` or `sitemap.changefreq` therefore opts the page back into sitemap generation. Other incompatible scalar parents remain protected.

## Basic and rendering

### `title`
```yaml
title: About Moosey
```
Type: text  
Suggested default: `""`

Used by admin listings, navigation, content indexes, feeds, templates, and SEO.

### `description`
```yaml
description: Learn how Moosey CMS works.
```
Type: textarea  
Suggested default: `""`

Used by content indexes, RSS descriptions, templates, and SEO. Prefer this to `summary`.

### `template`
```yaml
template: landing
```
Type: template name  
Suggested default: `""`

Overrides automatic template selection when the template exists. Moosey adds `.html` when omitted.

## Publishing

### `draft`
```yaml
draft: false
```
Type: boolean  
Suggested default: `false`

When true, direct access is unavailable outside development and the page is omitted from ordinary navigation and indexes.

### `visible`
```yaml
visible: true
```
Type: boolean  
Suggested default: `true`

Set false to omit a page from navigation and normal indexes without blocking direct access.

### `date`
```yaml
date: 2026-07-11
```
Type: date  
Suggested default: today

A scalar date becomes the publication date. Moosey also supports `date.published`; `date.created` and `date.updated` are generated from filesystem times.

### `published`
```yaml
published: 2026-07-11
```
Type: date  
Suggested default: today

Explicit publication date used by indexes, RSS ordering, and sitemap timestamp selection.

### `updated`
```yaml
updated: 2026-07-11
```
Type: date  
Suggested default: today

Explicit editorial update date used by feeds and sitemap timestamps.

### `created`
```yaml
created: 2026-07-11
```
Type: date  
Suggested default: today

Advanced explicit creation date. Moosey normally supplies filesystem-derived `date.created`.

## Navigation

### `nav_title`
```yaml
nav_title: About
```
Type: text  
Suggested default: `""`

Short title used in navigation and content indexes instead of `title`.

### `order`
```yaml
order: 10
```
Type: integer  
Suggested default: `0`

Controls ordering in generated directory navigation.

### `group`
```yaml
group: Company
```
Type: text  
Suggested default: `""`

Groups entries in generated directory navigation.

### `external_link`
```yaml
external_link: https://example.com/resource
```
Type: URL  
Suggested default: `""`

Uses an external navigation target and marks the page as an external index entry.

## URL parameter gating

### `lock_params`
```yaml
lock_params:
  campaign: summer
```
Type: object  
Suggested default: `{}`

Requires matching query parameters for access. This is URL gating, not authentication.

### `lock_params._fileset_list_`
```yaml
lock_params:
  campaign: summer
  _fileset_list_: true
```
Type: boolean  
Suggested default: `false`

Includes a gated page in navigation and appends the required parameters.

### `lock_params._sitemap_list_`
```yaml
lock_params:
  campaign: summer
  _sitemap_list_: true
```
Type: boolean  
Suggested default: `false`

Includes a gated page in the sitemap and appends the required parameters.

## SEO

These fields affect output when templates use Moosey's `seo()` helper.

### `noindex`
```yaml
noindex: false
```
Type: boolean  
Suggested default: `false`

Controls noindex output and optional content-index exclusion. It does not block access.

### `keywords`
```yaml
keywords: [fastapi, markdown]
```
Type: string array  
Suggested default: `[]`

SEO keywords; `tags` are the fallback.

### `image`
```yaml
image: /images/social-card.jpg
```
Type: image URL/path  
Suggested default: `""`

Page image used by SEO and social metadata.

### `canonical_url`
```yaml
canonical_url: https://example.com/canonical-page
```
Type: URL  
Suggested default: `""`

Preferred explicit canonical URL.

## Sitemap

### `sitemap`
```yaml
sitemap: false
```
Type: boolean or object  
Suggested exclusion default: `false`

False omits the page. As an object it may contain `changefreq` and `priority`.

### `sitemap.changefreq`
```yaml
sitemap:
  changefreq: weekly
```
Type: select  
Suggested default: `weekly`

Supported values: `always`, `hourly`, `daily`, `weekly`, `monthly`, `yearly`, and `never`.

### `sitemap.priority`
```yaml
sitemap:
  priority: 0.5
```
Type: number from 0.0 to 1.0  
Suggested default: `0.5`

Page-specific priority emitted in sitemap.xml.

## Feed

### `feed`
```yaml
feed: true
```
Type: boolean  
Suggested default: `true`

Set false to omit the page from RSS.

### `author`
```yaml
author: Anthony
```
Type: text  
Suggested default: `""`

RSS item and SEO author; site author is the fallback.

### `tags`
```yaml
tags: [python, cms]
```
Type: string array  
Suggested default: `[]`

RSS categories and fallback SEO keywords.

## Compatibility and advanced

### `summary`
```yaml
summary: A short summary.
```
Type: textarea  
Suggested default: `""`

Compatibility fallback for `description`. Prefer `description`.

### `redirect`
```yaml
redirect: https://example.com/resource
```
Type: URL  
Suggested default: `""`

Alias for `external_link` in navigation. It does not issue an HTTP redirect.

### `rss`
```yaml
rss: true
```
Type: boolean  
Suggested default: `true`

Alias for `feed`. Prefer `feed`.

### `canonical`
```yaml
canonical: https://example.com/canonical-page
```
Type: URL  
Suggested default: `""`

Alias for `canonical_url`. The UI prefers `canonical_url`.

### `changefreq`
```yaml
changefreq: weekly
```
Type: select  
Suggested default: `weekly`

Top-level fallback for `sitemap.changefreq`. Prefer the nested field.

### `priority`
```yaml
priority: 0.5
```
Type: number from 0.0 to 1.0  
Suggested default: `0.5`

Top-level fallback for `sitemap.priority`. Prefer the nested field.

### `slug`
```yaml
slug: custom-page-slug
```
Type: text  
Suggested default: `""`

Advanced content-index slug. Moosey normally derives it from the filename.

## Other fields

Arbitrary frontmatter remains available to templates but is not interpreted automatically. Fields such as `category`, `client`, `featured`, and page-builder structures belong in a project override when a template expects them. Proposed runtime behavior should be treated as a feature update before entering the bundled registry.
