# Security

## HTML Sanitization

The `sanitize` filter removes unsafe HTML tags and attributes using [Bleach](https://github.com/mozilla/bleach).

```jinja2
{{ user_comment | sanitize }}
```

Requires `pip install bleach`.

### Allowed Tags

By default, only safe tags are permitted:

`a`, `abbr`, `acronym`, `b`, `blockquote`, `code`, `em`, `i`, `li`, `ol`, `strong`, `ul`

All other tags and attributes are stripped. The `<a>` tag retains its `href` attribute.

### Custom Allowed Tags

Pass a list of additional tags to allow others:

```jinja2
{{ content | sanitize(["img", "table", "tr", "td"]) }}
```

The `href` attribute is always allowed on `<a>` tags. All other attributes are stripped.

## Content Security Policy

Configure CSP headers in `pyproject.toml`:

```toml
[tool.moosey-cms.csp]
default-src = ["'self'"]
script-src = ["'self'", "https://cdn.example.com"]
style-src = ["'self'", "'unsafe-inline'"]
img-src = ["'self'", "https://images.example.com"]
```

### How CSP Headers Work

Every HTML page served by the development server or exported to `_site/` includes CSP headers when configured. These tell the browser which sources are trusted for scripts, styles, images, and other resources.

A restrictive policy (default-src: 'self') blocks all external resources by default - you must explicitly allow each external domain you use.

### CSP Directives

| Directive | Purpose |
|-----------|---------|
| `default-src` | Fallback for all resource types |
| `script-src` | Allowed script sources |
| `style-src` | Allowed stylesheet sources |
| `img-src` | Allowed image sources |
| `font-src` | Allowed font sources |
| `connect-src` | Allowed fetch/XMLHttpRequest targets |
| `frame-src` | Allowed iframe sources |
| `media-src` | Allowed video/audio sources |
| `object-src` | Allowed plugin sources |

### CSP Best Practices

```toml
[tool.moosey-cms.csp]
default-src = ["'self'"]
script-src = ["'self'"]
style-src = ["'self'", "'unsafe-inline'"]
img-src = ["'self'", "data:", "https://*.cloudfront.net"]
font-src = ["'self'", "https://fonts.gstatic.com"]
connect-src = ["'self'"]
frame-src = ["'none'"]
object-src = ["'none'"]
```

The `frame-src` and `object-src` restrictions above are strongly recommended - they prevent clickjacking and plugin-based attacks.

## Sandboxing

moosey-cms supports Jinja2 sandbox mode to restrict template expressions:

```toml
[tool.moosey-cms]
sandbox = true
```

When enabled, templates cannot access:
- Private attributes (prefix `_`)
- Built-in functions (`eval`, `exec`, `open`, `import`, `__import__`)
- Unsafe object methods
- Modules and imports

Useful when allowing untrusted users to provide templates.

## Security Headers

moosey-cms adds these security headers to every page (development and production):

| Header | Description |
|--------|-------------|
| `X-Content-Type-Options: nosniff` | Prevents MIME-type sniffing |
| `X-Frame-Options: DENY` | Prevents clickjacking |
| `Referrer-Policy: strict-origin-when-cross-origin` | Controls referrer info |

You can override them:

```toml
[tool.moosey-cms.headers]
X-Frame-Options = "SAMEORIGIN"
```

Remove a header by setting it to an empty value.
