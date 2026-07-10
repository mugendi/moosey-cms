# Markdown Rendering

moosey-cms provides a `markdown` filter for rendering Markdown content via Python-Markdown with pymdown-extensions.

## `markdown`

Converts Markdown text to HTML:

```jinja2
{{ "This is **bold** and *italic*" | markdown | safe }}
```

```html
<p>This is <strong>bold</strong> and <em>italic</em></p>
```

### Inline Mode

Pass `inline=True` to drop wrapping `<p>` tags for short snippets:

```jinja2
{{ "This is **bold** and *italic*" | markdown(inline=True) | safe }}
```

```html
This is <strong>bold</strong> and <em>italic</em>
```

## Enabled Extensions

The following Markdown extensions are always enabled:

| Extension | Features |
|-----------|----------|
| `markdown.extensions.tables` | GFM-style tables |
| `markdown.extensions.toc` | Table of Contents generation |
| `pymdownx.magiclink` | Auto-link URLs, emails, GitHub references |
| `pymdownx.betterem` | Improved emphasis handling |
| `pymdownx.tilde` | Subscript (`~text~`) and strikethrough (`~~text~~`) |
| `pymdownx.emoji` | Emoji shortcodes (`:smile:` → 😄) |
| `pymdownx.tasklist` | GFM task lists (`- [x] done`) |
| `pymdownx.superfences` | Fenced code blocks with syntax highlighting |
| `pymdownx.saneheaders` | Prevent false header matches |
| `pymdownx.arithmatex` | LaTeX math rendering |
| `pymdownx.blocks.admonition` | Admonition/callout blocks |
| EmoticonExtension | Text emoticons (`:)` → 🙂, `<3` → ❤️) |

## Syntax Highlighting

Code blocks use Pygments via `pymdownx.superfences`. Apply a Pygments CSS theme in your template:

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pygments/2.19.1/pygments.min.css">
```

````markdown
```python
def hello():
    print("Hello, World!")
```
````

---

← [Previous: Filters](filters.md) | [Next: Images](images.md) →
