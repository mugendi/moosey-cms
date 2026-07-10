# Security

## HTML Sanitization

The `sanitize` filter removes unsafe HTML tags and attributes using [Bleach](https://github.com/mozilla/bleach).

```jinja2
{{ user_comment | sanitize }}
```

Sanitization is applied automatically to all rendered Markdown body content in production. You can opt out or customize it via `site_data.sanitize`:

```python
site_data = {
    # Disable auto-sanitization entirely
    "sanitize": False,

    # Or customize allowed tags/attrs
    "sanitize": {
        "tags": ["p", "a", "img", "strong", "em"],
        "attrs": {"a": ["href"], "img": ["src", "alt"]},
        "strip": True,
    },
}
```

### Default Allowlist

**Allowed tags**: `a`, `abbr`, `address`, `article`, `aside`, `audio`, `b`, `bdi`, `bdo`, `blockquote`, `br`, `caption`, `cite`, `code`, `col`, `colgroup`, `data`, `dd`, `del`, `details`, `dfn`, `div`, `dl`, `dt`, `em`, `figcaption`, `figure`, `footer`, `h1`–`h6`, `header`, `hgroup`, `hr`, `i`, `img`, `ins`, `kbd`, `li`, `mark`, `nav`, `ol`, `p`, `pre`, `q`, `rp`, `rt`, `ruby`, `s`, `samp`, `section`, `small`, `source`, `span`, `strong`, `sub`, `summary`, `sup`, `table`, `tbody`, `td`, `tfoot`, `th`, `thead`, `time`, `tr`, `u`, `ul`, `var`, `video`, `wbr`

**Allowed attributes**: `class`, `id`, `title`, `lang`, `dir` on all elements; `href`, `rel`, `target` on `<a>`; `src`, `alt`, `width`, `height`, `loading` on `<img>`; etc.

**Allowed protocols**: `http`, `https`, `mailto`, `tel`

**Inline CSS**: Disabled by default. Enable by passing a `styles` list and installing `bleach[css]`.

### Using as a Filter

```jinja2
{{ untrusted_html | sanitize | safe }}
```

Customize per-use:

```jinja2
{{ content | sanitize(tags=["p", "img", "table"], attrs={"img": ["src", "alt"]}) | safe }}
```

## Security Headers

Moosey CMS adds these headers to every HTTP response via middleware:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing |
| `X-XSS-Protection` | `1; mode=block` | Enables XSS filter in older browsers |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |

These are hardcoded in the middleware and cannot currently be overridden via config.

## Path Traversal Protection

Moosey validates all URL paths against the content directory:

1. **Null byte check** — Rejects paths containing `\0`
2. **Symlink resolution** — Resolves `..` and symlinks to absolute paths
3. **Jail enforcement** — Ensures the resolved path stays inside the content directory

See `get_secure_target()` in `helpers.py`.

## Sandboxed Template Rendering

Frontmatter strings and Markdown body content are rendered through a `SandboxedEnvironment` that blocks access to private attributes (`__class__`, `__subclasses__`), dangerous built-ins (`eval`, `exec`, `open`, `import`), and module imports. Only the `site_data`, `mode`, and registered filters are available.

---

← [Previous: Admin API](admin.md) | [Next: Patterns](patterns.md) →
