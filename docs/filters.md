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
{% minify_html(enabled=(mode != 'development')) %}
    <html>
      ...
    </html>
{% endfilter %}
```

**Combined Usage Example:**

This is the recommended setup for your `base.html` file to ensure maximum performance in production while keeping development easy.

```jinja
{% filter strip_comments(enabled=(mode != 'development')) | minify_html(enabled=(mode != 'development')) %}
    <html>
      ...
    </html>
{% endfilter %}
```

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

**Usage:**
```jinja
<h1>{{ title | title_case }}</h1>
<p>{{ content | excerpt(150) }}</p>
```

---

## 💰 Currency & Finance

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

**Usage:**
```jinja
<!-- Custom Yes/No labels -->
Active: {{ is_active | yesno("Online", "Offline") }}

<!-- File Size -->
Download size: {{ 2500000 | filesize }}
```
