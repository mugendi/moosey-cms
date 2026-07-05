<!--
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# Template Filters

Moosey CMS comes equipped with a powerful suite of Jinja2 filters. These allow you to format data, manipulate text, and clean up HTML directly within your Markdown files or HTML templates.

## Usage

Filters are applied using the pipe symbol (`|`). You can chain multiple filters together.

```jinja
{{ variable | filter_name }}
{{ variable | filter1 | filter2 }}
```

---

## 🧹 HTML & Structure

### `strip_comments`
**Type:** Block Filter  
Removes HTML comments (`<!-- ... -->`) from the enclosed content. This is useful for keeping production code clean while leaving comments in for development.

**Arguments:**
*   `enabled` (bool): If `False`, comments are preserved. Default is `True`.

**Usage:**
You typically wrap your entire `base.html` layout with this.

```jinja
<!-- example/templates/layout/base.html -->

<!-- Only strip comments if not in development mode -->
{% filter strip_comments(enabled=(mode != 'development')) %}
    <!DOCTYPE html>
    <html>
        <head>
            <!-- This comment will vanish in production -->
            <title>{{ title }}</title>
        </head>
        <body>
            {{ content }}
        </body>
    </html>
{% endfilter %}
```

### `minify_html`
**Type:** Block Filter  
Reduces file size by removing newlines, tabs, and extra spaces. It collapses multiple spaces into one and removes whitespace between HTML tags.

**Arguments:**
*   `enabled` (bool): Default `True`.

**⚠️ Important Note:** 
This filter is "aggressive." It does not detect `<pre>` or `<textarea>` tags. If you use code blocks where indentation must be preserved exactly, consider disabling this filter or handling those blocks separately.

**Usage Example:**

```jinja
{% filter minify_html(enabled=(mode != 'development')) %}
    <html>
      ...
    </html>
{% endfilter %}
```

**Production Base Layout Example:**

For most sites, wrap the entire `base.html` document with both filters and enable them only when Moosey CMS is running in production mode. This keeps development output readable while stripping comments and minifying the final HTML served by production.

```jinja
{% filter strip_comments(enabled=(mode == 'production')) | minify_html(enabled=(mode == 'production')) %}
<!doctype html>
<html lang="en">
  <head>
    {{ seo() }}
    <!-- Development notes stay visible outside production. -->
  </head>
  <body>
    {% block content %}{% endblock %}
  </body>
</html>
{% endfilter %}
```

Use `mode == 'production'` when you only want this behavior for production deployments. Use a broader condition, such as `mode != 'development'`, if you also want minified output in staging or testing.

---

## 📅 Date & Time

Assuming `date_obj` is a Python datetime object (e.g., from `date: 2026-01-21` in frontmatter).

| Filter | Description | Example Input | Output |
| :--- | :--- | :--- | :--- |
| **`fancy_date`** | Formats date with ordinal suffix. | `2026-01-21 18:00` | 21st Jan, 2026 at 6:00 PM |
| **`short_date`** | Standard clean date format. | `2026-01-21` | Jan 21, 2026 |
| **`iso_date`** | ISO 8601 format (good for meta tags). | `2026-01-21` | 2026-01-21 |
| **`time_only`** | Extracts just the time. | `2026-01-21 18:00` | 6:00 PM |
| **`relative_time`** | Human readable time difference. | `(Now - 2 hours)` | 2 hours ago |
| **`strptime`** | Parse a string to datetime using a format string. | `"2026-01-21" \| strptime("%Y-%m-%d")` | `datetime(2026, 1, 21)` |
| **`rfc822_date`** | Format a date for RSS feeds. | `2026-01-21` | Thu, 21 Jan 2026 00:00:00 GMT |

**Usage:**
```jinja
<time>{{ date.created | fancy_date }}</time>
```

---

## 📝 Text Manipulation

| Filter | Description | Example Input | Output |
| :--- | :--- | :--- | :--- |
| **`truncate_words`** | Cuts text after N words. | `{{ "one two three four" | truncate_words(2) }}` | one two... |
| **`excerpt`** | Smart truncation that tries to break at the end of a sentence. | *Long paragraph* | *First few sentences...* |
| **`title_case`** | Capitalizes words intelligently (skips "and", "the", etc). | `a tale of two cities` | A Tale of Two Cities |
| **`slugify`** | Converts text to URL-friendly format. | `Hello World!` | `hello-world` |
| **`smart_quotes`** | Converts straight quotes to curly quotes. | `"Hello"` | “Hello” |
| **`read_time`** | Calculates reading time (approx 200 wpm). | *500 words text* | 3 min read |
| **`reading_time`** | Alias for `read_time`. | *500 words text* | 3 min read |
| **`strip_html`** | Removes HTML tags/comments and collapses whitespace. | `<p>Hello</p>` | Hello |

**Usage:**
```jinja
<h1>{{ title | title_case }}</h1>
<p>{{ content | excerpt(150) }}</p>
```

---

## 📝 Markdown Rendering

### `markdown`

**Type:** Filter
**Returns:** Raw HTML string (Jinja escapes it unless you pipe through `safe`).

Render an inline Markdown string to HTML using Moosey's full configured Markdown
renderer — the same pipeline used to render your `content/*.md` files.

**Arguments:**
* `inline` (bool): If `True`, the outer `<p>…</p>` wrapper added by Python-Markdown
  for single-block content is stripped so the result can sit inline inside an
  existing heading, list item, or table cell. Default `False`.

#### Simple usage

Pipe any Markdown string through `markdown` and then `safe`:

```jinja
{{ bio | markdown | safe }}
{{ "**Active** project" | markdown | safe }}
```

Because Jinja escapes by default, **always** add `| safe` — otherwise the HTML
tags show up verbatim in the browser.

Rendering a frontmatter field that holds Markdown:

```yaml
---
title: About the team
lead: |
  We are **engineers** and **supervisors** based in Nairobi.
  Every project is built around [verifiable records](/process).
---
```

```jinja
<p class="lead">{{ lead | markdown | safe }}</p>
```

#### Advanced usage

**Inline mode for headings, captions, and table cells**

When you don't want a block-level `<p>`, set `inline=True`. Moosey only unwraps a
single outer paragraph (count-checked), so multi-paragraph input still renders
predictably:

```jinja
<h1>{{ title | markdown(inline=True) | safe }}</h1>
<caption>{{ caption | markdown(inline=True) | safe }}</caption>
```

**Generate a plain-text excerpt from Markdown content**

Chain `markdown` → `strip_html` to collapse rich content to plain text:

```jinja
{{ body | markdown | strip_html | truncate_words(40) }}
```

This gives you a clean teaser string for cards, meta descriptions, or RSS
excerpts without re-parsing the Markdown yourself.

**Use inside Markdown content files**

Moosey evaluates Jinja inside `*.md` files (sandboxed), so you can render nested
fields with the filter directly in your content:

```markdown
---
intro: "Builders for the **African diaspora**."
---

{{ intro | markdown | safe }}
```

**Combine with block filters**

The block filters `strip_comments` and `minify_html` wrap their body and
post-process it, so they compose naturally on top of `markdown`:

```jinja
{% filter markdown %}{% filter minify_html(enabled=(mode == 'production')) %}
{{ long_bio }}
{% endfilter %}{% endfilter %}
```

**Use with `absolute_url` for internal links**

If your Markdown contains relative URLs, render the Markdown first, then bake
absolute URLs for email or RSS templates:

```jinja
{{ body | markdown | absolute_url | safe }}
```

#### Supported Markdown features

Moosey's `markdown` filter uses the same configured renderer as your
`content/*.md` files. The extensions below are pre-configured in
`src/moosey_cms/md.py` — no setup required. Each example below shows the
Markdown input and the exact HTML returned by `{{ content | markdown | safe }}`.

##### 1. Tables (`markdown.extensions.tables`)

**Input:**
```markdown
| Col A | Col B |
|-------|-------|
| 1     | 2     |
```

**Output:**
```html
<table>
<thead>
<tr>
<th>Col A</th>
<th>Col B</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>2</td>
</tr>
</tbody>
</table>
```

##### 2. Table of Contents (`markdown.extensions.toc`)

**Input:**
```markdown
## Section One
[TOC]
## Section Two
```

**Output:**
```html
<h2 id="section-one">Section One</h2>
<div class="toc"><span class="toctitle">Table of Contents</span><ul>
<li><a href="#section-one">Section One</a></li>
<li><a href="#section-two">Section Two</a></li>
</ul>
</div>
<h2 id="section-two">Section Two</h2>
```

**Note:** Use the `[TOC]` marker inline where you want the table to appear. The
title "Table of Contents" is configured via `extension_configs` in `md.py`.

##### 3. Magic Links — URLs, GitHub shorthand, mentions (`pymdownx.magiclink`)

**Input:**
```markdown
Visit https://example.com today.
See issue #1, PR !2, and @octocat.
Also visit www.example.com or email user@example.com.
```

**Output (condensed):**
```html
<p>Visit <a href="https://example.com">https://example.com</a> today.</p>

<p>See issue
   <a class="magiclink magiclink-github magiclink-issue"
      href="https://github.com/facelessuser/pymdown-extensions/issues/1"
      title="GitHub Issue: facelessuser/pymdown-extensions #1">#1</a>,
   PR <a class="magiclink magiclink-github magiclink-pull"
         href="https://github.com/facelessuser/pymdown-extensions/pull/2">!2</a>,
   and <a class="magiclink magiclink-github magiclink-mention"
          href="https://github.com/octocat"
          title="GitHub User: octocat">@octocat</a>.</p>

<p>Also visit <a href="http://www.example.com">www.example.com</a>
   or email
   <a href="&#109;&#97;&#105;&#108;&#116;&#111;&#58;...">&#117;&#115;&#101;&#114;&#64;...</a>.</p>
```

**Note:** `#N` and `!N` resolve against the GitHub user/repo configured in
`md.py`'s `extension_configs["pymdownx.magiclink"]` (currently
`facelessuser/pymdown-extensions`). Update that config to your own repo so your
issue/PR numbers link correctly. Email addresses are auto-linked and
HTML-escaped character-by-character (`mailto:` becomes
`&#109;&#97;&#105;&#108;&#116;&#111;&#58;…`) for anti-spam obfuscation — they
render as clickable links in browsers but appear as raw entities in HTML
source.

##### 4. Better Emphasis (`pymdownx.betterem`)

**Input:**
```markdown
**bold** and _italic_ and ***both*** and __strong__.
```

**Output:**
```html
<p><strong>bold</strong> and <em>italic</em>
   and <strong><em>both</em></strong> and <strong>strong</strong>.</p>
```

##### 5. Strikethrough (`pymdownx.tilde`)

**Input:**
```markdown
~~struck~~ and text~sub~
```

**Output:**
```html
<p><del>struck</del> and text~sub~.</p>
```

**Note:** Subscript is **disabled** in Moosey's config
(`"pymdownx.tilde": {"subscript": False}`). `~text~` renders literally. Only
`~~strike~~` produces `<del>`.

##### 6. Emoji Shortcodes (`pymdownx.emoji`)

**Input:**
```markdown
Smile :smile: thumbs :thumbsup: heart :heart:.
```

**Output:**
```html
<p>Smile
   <img alt="😄" class="emojione"
        src="https://cdnjs.cloudflare.com/ajax/libs/emojione/2.2.7/assets/png/1f604.png"
        title=":smile:" />
   thumbs <img alt="👍" class="emojione"
              src="https://cdnjs.cloudflare.com/ajax/libs/emojione/2.2.7/assets/png/1f44d.png"
              title=":thumbsup:" />
   heart <img alt="❤️" class="emojione"
              src="https://cdnjs.cloudflare.com/ajax/libs/emojione/2.2.7/assets/png/2764.png"
              title=":heart:" />.</p>
```

**Note:** Output is `<img>` tags pointing at the legacy **emojione v2.2.7 PNG
CDN** (the `pymdownx.emoji` default). To use Twemoji SVGs or a self-hosted set,
edit `extension_configs["pymdownx.emoji"]` in `src/moosey_cms/md.py`. Full
shortcode list: https://github.com/iamcal/emoji-data.

##### 7. Task Lists (`pymdownx.tasklist`)

**Input:**
```markdown
- [x] Done item
- [ ] Pending item
- regular item
```

**Output:**
```html
<ul class="task-list">
  <li class="task-list-item"><input type="checkbox" disabled checked/> Done item</li>
  <li class="task-list-item"><input type="checkbox" disabled/> Pending item</li>
  <li>regular item</li>
</ul>
```

**Note:** Checkboxes are `disabled` (display-only). To make them interactive,
style with CSS and add a small JS handler — the rendered HTML has no `<form>`.

##### 8. Fenced Code & Nested Fences (`pymdownx.superfences`)

**Input:**
````markdown
```python
def add(a, b):
    return a + b
```
````

**Output:**
```html
<pre class="highlight"><code class="language-python">def add(a, b):
    return a + b</code></pre>
```

**Note:** Syntax highlighting classes are emitted but no stylesheet is bundled.
Pair with Pygments CSS
(`pygmentize -S default -f html -a .highlight > highlight.css`) for colored
output. Unlike Python-Markdown's built-in fenced code, SuperFences supports
**nested fences inside other blocks** (admonitions, list items) using ```` ``` ````
of varying lengths or `~~~` markers.

##### 9. Sane Headers (`pymdownx.saneheaders`)

**Input:**
```markdown
# H1
## H2
###### H6
```

**Output:**
```html
<h1 id="h1">H1</h1>
<h2 id="h2">H2</h2>
<h6 id="h6">H6</h6>
```

**Note:** "Sane" means a single `#` no longer requires a space — `#H1` works.
IDs are auto-generated from the heading text (lowercased, spaces→`-`), useful
for the TOC extension's anchor links.

##### 10. Math / Arithmatex (`pymdownx.arithmatex`)

**Input:**
```markdown
Inline $E = mc^2$ and block $$\sum_{i=1}^n i$$.
```

**Output:**
```html
<p>Inline <span class="arithmatex">\(E = mc^2\)</span>
   and block $<span class="arithmatex">\(\sum_{i=1}^n i\)</span>$.</p>
```

**Note:** Arithmatex runs in **generic mode** (`"generic": True` in `md.py`). It
emits `\(...\)` and `\[...\]` LaTeX delimiters wrapped in
`<span class="arithmatex">` — it does **not** render the math itself. Add
MathJax or KaTeX client-side:

```html
<script>
  MathJax = { tex: { inlineMath: [['\\(', '\\)']],
                     displayMath: [['$$', '$$']] } };
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
```

##### 11. Admonitions (`pymdownx.blocks.admonition`) — ⚠️ use `///`, not `!!!`

**Input:**
````markdown
/// note | My Title
Body text with **bold**.

- item 1
- item 2
///
````

**Output:**
```html
<div class="admonition note">
  <p class="admonition-title">My Title</p>
  <p>Body text with <strong>bold</strong>.</p>
  <ul>
    <li>item 1</li>
    <li>item 2</li>
  </ul>
</div>
```

**⚠️ Critical:** Moosey uses the **blocks-family**
`pymdownx.blocks.admonition`, which uses `///` fences — **not** the `!!!`
syntax used by the legacy `pymdownx.admonition` (which is not installed). The
`!!! note` syntax you see in most online tutorials produces literal text.

**Supported types** (built into the extension's `types` config):
- `note`, `attention`, `caution`, `danger`, `error`
- `tip`, `hint`, `warning`, `important`
- `admonition` (generic — no title bar, no class suffix)

**Variants:**

````markdown
/// warning
No title — uses the type name.
///

/// danger | Critical Alert
Bold body **here**.
///
````

```html
<div class="admonition warning">
  <p class="admonition-title">Warning</p>
  <p>No title — uses the type name.</p>
</div>

<div class="admonition danger">
  <p class="admonition-title">Critical Alert</p>
  <p>Bold body <strong>here</strong>.</p>
</div>
```

To add custom types (e.g., `success`), edit `md.py`:
```python
extension_configs["pymdownx.blocks.admonition"] = {
    "types": ["note", "tip", "warning", "success"]
}
```

##### 12. Custom Emoticons (built-in `EmoticonExtension`)

**Input:**
```markdown
Wink ;-) and smile :-).
```

**Output:**
```html
<p>Wink <span class="emoji" title=";-)">😉</span>
   and smile <span class="emoji" title=":-)">🙂</span>.</p>
```

**Note:** This is a custom Moosey extension (not a pymdownx plugin). It converts
`:-)`, `:-D`, `;-)`, `<3`, etc. into Unicode emoji characters, **not** images.
The full dictionary is in `md.py` (`EXTENDED_EMOTICONS`).

**Gotcha:** `:/` is **intentionally not** handled (it would break URLs like
`https://`). Use `:-/` instead for the confused face.

#### Notes

- **Security:** the Markdown renderer does **not** sanitize raw HTML in input
  (`markdown.extensions` allow inline HTML by default). Use trusted content, or
  pair with `strip_html` after rendering to remove unwanted tags. Moosey's
  Jinja-in-Markdown sandbox covers template-level RCE concerns but does not
  sanitize `markdown` filter output.
- **Performance:** rendering the same field repeatedly is cheap; Moosey's
  upstream content/template caching handles repeated renders at the page level.
- **Empty inputs:** `None`, `""`, and missing fields all return `""` so the
  filter is safe to call on optional frontmatter.

---

## 💰 Currency & Finance

> **Note:** The currency, country, and locale filters optionally use `pycountry` for comprehensive name/flag resolution. When `pycountry` is not installed, they fall back to a built-in lookup table with common entries. All filters remain functional without the extra dependency.

| Filter | Description | Arguments | Output |
| :--- | :--- | :--- | :--- |
| **`currency`** | Formats number with symbol. | `code` (default 'USD') | `$1,234.56` |
| **`compact_currency`** | Shortens large numbers. | `code` (default 'USD') | `$1.5M`, `$45K` |
| **`currency_name`** | Converts ISO code to name. | - | `KES` → `Kenyan Shilling` |

**Usage:**
```jinja
<!-- Custom Currency -->
Price: {{ 4500 | currency('EUR') }} 
<!-- Output: €4,500.00 -->
```

---

## 🌍 Geography & Locale

Requires valid ISO 3166-1 alpha-2 or alpha-3 codes.

| Filter | Description | Example Input | Output |
| :--- | :--- | :--- | :--- |
| **`country_flag`** | Converts country code to Emoji flag. | `US` | 🇺🇸 |
| **`country_name`** | Converts code to full name. | `DE` | Germany |
| **`language_name`** | Converts language code to name. | `fr` | French |

**Usage:**
```jinja
<span>Made in {{ 'JP' | country_flag }} {{ 'JP' | country_name }}</span>
```

---

## 🔢 Numbers & Math

| Filter | Description | Example Input | Output |
| :--- | :--- | :--- | :--- |
| **`number_format`** | Adds thousand separators. | `10000` | `10,000` |
| **`percentage`** | Formats float as percent. | `50.5` | `50.5%` |
| **`ordinal`** | Adds ordinal suffix to integer. | `3` | `3rd` |

---

## 🛠 Utilities

| Filter | Description | Example Input | Output |
| :--- | :--- | :--- | :--- |
| **`filesize`** | Bytes to human readable size. | `1048576` | `1.0 MB` |
| **`yesno`** | Boolean to text. | `True` | `Yes` (or custom) |
| **`default_if_none`** | Fallback if value is None. | `None` | *(Default string)* |
| **`absolute_url`** | Resolves a relative path against `site_data.web.site_url` or the request base URL. | `/about` | `https://example.com/about` |

**Usage:**
```jinja
<!-- Custom Yes/No labels -->
Active: {{ is_active | yesno("Online", "Offline") }}

<!-- File Size -->
Download size: {{ 2500000 | filesize }}
```
