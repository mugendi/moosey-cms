# Filters Reference

moosey-cms provides 54 built-in Jinja2 filters for dates, text, numbers, images, and more.

All filters are automatically registered when you call `init_cms()`.

## Quick Reference

| Filter | Category | Description |
|--------|----------|-------------|
| `slugify` | String | URL-friendly slug |
| `title_case` | String | Title case conversion |
| `truncate_words` | String | Truncate by word count |
| `excerpt` | String | Smart excerpt at sentence break |
| `reading_time` | String | Estimated reading time |
| `read_time` | String | Estimated reading time (alias) |
| `smart_quotes` | String | Straight to curly quotes |
| `pluralize` | String | Plural/singular suffix |
| `snake_case` | String | Convert to snake_case |
| `kebab_case` | String | Convert to kebab-case |
| `camel_case` | String | Convert to camelCase |
| `pascal_case` | String | Convert to PascalCase |
| `upper_case` | String | Convert to UPPER CASE |
| `lower_case` | String | Convert to lower case |
| `word_count` | String | Count words in text |
| `fancy_date` | Date | '13th Jan, 2026 at 6:00 PM' |
| `short_date` | Date | 'Jan 13, 2026' |
| `iso_date` | Date | '2026-01-13' |
| `relative_time` | Date | '2 hours ago' |
| `time_only` | Date | '6:00 PM' |
| `strptime` | Date | Parse string to datetime |
| `rfc822_date` | Date | RFC 822 format (RSS) |
| `number_format` | Number | Thousand separators |
| `percentage` | Number | Format as percentage |
| `ordinal` | Number | 1st, 2nd, 3rd |
| `filesize` | Number | Human-readable bytes |
| `currency` | Currency | Format with symbol ($1,234.56) |
| `compact_currency` | Currency | Compact format ($1.2M) |
| `currency_name` | Currency | Code to full name ('US Dollar') |
| `country_name` | Currency | Code to full name ('United States') |
| `country_flag` | Currency | Code to emoji flag (🇺🇸) |
| `language_name` | Currency | Code to full name ('English') |
| `image` | Image | Image URL or responsive `<img>` |
| `image_url` | Image | *(deprecated)* Image URL |
| `responsive_image` | Image | *(deprecated)* Responsive `<img>` |
| `image_dimensions` | Image | `width="…" height="…"` string |
| `dominant_color` | Image | Most common hex color |
| `image_cdn` | Image | CDN transform URL |
| `img_attrs` | Image | `src loading decoding` string |
| `lazy_image` | Image | Inject lazy attrs |
| `strip_html` | HTML | Remove HTML tags |
| `strip_comments` | HTML | Remove HTML comments |
| `minify_html` | HTML | Minify whitespace |
| `sanitize` | HTML | Bleach safe tag allowlist |
| `markdown` | Content | Markdown to HTML |
| `embed` | Content | Video/social embed HTML |
| `headings` | Content | Extract heading tree |
| `toc_from_html` | Content | Render table of contents |
| `gravatar` | Content | Gravatar URL |
| `default_if_none` | Utility | Fallback for None values |
| `yesno` | Utility | Boolean to yes/no text |
| `absolute_url` | Utility | Resolve relative URL |
| `cache_bust` | Utility | Append version hash |
| `inline` | Utility | Inline file contents |

## String Filters

Filters that transform, analyze, or format text content.

### `slugify`

Convert string to URL-friendly slug:

```jinja2
{{ "Hello World!" | slugify }}
{# "hello-world" #}

{{ "Café & Bakery" | slugify }}
{# "cafe-bakery" #}
```

### `title_case`

Convert to title case, preserving acronyms:

```jinja2
{{ "hello world" | title_case }}
{# "Hello World" #}

{{ "the quick brown fox" | title_case }}
{# "The Quick Brown Fox" #}
```

### `truncate_words`

Truncate text to specified word count:

```jinja2
{{ long_text | truncate_words(50) }}
{# "First 50 words..." #}
```

### `excerpt`

Create excerpt from text, breaking at sentence boundary:

```jinja2
{{ page.content | excerpt }}
{# "First sentence." #}

{{ page.content | excerpt(200) }}
{# "First ~200 chars breaking at sentence." #}
```

### `reading_time`

Calculate reading time in minutes:

```jinja2
{{ page.content | reading_time }}
{# "3 min read" #}
```

### `read_time`

Alias for `reading_time`.

### `smart_quotes`

Convert straight quotes to smart/curly quotes:

```jinja2
{{ '"Hello" -- world' | smart_quotes }}
```

### `pluralize`

Return plural suffix based on count:

```jinja2
{{ 'review' | pluralize(reviews|length) }}
{# "review" or "reviews" #}

{{ 'box' | pluralize(3, 'boxes') }}
{# "boxes" #}
```

### `word_count`

Number of whitespace-separated words (strips HTML if present):

```jinja2
{{ page.content | word_count }}
{# 342 #}
```

### `snake_case`

Convert to `snake_case` from spaces, camelCase, kebab-case, or mixed:

```jinja2
{{ "Hello World" | snake_case }}
{# "hello_world" #}

{{ "helloWorld" | snake_case }}
{# "hello_world" #}

{{ "HTMLParser" | snake_case }}
{# "html_parser" #}
```

### `kebab_case`

Convert to `kebab-case` from spaces, camelCase, snake_case, or mixed:

```jinja2
{{ "Hello World" | kebab_case }}
{# "hello-world" #}

{{ "hello_world" | kebab_case }}
{# "hello-world" #}
```

### `camel_case`

Convert to `camelCase` from spaces, snake_case, kebab-case, or mixed:

```jinja2
{{ "Hello World" | camel_case }}
{# "helloWorld" #}

{{ "hello_world" | camel_case }}
{# "helloWorld" #}
```

### `pascal_case`

Convert to `PascalCase` from spaces, snake_case, camelCase, or mixed:

```jinja2
{{ "Hello World" | pascal_case }}
{# "HelloWorld" #}

{{ "hello_world" | pascal_case }}
{# "HelloWorld" #}
```

### `upper_case`

Convert to uppercase:

```jinja2
{{ "Hello World" | upper_case }}
{# "HELLO WORLD" #}
```

### `lower_case`

Convert to lowercase:

```jinja2
{{ "Hello World" | lower_case }}
{# "hello world" #}
```

---

## Date & Time Filters

Filters for formatting, parsing, and displaying dates and times.

### `fancy_date`

Format date as '13th Jan, 2026 at 6:00 PM':

```jinja2
{{ page.date | fancy_date }}
{# "13th Jan, 2026 at 6:00 PM" #}
```

### `short_date`

Format date as 'Jan 13, 2026':

```jinja2
{{ page.date | short_date }}
{# "Jan 13, 2026" #}
```

### `iso_date`

ISO 8601 date format:

```jinja2
{{ page.date | iso_date }}
{# "2026-01-13" #}
```

### `relative_time`

Relative time (e.g., '2 hours ago', 'yesterday'):

```jinja2
{{ page.date | relative_time }}
{# "3 days ago" #}

{{ page.date | relative_time(showAgo=False) }}
{# "3 days" #}
```

### `time_only`

Format as time only '6:00 PM':

```jinja2
{{ page.date | time_only }}
{# "6:00 PM" #}
```

### `strptime`

Parse a string into a datetime using a format string:

```jinja2
{{ "2026-01-13" | strptime("%Y-%m-%d") | fancy_date }}
```

### `rfc822_date`

Format for RSS feeds (RFC 822):

```jinja2
{{ page.date | rfc822_date }}
{# "Tue, 13 Jan 2026 18:00:00 GMT" #}
```

---

## Number Filters

Filters for formatting numeric values.

### `number_format`

Format with thousand separators:

```jinja2
{{ 1234567.89 | number_format }}
{# "1,234,568" #}

{{ 1234567.89 | number_format(2) }}
{# "1,234,567.89" #}
```

### `percentage`

Format as percentage:

```jinja2
{{ 0.5 | percentage }}
{# "50.0%" #}

{{ 0.5 | percentage(0) }}
{# "50%" #}
```

### `ordinal`

Convert number to ordinal (1st, 2nd, 3rd):

```jinja2
{{ 1 | ordinal }}
{# "1st" #}

{{ 23 | ordinal }}
{# "23rd" #}

{{ 42 | ordinal }}
{# "42nd" #}
```

### `filesize`

Human-readable byte sizes:

```jinja2
{{ 1024 | filesize }}
{# "1.0 KB" #}

{{ 1048576 | filesize }}
{# "1.0 MB" #}
```

---

## Currency & Locale Filters

These filters require the `pycountry` library (`pip install pycountry`). They gracefully degrade with built-in fallbacks when pycountry is absent.

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

### `compact_currency`

Compact format for large numbers:

```jinja2
{{ 1500000 | compact_currency }}
{# "$1.5M" #}

{{ 2500 | compact_currency("EUR") }}
{# "€2.5K" #}
```

### `currency_name`

Convert ISO currency code to full name:

```jinja2
{{ "USD" | currency_name }}
{# "US Dollar" #}

{{ "KES" | currency_name }}
{# "Kenyan Shilling" #}
```

### `country_name`

Convert ISO country code to full name:

```jinja2
{{ "US" | country_name }}
{# "United States" #}

{{ "KE" | country_name }}
{# "Kenya" #}
```

Supports both alpha-2 and alpha-3 codes.

### `country_flag`

Convert ISO country code to emoji flag:

```jinja2
{{ "US" | country_flag }}
{# 🇺🇸 #}

{{ "KE" | country_flag }}
{# 🇰🇪 #}
```

### `language_name`

Convert language code to full name:

```jinja2
{{ "en" | language_name }}
{# "English" #}

{{ "sw" | language_name }}
{# "Swahili" #}
```

---

## Image Filters

See [Image Processing](images.md) for complete documentation and examples.

### `image`

Generate an image URL or responsive `<img>` tag with `srcset`:

```jinja2
{# Single URL #}
<img src="{{ '/photos/photo.jpg' | image(w=800) }}" alt="Photo">

{# Responsive srcset #}
{{ '/photos/photo.jpg' | image(widths=[400, 800, 1200], alt="Photo") }}
```

The `image` filter is the primary API. `image_url` and `responsive_image` are deprecated.

### `image_cdn`

Transform an image URL through the configured CDN:

```jinja2
{{ '/photos/photo.jpg' | image_cdn(w=400, q=80) }}
```

Provider is configured via `site_data.image_cdn`.

### `image_dimensions`

Read width/height of a local image:

```jinja2
<img {{ '/photos/photo.jpg' | image_dimensions }} src="...">
{# ' width="1920" height="1080"' #}
```

### `dominant_color`

Extract the dominant color as a hex string:

```jinja2
<div style="background-color: {{ '/photos/photo.jpg' | dominant_color }}">
```

### `img_attrs`

Build `src loading decoding width height` attr string:

```jinja2
<img {{ '/photos/photo.jpg' | img_attrs(width=800, height=600) }}>
```

### `lazy_image`

Inject lazy/async/referrerpolicy attributes:

```jinja2
{{ lazy_html | lazy_image }}
```

### `image_url` (deprecated)

Legacy filter for generating an image URL. Prefer `image`.

### `responsive_image` (deprecated)

Legacy filter for generating responsive `<img>` tags. Prefer `image`.

---

## HTML Filters

Filters for sanitizing, stripping, and minifying HTML content.

### `sanitize`

Strip unsafe HTML tags and attributes using [Bleach](https://github.com/mozilla/bleach):

```jinja2
{{ user_comment | sanitize }}
```

Allows a broad set of safe HTML5 tags by default. Pass overrides to customize:

```jinja2
{{ content | sanitize(tags=["p", "img", "a"]) | safe }}
```

See [Security](security.md) for full details and configuration.

### `strip_html`

Remove HTML tags/comments and collapse whitespace:

```jinja2
{{ "<p>Hello <b>World</b></p>" | strip_html }}
{# "Hello World" #}
```

### `strip_comments`

Remove HTML comments from the output:

```jinja2
{{ content | strip_comments }}
```

Can be used as a block filter:

```jinja2
{% filter strip_comments %}
<!-- this comment will be removed -->
<p>visible content</p>
{% endfilter %}
```

### `minify_html`

Minify HTML by removing unnecessary whitespace and newlines:

```jinja2
{{ content | minify_html }}
```

> Warning: Regex-based minifier, does not respect `<pre>` tags.

---

## Content Filters

Filters for rendering markdown, embeds, headings, and avatars.

### `markdown`

Render a Markdown string to HTML:

```jinja2
{{ "This is **bold** and *italic*" | markdown | safe }}
```

Inline mode (no wrapping `<p>` tags):

```jinja2
{{ "**bold**" | markdown(inline=True) | safe }}
```

See [Markdown Rendering](markdown.md) for full details.

### `embed`

Convert a video, social, or gist URL into embed HTML:

```jinja2
{{ "https://www.youtube.com/watch?v=dQw4w9WgXcQ" | embed  | safe}}

{{ "https://twitter.com/user/status/123456789" | embed  | safe}}

{{ "https://gist.github.com/user/abc123" | embed | safe }}

{{ "https://codepen.io/user/pen/abcde" | embed | safe }}

{{ "https://vimeo.com/12345678" | embed  | safe}}
```

Falls back to a plain `<a>` link for unknown providers.

### `headings`

Extract `[(id, text, level), ...]` from rendered HTML:

```jinja2
{% for id, text, level in content | headings %}
    <a href="#{{ id }}">{{ text }}</a>
{% endfor %}
```

### `toc_from_html`

Render a `<nav><ul>` table of contents from HTML headings:

```jinja2
{{ content | toc_from_html }}

{{ content | toc_from_html(min_level=2, max_level=3, klass="my-toc") }}
```

### `gravatar`

Return a Gravatar URL for an email:

```jinja2
<img src="{{ user.email | gravatar(size=80) }}" alt="Avatar">
```

---

## Utility Filters

Helper filters for common template patterns.

### `default_if_none`

Return default value if None:

```jinja2
{{ page.author | default_if_none("Unknown") }}
```

### `yesno`

Convert boolean to yes/no text:

```jinja2
{{ page.published | yesno }}
{# "Yes" or "No" #}

{{ page.published | yesno("Published", "Draft") }}
```

### `absolute_url`

Resolve a relative URL against the site URL:

```jinja2
{{ "/about" | absolute_url }}
{# "https://example.com/about" #}
```

Resolves against `site_data.web.site_url` or the request base URL.

### `cache_bust`

Append cache-busting query string (mtime or sha8) to a static asset URL:

```jinja2
<link href="{{ '/static/site.css' | cache_bust }}" rel="stylesheet">
{# '/static/site.css?v=1736719200' #}

{{ '/static/app.js' | cache_bust(mode="sha8") }}
{# '/static/app.js?v=a1b2c3d4' #}
```

Resolves files under the configured static directory.

### `inline`

Inline a static asset's contents directly into the page:

```jinja2
<style>{{ '/static/critical.css' | inline }}</style>

<img src="{{ '/static/icon.svg' | inline(encode="data-uri") }}">
```

Looks up files under the configured static directory.

---

← [Previous: Templates](templates.md) | [Next: Markdown](markdown.md) →
