# Markdown Rendering

moosey-cms provides two Jinja2 filters for rendering Markdown content.

These require the `markdown` extra:

```bash
pip install moosey-cms[markdown]
```

## `markdown`

Converts Markdown text to full HTML. Wraps the output in a `<div class="content">`.

```jinja2
{{ page.content | markdown }}
```

```html
<div class="content">
<h1>Hello</h1>
<p>Welcome to my site.</p>
</div>
```

### Syntax Highlighting

Uses Pygments for code blocks. Apply a Pygments CSS theme in your template:

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pygments/2.19.1/pygments.min.css">
```

## `markdown_inline`

Converts Markdown to inline HTML **without** block-level wrappers. Use for short strings inside paragraphs.

```jinja2
{{ "This is **bold** and *italic*" | markdown_inline }}
```

```html
This is <strong>bold</strong> and <em>italic</em>
```

## Configuration

Markdown rendering supports these `pyproject.toml` settings:

```toml
[tool.moosey-cms]
markdown.extensions = ["extra", "codehilite", "toc", "sane_lists"]
markdown.codehilite_css = true
```

| Setting | Default | Description |
|---------|---------|-------------|
| `markdown.extensions` | `["extra", "codehilite", "toc", "sane_lists", "nl2br"]` | Python-Markdown extensions to enable |
| `markdown.codehilite_css` | `true` | Whether to include inline Pygments CSS |
