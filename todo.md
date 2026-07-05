# Todo: Documented-but-not-implemented features

Features that are documented in `docs/` but not yet implemented in the codebase.

## Config System

- [ ] `[tool.moosey-cms]` pyproject.toml config parser — translate TOML into the Python dicts `init_cms()` accepts
- [ ] `[tool.moosey-cms.collections]` — group related content (e.g. `projects = { path = "projects", template = "project.html" }`)
- [ ] `[tool.moosey-cms.pages]` — define extra pages beyond the content directory with optional pagination
- [ ] `[tool.moosey-cms.seo]` — sitemap, robots, changefreq, priority config via TOML
- [ ] `[tool.moosey-cms.csp]` — Content Security Policy header config
- [ ] `[tool.moosey-cms.headers]` — custom security header overrides
- [ ] `[tool.moosey-cms.img_cdn]` — image CDN base_url config via TOML

## CLI

- [ ] `moosey build` — build static site to `_site/`
- [ ] `moosey serve` — development server (currently use `uvicorn` directly)

## Template Helpers

- [ ] `{{ static(path) }}` filter — resolve static file URL with cache-busting
- [ ] `{{ url(path) }}` filter — resolve internal page URL
- [ ] `{{ config }}` global — expose full config in templates (currently `{{ site_data }}`)
- [ ] `{{ data }}` global — load YAML/JSON from `data/` directory
- [ ] `{{ now }}` global — current datetime
- [ ] `{{ to_json }}` filter — serialize dict to JSON
- [ ] `{{ date_iso }}` filter — format date as ISO 8601

## Search

- [ ] `search.index` — auto-generated search index from page content

## Pagination

- [ ] Paginator object (`paginator.items`, `paginator.total`, `paginator.page`, `paginator.pages`, `paginator.has_prev`, `paginator.has_next`, `paginator.prev_url`, `paginator.next_url`)
- [ ] Pagination config via frontmatter (`pagination.items`, `pagination.per_page`, `pagination.sort_by`, `pagination.reverse`)

## Toggles / Opt-Ins

- [ ] `sandbox = true` config — toggle Jinja2 sandbox mode on/off
- [ ] `cache_bust = true` config — enable auto cache-busting on static assets
- [ ] `canonical = "always"` config — always include canonical link

## Misc

- [ ] `{{ markdown_inline }}` filter — currently available as `markdown(text, inline=True)`
- [ ] Image pipeline: `width`/`height`/`quality`/`format` param aliases — currently `w`/`h`/`q`/`fmt`
- [ ] `data/` directory — auto-load YAML/JSON data files into `{{ data }}`
- [ ] `overrides/` directory — custom templates that replace built-in rendering
- [ ] `dirs.source` / `dirs.output` — currently `dirs.content` / `dirs.templates`
- [ ] RSS/Atom feed type selection — currently RSS 2.0 only
