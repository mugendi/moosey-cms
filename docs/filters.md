# Filters Reference

moosey-cms provides 38 built-in Jinja2 filters for dates, text, numbers, images, and more.

## Quick Reference

| Filter | Category | Description |
|--------|----------|-------------|
| `date` | Date | Format date string |
| `date_iso` | Date | ISO 8601 format |
| `date_rfc` | Date | RFC 2822 format |
| `date_short` | Date | Short format |
| `strftime` | Date | Custom strftime format |
| `time_ago` | Date | Relative "3 days ago" |
| `time_until` | Date | Relative "in 3 days" |
| `country_name` | Currency | Country code to full name |
| `currency_name` | Currency | Currency code to full name |
| `currency_symbol` | Currency | Currency code to symbol ($, €) |
| `currency` | Currency | Format amount with symbol |
| `currency_short` | Currency | Compact currency format |
| `currency_spaced` | Currency | Currency with non-breaking space |
| `pluralize` | Text | Plural/singular suffix |
| `slugify` | Text | URL-friendly slug |
| `truncate` | Text | Truncate with ellipsis |
| `titlecase` | Text | Title case conversion |
| `typogrify` | Text | Smart typography |
| `smartypants` | Text | Smart quotes and dashes |
| `number` | Number | Locale-formatted number |
| `number_short` | Number | Compact format (1.2K) |
| `number_bytes` | Number | Human-readable bytes |
| `number_fixed` | Number | Fixed decimal places |
| `sanitize` | HTML | Strip unsafe HTML tags |
| `format_yaml` | Content | Dict to YAML string |
| `format_toml` | Content | Dict to TOML string |
| `format_json` | Content | Dict to JSON string |
| `format_xml` | Content | Dict to XML string |
| `markdown` | Content | Markdown to full HTML |
| `markdown_inline` | Content | Markdown to inline HTML |
| `to_json` | Utility | Object to JSON |
| `to_yaml` | Utility | Object to YAML |
| `to_toml` | Utility | Object to TOML |
| `to_xml` | Utility | Object to XML |
| `urlencode` | Utility | URL-encode a string |
| `image` | Image | Responsive image tag or URL |
| `image_url` | Image | *(deprecated)* Single image URL |
| `responsive_image` | Image | *(deprecated)* Responsive srcset HTML |
| `image_width` | Image | Get image width |
| `image_height` | Image | Get image height |
| `dominant_color` | Image | Extract dominant color |
| `image_cdn` | Image | Transform URL via CDN |

---

## Date & Time Filters

### `date`

Format a date string:

```jinja2
{{ page.date | date("%B %d, %Y") }}
{# "January 15, 2025" #}
```

Uses Python's `strftime` under the hood.

### `date_iso`

ISO 8601 date format:

```jinja2
{{ page.date | date_iso }}
{# "2025-01-15" #}
```

### `date_rfc`

RFC 2822 date format (for RSS feeds):

```jinja2
{{ page.date | date_rfc }}
{# "Wed, 15 Jan 2025 00:00:00 +0000" #}
```

### `date_short`

Short date format:

```jinja2
{{ page.date | date_short }}
{# "Jan 15, 2025" #}
```

### `strftime`

Alias for Python's `strftime`:

```jinja2
{{ page.date | strftime("%Y-%m-%d") }}
```

### `time_ago`

Relative time in the past:

```jinja2
{{ page.date | time_ago }}
{# "3 days ago" #}
```

### `time_until`

Relative time in the future:

```jinja2
{{ page.date | time_until }}
{# "in 3 days" #}
```

---

## Country & Currency Filters

These require the `pycountry` library (`pip install pycountry`). They gracefully degrade when pycountry is absent, returning the input value unchanged.

### `country_name`

Convert ISO country code to full name:

```jinja2
{{ "US" | country_name }}
{# "United States" #}

{{ "GB" | country_name }}
{# "United Kingdom" #}
```

### `currency_name`

Convert ISO currency code to full name:

```jinja2
{{ "USD" | currency_name }}
{# "US Dollar" #}

{{ "EUR" | currency_name }}
{# "Euro" #}
```

### `currency_symbol`

Get currency symbol from code:

```jinja2
{{ "USD" | currency_symbol }}
{# "$" #}

{{ "EUR" | currency_symbol }}
{# "€" #}

{{ "JPY" | currency_symbol }}
{# "¥" #}
```

### `currency`

Format a number as currency with symbol:

```jinja2
{{ 1234.56 | currency }}
{# "$1,234.56" #}

{{ 1234.56 | currency("EUR") }}
{# "€1,234.56" #}

{{ 0 | currency }}
{# "$0.00" #}
```

### `currency_short`

Compact currency format:

```jinja2
{{ 1500000 | currency_short }}
{# "$1.5M" #}

{{ 2500 | currency_short("EUR") }}
{# "€2.5K" #}
```

### `currency_spaced`

Currency with non-breaking space between symbol and amount:

```jinja2
{{ 1234.56 | currency_spaced("EUR") }}
{# "€ 1,234.56"  (with non-breaking space) #}
```

---

## Text Filters

### `pluralize`

Return plural suffix based on count:

```jinja2
{{ 1 }} item{{ 1 | pluralize }}
{# "1 item" #}

{{ 3 }} item{{ 3 | pluralize }}
{# "3 items" #}

Custom suffix:
{{ 3 | pluralize("es") }}
{# "es" #}

{{ 1 | pluralize("ies", "y") }}
{# "y" #}

{{ 3 | pluralize("ies", "y") }}
{# "ies" #}
```

### `slugify`

Convert string to URL-friendly slug:

```jinja2
{{ "Hello World!" | slugify }}
{# "hello-world" #}

{{ "Café & Bakery" | slugify }}
{# "cafe-bakery" #}

{{ "  Spaces!  " | slugify }}
{# "spaces" #}
```

### `truncate`

Truncate text with ellipsis:

```jinja2
{{ long_text | truncate(100) }}
{# "First 100 characters..." #}
```

### `titlecase`

Convert to title case:

```jinja2
{{ "hello world" | titlecase }}
{# "Hello World" #}

{{ "the quick brown fox" | titlecase }}
{# "The Quick Brown Fox" #}
```

### `typogrify`

Apply smart typography (requires `smartypants`):

```jinja2
{{ '"Hello" -- world' | typogrify }}
{# "&ldquo;Hello&rdquo; &mdash; world" #}
```

### `smartypants`

Smart quotes, dashes, and ellipses:

```jinja2
{{ '"Hello" -- world...' | smartypants }}
{# "&ldquo;Hello&rdquo; &mdash; world&hellip;" #}
```

---

## Number Filters

### `number`

Format with thousand separators:

```jinja2
{{ 1234567.89 | number }}
{# "1,234,567.89" #}
```

### `number_short`

Compact notation:

```jinja2
{{ 1234 | number_short }}
{# "1.2K" #}

{{ 1500000 | number_short }}
{# "1.5M" #}

{{ 500 | number_short }}
{# "500" #}
```

### `number_bytes`

Human-readable byte sizes:

```jinja2
{{ 1024 | number_bytes }}
{# "1.0 KB" #}

{{ 1048576 | number_bytes }}
{# "1.0 MB" #}

{{ 0 | number_bytes }}
{# "0 B" #}

{{ 1536 | number_bytes }}
{# "1.5 KB" #}
```

### `number_fixed`

Format with fixed decimal places:

```jinja2
{{ 3.14159 | number_fixed(2) }}
{# "3.14" #}

{{ 3.1 | number_fixed(2) }}
{# "3.10" #}

{{ 3 | number_fixed(2) }}
{# "3.00" #}
```

---

## HTML & Sanitization

### `sanitize`

Strip unsafe HTML tags and attributes using [Bleach](https://github.com/mozilla/bleach):

```jinja2
{{ user_comment | sanitize }}
```

By default allows: `a`, `abbr`, `acronym`, `b`, `blockquote`, `code`, `em`, `i`, `li`, `ol`, `strong`, `ul`. Pass additional tags as an argument:

```jinja2
{{ content | sanitize(["img", "table"]) }}
```

See [Security](security.md) for full details and CSP configuration.

---

## Content Helpers

### `format_yaml`

Serialize a dict to YAML:

```jinja2
{{ data | format_yaml }}
```

### `format_toml`

Serialize a dict to TOML:

```jinja2
{{ data | format_toml }}
```

### `format_json`

Serialize a dict to formatted JSON:

```jinja2
{{ data | format_json }}
```

### `format_xml`

Serialize a dict to XML:

```jinja2
{{ data | format_xml }}
```
<!-- TODO: document format_xml root tag behavior -->

---

## Utility Filters

### `to_json`

Convert any object to a JSON string (safe for embedding in `<script>` tags):

```jinja2
<script>
const data = {{ page | to_json | safe }};
</script>
```

### `to_yaml`

Convert object to YAML string:

```jinja2
<pre>{{ data | to_yaml }}</pre>
```

### `to_toml`

Convert object to TOML string:

```jinja2
<pre>{{ data | to_toml }}</pre>
```

### `to_xml`

Convert object to XML string:

```jinja2
<pre>{{ data | to_xml }}</pre>
```

### `urlencode`

URL-encode a string:

```jinja2
{{ page.title | urlencode }}
```

---

## Image Filters

See [Image Processing](images.md) for complete documentation and examples.

### `image`

Generate an image URL or responsive `<img>` tag with `srcset`:

```jinja2
{# Single URL #}
<img src="{{ '/photos/photo.jpg' | image(width=800) }}" alt="Photo">

{# Responsive srcset #}
{{ '/photos/photo.jpg' | image(widths=[400, 800, 1200], alt="Photo") }}
```

The `image` filter is the primary API. `image_url` and `responsive_image` are deprecated wrappers that emit `DeprecationWarning`.

### `image_url` *(deprecated)*

Returns a single processed image URL. Prefer `image`.

### `responsive_image` *(deprecated)*

Returns a full `<img>` tag with `srcset`. Prefer `image(widths=...)`.

### `image_width`

Get the pixel width of an image:

```jinja2
{{ '/photos/photo.jpg' | image_width }}
```

### `image_height`

Get the pixel height of an image:

```jinja2
{{ '/photos/photo.jpg' | image_height }}
```

### `dominant_color`

Extract the dominant color as a hex string:

```jinja2
<div style="background-color: {{ '/photos/photo.jpg' | dominant_color }}">
```

### `image_cdn`

Transform an image URL through the configured CDN:

```jinja2
{{ '/photos/photo.jpg' | image_cdn(width=400) }}
```

---

## Markdown Filters

See [Markdown Rendering](markdown.md) for complete documentation.

### `markdown`

Convert Markdown text to full HTML with syntax highlighting:

```jinja2
{{ page.content | markdown }}
```

Requires `pip install moosey-cms[markdown]`.

### `markdown_inline`

Convert Markdown to inline HTML (no wrapper `<div>`):

```jinja2
{{ "This is **bold**" | markdown_inline }}
```
