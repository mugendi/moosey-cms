# CLI Reference

moosey-cms ships with a command-line tool for scaffolding admin templates into your project.

## `moosey-cms setup`

Copies the bundled admin templates (dashboard, file browser, editor) into your project's templates directory.

```bash
moosey-cms setup --templates ./templates
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--templates` | `./templates` | Path to your project's templates directory |

### What it does

1. Creates a `admin/` subdirectory inside your templates directory
2. Copies the bundled admin templates into it:
   - `base.html` — admin layout with sidebar navigation
   - `dashboard.html` — overview page with stats and quick actions
   - `list.html` — file/directory browser
   - `editor.html` — tabbed markdown + metadata editor (TUI Editor + Guifier)

### After running

Add the `admin` config to your `init_cms()` call:

```python
init_cms(
    app=app,
    host="localhost",
    port=8000,
    dirs={
        "content": BASE_DIR / "content",
        "templates": BASE_DIR / "templates",
    },
    mode="development",
    site_data={...},
    admin={"prefix": "admin/content", "templates": "admin"},
)
```

Then visit `/admin/content/` in your browser.

### Customizing templates

The copied templates are plain Jinja2 + Tailwind CSS. Edit them in your project's `templates/admin/` directory to match your site's look and feel. The bundled templates are only used as a starting point — changes to your copies are never overwritten.

## Coming Soon

- `moosey-cms build` — build static site to `_site/`
- `moosey-cms serve` — development server (currently use `uvicorn` directly)
