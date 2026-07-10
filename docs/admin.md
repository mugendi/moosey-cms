# Admin Dashboard & API

Moosey CMS ships with a full-featured admin dashboard — a Tailwind-rendered HTML UI for content CRUD operations, plus a JSON API for programmatic access.

The editor includes a searchable picker for runtime-supported metadata. See [Frontmatter fields](frontmatter.md) for the complete reference and automatic `.moosey/frontmatter_fields.yaml` project overrides.

---

## Quick Start

1. **Install the admin templates** into your project:
   ```bash
   moosey-cms admin --templates ./templates
   ```
   This copies `dashboard.html`, `list.html`, `editor.html`, `base.html`, and `admin.js` into `templates/admin/`.

2. **Enable the admin** by passing the `admin` dict to `init_cms()`:
   ```python
   init_cms(
       app,
       ...,
       admin={"prefix": "admin/content", "templates": "admin"},
   )
   ```

3. **Visit the dashboard** at `http://localhost:8000/admin/content/`.

---

## Configuration

### `admin` dict (recommended)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `prefix` | `str` | — (required) | URL prefix, e.g. `"admin/content"`. No leading/trailing slash. |
| `templates` | `str` | `"admin"` | Subdirectory within your `templates/` dir where admin templates live. |

```python
admin={"prefix": "admin/content", "templates": "admin"}
```

---

## Admin Routes

### HTML Dashboard Routes

| Route | Template | Description |
|-------|----------|-------------|
| `GET /{prefix}/` | `dashboard.html` | Overview with stats cards, recent files, quick actions |
| `GET /{prefix}/browse/` | `list.html` | File/directory browser with breadcrumbs |
| `GET /{prefix}/browse/{subpath}` | `list.html` | Browse a specific subdirectory |
| `GET /{prefix}/edit/` | `editor.html` | Create a new file |
| `GET /{prefix}/edit/{file_path}` | `editor.html` | Edit an existing file |

These routes use `Jinja2` templates located in your project's `templates/admin/` directory (configurable via the `templates` key). The admin router is registered **before** the catch-all content router, so admin paths never fall through to a 404 page.

### JSON API Routes

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/{prefix}/list` | List content root directory |
| `GET` | `/{prefix}/list/{subpath}` | List a subdirectory |
| `GET` | `/{prefix}/file/{file_path}` | Read a file (frontmatter + body) |
| `POST` | `/{prefix}/file/{file_path}` | Create a new file |
| `PUT` | `/{prefix}/file/{file_path}` | Update an existing file |
| `DELETE` | `/{prefix}/file/{file_path}` | Delete a file |
| `POST` | `/{prefix}/dir/{dir_path}` | Create a directory |
| `DELETE` | `/{prefix}/dir/{dir_path}` | Delete a directory |

All JSON endpoints return structured responses and standard HTTP status codes.

See the [JSON API Reference](#json-api-reference) section below for detailed endpoint docs.

---

## Customizing Templates

### File List

The admin templates live in `templates/admin/`:

| File | Purpose |
|------|---------|
| `base.html` | Layout with Tailwind sidebar, nav, flash messages, responsive hamburger menu |
| `dashboard.html` | Dashboard overview extending `base.html` |
| `list.html` | File browser with breadcrumbs and CRUD actions |
| `editor.html` | Markdown editor with TUI Editor (content) and Guifier (metadata) |
| `admin.js` | Shared JS utilities (`toggleSidebar`, `showFlash`, escape-key modals) |

### Template Variables

Every admin page receives:

| Variable | Type | Description |
|----------|------|-------------|
| `admin_config` | `dict` | The admin config dict (`prefix`, `templates` keys) |
| `mode` | `str` | `"development"` or `"production"` |
| `request` | `Request` | The Starlette/FastAPI request object |
| `subpath` | `str` | Current browse path (list page only) |
| `file_path` | `str` | Current file path (editor page only) |

Access `admin_config.prefix` in templates for URL building:
```jinja2
{% set prefix = admin_config.prefix %}
<a href="/{{ prefix }}/browse/">Content</a>
```

### Editor Tabbed Interface

The editor uses a two-tab interface:

- **Content Tab** (default): TUI Editor for WYSIWYG/Markdown editing
- **Metadata Tab**: Guifier for visual YAML frontmatter editing

Both editors load via CDN and fall back to basic editors if unavailable.

### Adding Custom Routes

Register additional admin pages inside your application — they coexist with the admin router:

```python
@app.get("/admin/content/analytics")
async def analytics_page(request: Request):
    return templates.TemplateResponse("admin/analytics.html", {
        "request": request,
        "admin_config": app.state.admin,
    })
```

---

## Authentication

The admin dashboard has **no built-in authentication** — you must secure it yourself. Two approaches:

### Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware

class AdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/admin/"):
            auth = request.headers.get("Authorization")
            if auth != "Bearer my-secret-token":
                return HTMLResponse(status_code=401)
        return await call_next(request)

app.add_middleware(AdminAuthMiddleware)
```

### FastAPI Dependency

```python
from fastapi import Depends, HTTPException, status

async def verify_admin(request: Request):
    # check session, cookie, header, etc.
    if not request.session.get("admin_logged_in"):
        raise HTTPException(status_code=403)

# Apply via routes that call the admin templates:
@app.get("/admin/", dependencies=[Depends(verify_admin)])
async def admin_dashboard():
    ...
```

---

## Tailwind in Production

The admin templates load Tailwind CSS via CDN for development convenience. Additionally, the editor loads TUI Editor and Guifier via CDN for development.

```html
<!-- WARNING: The CDN script is NOT recommended for production. -->
<script src="https://cdn.tailwindcss.com"></script>
```

For production, build the CSS file:

```bash
npm init -y
npm install tailwindcss @tailwindcss/cli
npx tailwindcss -i ./src/input.css -o ./static/admin.css
```

Create `src/input.css`:
```css
@import "tailwindcss";
```

Then configure `tailwind.config.js` to scan your admin templates:
```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/admin/**/*.html"],
  theme: {
    extend: {
      colors: {
        moose: {
          50: '#f8f6f3', 100: '#eee9e2', 200: '#ddd3c4',
          300: '#c8b69f', 400: '#b3987a', 500: '#a08260',
          600: '#8a6d50', 700: '#725843', 800: '#5f4a3a',
          900: '#513f33', 950: '#2c2019',
        },
      },
    },
  },
};
```

Replace the CDN script in `base.html` with a local stylesheet link:
```html
<link rel="stylesheet" href="/static/admin.css">
```

---

## JSON API Reference

### List directory

```
GET /{prefix}/list
GET /{prefix}/list/{subpath}
```

Returns all files and directories in the given path (default: content root). Each entry includes the Markdown `title` from frontmatter.

**Response:**

```json
{
  "path": "blog",
  "entries": [
    {
      "name": "hello-world.md",
      "path": "blog/hello-world.md",
      "type": "file",
      "size": 2048,
      "modified": "2026-07-10T12:00:00",
      "title": "Hello, World!",
      "is_index": false
    },
    {
      "name": "recipes",
      "path": "blog/recipes",
      "type": "directory",
      "size": 0,
      "modified": "2026-07-10T12:00:00",
      "title": "Recipes",
      "is_index": true
    }
  ]
}
```

**Example:**

```bash
curl http://localhost:8000/admin/content/list
curl http://localhost:8000/admin/content/list/blog
```

---

### Get file

```
GET /{prefix}/file/{file_path}
```

Read a Markdown file and return its frontmatter and body.

**Response:**

```json
{
  "path": "blog/hello-world.md",
  "frontmatter": {
    "title": "Hello, World!",
    "tags": ["python", "tutorial"],
    "date": "2026-01-15"
  },
  "body": "Welcome to my blog post.\n\nThis is the content.",
  "size": 2048,
  "modified": "2026-07-10T12:00:00"
}
```

**Example:**

```bash
curl http://localhost:8000/admin/content/file/blog/hello-world.md
```

---

### Create file

```
POST /{prefix}/file/{file_path}
```

Create a new Markdown file. Returns `409` if the file already exists.

**Request body:**

```json
{
  "frontmatter": {
    "title": "New Post",
    "tags": ["draft"],
    "draft": true
  },
  "body": "Write your content here."
}
```

**Response:**

```json
{
  "path": "blog/new-post.md",
  "status": "created"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/admin/content/file/blog/new-post.md \
  -H "Content-Type: application/json" \
  -d '{
    "frontmatter": {"title": "New Post", "draft": true},
    "body": "Write your content here."
  }'
```

---

### Update file

```
PUT /{prefix}/file/{file_path}
```

Replace the full contents of an existing Markdown file. Returns `404` if the file does not exist.

**Request body:** Same format as create.

**Response:**

```json
{
  "path": "blog/hello-world.md",
  "status": "updated"
}
```

**Example:**

```bash
curl -X PUT http://localhost:8000/admin/content/file/blog/hello-world.md \
  -H "Content-Type: application/json" \
  -d '{
    "frontmatter": {"title": "Hello, World!", "tags": ["python"]},
    "body": "Updated content."
  }'
```

---

### Delete file

```
DELETE /{prefix}/file/{file_path}
```

**Response:**

```json
{
  "path": "blog/hello-world.md",
  "status": "deleted"
}
```

**Example:**

```bash
curl -X DELETE http://localhost:8000/admin/content/file/blog/hello-world.md
```

---

### Create directory

```
POST /{prefix}/dir/{dir_path}
```

Returns `409` if the directory already exists.

**Response:**

```json
{
  "path": "blog/recipes",
  "status": "created"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/admin/content/dir/blog/recipes
```

---

### Delete directory

```
DELETE /{prefix}/dir/{dir_path}
```

**Recursively** deletes the directory and all its contents. Cannot delete the content root.

**Response:**

```json
{
  "path": "blog/recipes",
  "status": "deleted"
}
```

**Example:**

```bash
curl -X DELETE http://localhost:8000/admin/content/dir/blog/recipes
```

---

### Path Traversal Protection

All paths are resolved against the content root using strict `pathlib` checks. Attempts to escape the content directory (`../../etc/passwd`) are blocked before the route handler runs.

### Atomic Writes

Files are written atomically via a temp-file + `os.replace()` pattern. If a write fails mid-stream, the original file is not corrupted — the temp file is cleaned up automatically.

### Error Responses

| Status | Meaning | Example |
|--------|---------|---------|
| `400` | Path is the wrong type | `"Path is a directory, not a file"` |
| `404` | File or directory does not exist | `"File not found"` |
| `409` | Resource already exists | `"File already exists"` |
| `422` | Request body failed validation | Pydantic validation error |
| `500` | Internal error | `"Failed to parse file: ..."` |

---

### Static file browsing

Browse, upload, and manage files in the configured static directory.

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/{prefix}/static[/subpath]` | List files and directories |
| `POST` | `/{prefix}/static/upload/{path}` | Upload a file (multipart form) |
| `POST` | `/{prefix}/static/mkdir/{path}` | Create a directory |

**Requires** `dirs["static"]` to be configured in `init_cms()`. If not configured, these endpoints are not registered.

#### List static files

```
GET /{prefix}/static
GET /{prefix}/static/{subpath}
```

Returns files and directories with MIME types and URLs.

**Response:**

```json
{
  "path": "images",
  "entries": [
    {
      "name": "photo.jpg",
      "path": "images/photo.jpg",
      "type": "file",
      "size": 204800,
      "modified": "2026-07-10T12:00:00",
      "mime_type": "image/jpeg",
      "url": "/static/images/photo.jpg"
    }
  ]
}
```

**Example:**

```bash
curl http://localhost:8000/admin/content/static
curl http://localhost:8000/admin/content/static/images
```

#### Upload file

```
POST /{prefix}/static/upload/{path}
```

Upload a file via `multipart/form-data`. Parent directories are created automatically. Max 10MB.

**Example:**

```bash
curl -X POST http://localhost:8000/admin/content/static/upload/images/photo.jpg \
  -F "file=@photo.jpg"
```

#### Create directory

```
POST /{prefix}/static/mkdir/{path}
```

Returns `409` if the directory already exists.

**Example:**

```bash
curl -X POST http://localhost:8000/admin/content/static/mkdir/images/blog
```

---

## Example: Full CRUD Session

```bash
# Create a directory
curl -X POST http://localhost:8000/admin/content/dir/drafts

# Create a file
curl -X POST http://localhost:8000/admin/content/file/drafts/post.md \
  -H "Content-Type: application/json" \
  -d '{"frontmatter": {"title": "My Draft"}, "body": "Work in progress."}'

# Read it back
curl http://localhost:8000/admin/content/file/drafts/post.md

# Update it
curl -X PUT http://localhost:8000/admin/content/file/drafts/post.md \
  -H "Content-Type: application/json" \
  -d '{"frontmatter": {"title": "My Draft", "draft": true}, "body": "Final version."}'

# List the directory
curl http://localhost:8000/admin/content/list/drafts

# Delete the file
curl -X DELETE http://localhost:8000/admin/content/file/drafts/post.md

# Delete the directory
curl -X DELETE http://localhost:8000/admin/content/dir/drafts
```

---

← [Previous: SEO](seo.md) | [Next: Security](security.md) →
