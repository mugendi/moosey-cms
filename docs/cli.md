# CLI Reference

moosey-cms ships with a command-line tool for managing your site — scaffolding, admin setup, and running servers.

## `moosey-cms init`

Scaffold a new site by copying the bundled example app to a target directory.

```bash
moosey-cms init ./my-site
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--force` | `false` | Overwrite the target directory if it already exists |

### What it does

1. Copies the entire example app to the target directory:
   - `main.py` — FastAPI app with `init_cms()`
   - `content/` — sample content files
   - `templates/` — Jinja2 templates
   - `advanced/` — advanced examples
   - `assets/` — static assets
2. Patches `main.py` to read `MOOSEY_MODE` from environment (instead of hardcoded `"development"`)
3. Skips `__pycache__` directories

### After running

```bash
cd my-site
moosey-cms dev
```

## `moosey-cms admin`

Copy bundled admin templates (dashboard, file browser, editor) into your project's templates directory.

```bash
moosey-cms admin --templates ./templates
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--templates` | `./templates` | Path to your project's templates directory |

### What it does

1. Creates an `admin/` subdirectory inside your templates directory
2. Copies the bundled admin templates into it:
   - `base.html` — admin layout with sidebar navigation
   - `dashboard.html` — overview page with stats and quick actions
   - `list.html` — file/directory browser
   - `editor.html` — tabbed markdown + metadata editor (TUI Editor + Guifier)
   - `admin.js` — shared JavaScript utilities

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
    mode=os.environ.get("MOOSEY_MODE", "development"),
    site_data={...},
    admin={"prefix": "admin/content", "templates": "admin"},
)
```

Then visit `/admin/content/` in your browser.

### Customizing templates

The copied templates are plain Jinja2 + Tailwind CSS. Edit them in your project's `templates/admin/` directory to match your site's look and feel. The bundled templates are only used as a starting point — changes to your copies are never overwritten.

## `moosey-cms dev`

Run the development server with hot-reload.

```bash
moosey-cms dev
moosey-cms dev --host 127.0.0.1 --port 3000
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind host |
| `--port` | `8000` | Bind port |

### What it does

1. Verifies `main.py` exists in the current directory
2. Sets `MOOSEY_MODE=development` in the environment
3. Runs `uvicorn main:app --reload`

## `moosey-cms prod`

Run the production server (no hot-reload).

```bash
moosey-cms prod
moosey-cms prod --host 127.0.0.1 --port 9000
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Bind host |
| `--port` | `8000` | Bind port |

### What it does

1. Verifies `main.py` exists in the current directory
2. Sets `MOOSEY_MODE=production` in the environment
3. Runs `uvicorn main:app` (no reload)
