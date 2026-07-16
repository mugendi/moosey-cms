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
4. Uses the shared setup workflow to generate `.moosey-cms.yaml`, including
   the admin brand name, admin title, home-link label, and home-link URL

### After running

```bash
cd my-site
moosey-cms dev
```

### Git Versioning

During `init`, you are prompted for an "auto-push to remote" setting. This controls
whether file saves are automatically pushed to your Git remote. The value is stored
as `git.auto_push` in `.moosey-cms.yaml` (default: `false`). Even with auto-push
enabled, rollback commits are never pushed.

## `moosey-cms config`

Create or update `.moosey-cms.yaml` in an existing project. This command uses
the same prompts and configuration builder as `moosey-cms init`, preserving
the crypto key and advanced settings unless explicitly replaced.

```bash
moosey-cms config
```

Use `--force` to skip the overwrite confirmation or `--generate-key` to
rotate the crypto key. The command also prompts for the `git.auto_push`
setting, which controls whether file saves are automatically pushed to
your Git remote.

## `moosey-cms admin`

Copy bundled admin templates and static files into your project.

```bash
moosey-cms admin --templates ./templates --static ./static
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--templates` | `./templates` | Path to your project's templates directory |
| `--static` | `./static` | Path to your project's static directory |

### What it does

1. Creates an `admin/` subdirectory inside your templates directory
2. Copies the bundled admin templates into it:
   - `base.html` — admin layout with sidebar navigation
   - `dashboard.html` — overview page with stats and quick actions
   - `list.html` — file/directory browser
   - `editor.html` — tabbed markdown + metadata editor (TUI Editor + Guifier)
   - `admin.js` — shared JavaScript utilities
3. Creates an `admin/` subdirectory inside your static directory
4. Copies the bundled admin static files into it:
   - `admin.css` — pre-built Tailwind CSS with CSS custom properties
   - `admin.js` — admin JavaScript (editor initialization, etc.)
   - `editor.js` — editor JavaScript (TUI Editor setup)

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
        "static": BASE_DIR / "static",
    },
    mode=os.environ.get("MOOSEY_MODE", "development"),
    site_data={...},
    admin={"prefix": "admin/content", "templates": "admin"},
)
```

Then visit `/admin/content/` in your browser.

### Customizing the admin appearance

The admin CSS uses Tailwind CSS with CSS custom properties for theming. Edit `static/admin/admin.css` to customize colors:

```css
:root {
    --moose-50: #eff6ff;
    --moose-100: #dbeafe;
    --moose-200: #bfdbfe;
    --moose-300: #93c5fd;
    --moose-400: #60a5fa;
    --moose-500: #3b82f6;
    --moose-600: #2563eb;
    --moose-700: #1d4ed8;
    --moose-800: #1e40af;
    --moose-900: #1e3a8a;
    --moose-950: #172554;
}
```

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
