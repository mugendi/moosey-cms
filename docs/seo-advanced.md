# SEO & Structured Data (Advanced)

Moosey CMS ships a primitive `json_ld` filter and a small library of schema
builders, plus the `cache_bust`, `pluralize`, `word_count`, and `inline`
helpers. This page complements `docs/filters.md` with full reference per
builder, migration recipes, and testing guidance.

---

## 1. The `json_ld` primitive filter

`json_ld` renders a Python dict as a `<script type="application/ld+json">…</script>`
block:

```jinja
{{ {"@type": "Thing", "name": "Custom"} | json_ld | safe }}
```

Output:

```html
<script type="application/ld+json">
{
  "@type": "Thing",
  "name": "Custom"
}
</script>
```

### Escape semantics
- **JSON encoding**: `ensure_ascii=False`, no sort (preserves dict order). Use `sort_keys=True` if you want stable diffs.
- **`</` breakouts**: every `</` in the payload becomes `<\/` so a string like `"</script>"` can't close the script tag.
- **U+2028 / U+2029**: encoded as their `\u2028`/`\u2029` escape sequences - older JS engines treat these codepoints as line ends and would choke on raw versions.
- **HTML escaping of values**: not applied. JSON-LD's payload isn't inside HTML attributes, so HTML entities would corrupt the data. Schema.org expects raw Unicode.
- **`Markup` return type**: the result is `markupsafe.Markup`, so Jinja treats it as already-safe HTML. `| safe` is harmless but unnecessary.

---

## 2. Built-in schema builders

Each builder returns a plain dict. Pipe to `json_ld`:

### 2.1 `schema_article`

```jinja
{{ schema_article(
     title=post.name,
     description=post.metadata.description,
     image=post.metadata.lead_image,
     author=post.metadata.author,
     date_published=post.metadata.date.published,
     date_modified=post.metadata.date.updated,
     url=request.url
   ) | json_ld | safe }}
```

Emits:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "...",
  "description": "...",
  "image": "...",
  "author": {"@type": "Person", "name": "..."},
  "datePublished": "...",
  "dateModified": "...",
  "mainEntityOfPage": {"@type": "WebPage", "@id": "..."}
}
</script>
```

### 2.2 `schema_breadcrumbs`

```jinja
{{ schema_breadcrumbs(breadcrumbs) | json_ld | safe }}
```

`breadcrumbs` is a list of `{name, url}` dicts. Moosey's `get_breadcrumbs()`
already returns this shape - pass it directly.

### 2.3 `schema_faqpage`

```jinja
{{ schema_faqpage(faqs) | json_ld | safe }}
```

`faqs` is a list of `{question, answer}` dicts.

### 2.4 `schema_howto`

```jinja
{{ schema_howto(
     name="How to build a house in Kenya",
     steps=[{"name": "Scoping", "text": "..."},
            {"name": "Verification", "text": "..."}],
     description="...",
     image="/static/how.jpg"
   ) | json_ld | safe }}
```

### 2.5 `schema_localbusiness`

```jinja
{{ schema_localbusiness(
     name="BackHome Construction",
     url="https://backhome.construction",
     telephone="+254722875845",
     email="hello@backhome.construction",
     address={"addressLocality": "Nairobi", "addressCountry": "KE"},
     hours=[{"dayOfWeek": "Monday", "opens": "09:00", "closes": "18:00"}],
     image="/static/logo.png"
   ) | json_ld | safe }}
```

### 2.6 `schema_product`, `schema_event`, `schema_organization`, `schema_website`, `schema_person`

See the signatures in `src/moosey_cms/schemas.py`. Each takes named args and
returns a ready-to-pipe dict.

---

## 3. Custom schemas - passing your own dict

Nothing pins you to Moosey's builders. If a builder's output doesn't match
your schema, bypass it:

```jinja
{% set custom = {
     "@context": "https://schema.org",
     "@type": "TouristAttraction",
     "name": title,
     "image": lead_image,
     "geo": {"@type": "GeoCoordinates",
             "latitude": "-1.2864", "longitude": "36.8172"}
   } %}
{{ custom | json_ld | safe }}
```

You can also **merge** a built-in with custom fields by spreading:

```jinja
{% set merged = schema_article(title=post.name, ...) |
   tojson | from_json %}
{# merge merges two dicts via ** spread #}
{% set with_video = {**merged, "video": {"@type": "VideoObject",
                                          "contentUrl": post.metadata.video}} %}
{{ with_video | json_ld | safe }}
```

(If you need dict-spread, register a tiny `from_json` filter; for most cases
builder output is enough.)

---

## 4. `cache_bust`

Append `?v=<mtime>` to a static asset URL by reading the file's modification
time under the static mount:

```jinja
<link href="{{ '/static/site.css' | cache_bust }}" rel="stylesheet">
```

Modes:

- `mtime` (default): uses `int(st_mtime)`. Fast, cached in inode.
- `sha8`: `?v=<first 8 hex chars of sha256 of file bytes>` (reads up to 1MB). Opt-in via `| cache_bust(mode='sha8')` or globally via `site_data.cache_bust = "sha8"` (planned).

**Failure mode:** file can't be located (path mismatch, static mount not
configured, file vanished) → returns the unmodified URL. Never raises.

---

## 5. `pluralize`, `word_count`, `inline`

### 5.1 `pluralize`

```jinja
{{ reviews_count }} {{ 'review' | pluralize(reviews_count) }}
```

Custom plural:

```jinja
{{ count }} {{ 'mouse' | pluralize(count, 'mice') }}
```

### 5.2 `word_count`

```jinja
{{ body | word_count }}     → integer
```

Strips HTML first if any tags are present; otherwise splits on whitespace.

### 5.3 `inline`

```jinja
{{ '/static/images/logo.svg' | inline | safe }}              → raw SVG content
{{ '/static/critical.css' | inline | safe }}                 → CSS source
{{ '/static/og-image.webp' | inline(encode='data-uri') }}     → data:<mime>;base64,...
```

For non-text files without `encode="data-uri"`, `inline` falls back to
base64 safely (won't corrupt binary content into the page).

---

## 6. Migrating from hand-written JSON-LD

### 6.1 `LocalBusiness` in base.html (before)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "BackHome Construction",
  "url": "https://backhome.construction",
  "telephone": "+254722875845",
  "email": "hello@backhome.construction",
  ...
}
</script>
```

### After

```jinja
{{ schema_localbusiness(
     name="BackHome Construction",
     url="https://backhome.construction",
     telephone="+254722875845",
     email="hello@backhome.construction",
     address={"addressLocality": "Nairobi", "addressCountry": "KE"},
     hours=[{"dayOfWeek": "Monday",    "opens": "09:00", "closes": "18:00"},
            {"dayOfWeek": "Tuesday",   "opens": "09:00", "closes": "18:00"},
            {"dayOfWeek": "Wednesday", "opens": "09:00", "closes": "18:00"},
            {"dayOfWeek": "Thursday",  "opens": "09:00", "closes": "18:00"},
            {"dayOfWeek": "Friday",    "opens": "09:00", "closes": "18:00"},
            {"dayOfWeek": "Saturday",  "opens": "10:00", "closes": "16:00"}],
     image="/static/images/logo.png"
   ) | json_ld | safe }}
```

### 6.2 `HowTo` in process.html (before)

```jinja
{% set howto_steps = namespace(items=[]) %}
{% for tab in process_tabs %}
  {% set step = {
    "@type": "HowToStep", "position": loop.index,
    "name": tab.title, "text": tab.summary,
    "image": "https://backhome.construction/static/images/process/" ~ loop.index ~ ".jpg"
  } %}
  ...
{% endfor %}

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "{{ title }}",
  "description": "{{ description }}",
  "step": {{ howto_steps.items | tojson }}
}
</script>
```

### After

```jinja
{{ schema_howto(
     name=title,
     description=description,
     steps=[{"name": tab.title,
              "text": tab.summary}
            for tab in process_tabs]
   ) | json_ld | safe }}
```

Cleaner, with consistent escaping and no risk of `</script>` injection.

---

## 7. Testing your schemas

- **Google Rich Results Test:** https://search.google.com/test/rich-results - paste the URL of your page.
- **Schema.org validator:** https://validator.schema.org/ - paste URL or page HTML.
- **Lighthouse SEO category** runs both; aim for a perfect score on Home, Blog index, single post, About, and Service pages.

A simple smoke test in a template:

```jinja
{% set sample = schema_article(title="Smoke") %}
{{ sample["@type"] }}     {{ sample["headline"] }}
```

---

## 8. Reading more

- `docs/filters.md` - the per-filter summary table.
- `docs/advanced-features.md` §8 - the `seo()` function (different from `json_ld` - `seo()` emits the Open Graph / Twitter Card / standard meta tags).
- `docs/filters.md` Sanitize section - always-on HTML sanitization.