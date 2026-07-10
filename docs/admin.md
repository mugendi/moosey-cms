# Admin API

A built-in REST API for programmatic content management. Create, update, and delete Markdown files and directories — no database required.

## Quick Start

Pass `admin_prefix` to `init_cms()`:

```python
init_cms(
    app,
    ...,
    admin_prefix="admin/content",
)
```

The admin API is now live at `http://localhost:8000/admin/content/...`.

## Security

!!! warning
    The admin API has **no built-in authentication**. You must secure it yourself — for example, with a [FastAPI dependency](https://fastapi.tiangolo.com/advanced/security/) or middleware that checks credentials before the admin routes are reached.

All admin endpoints are plain JSON. There is no HTML UI — use them as the backend for your own editor.

## Enabling

| Parameter | Type | Description |
|-----------|------|-------------|
| `admin_prefix` | `str` | URL prefix without leading slash (e.g. `"admin"`, `"admin/content"`) |

```python
# Basic — API at /admin/...
init_cms(app, ..., admin_prefix="admin")

# Namespaced — API at /admin/content/...
init_cms(app, ..., admin_prefix="admin/content")
```

The admin `APIRouter` is registered **before** the catch-all content router, so more-specific admin routes take priority.

## Endpoints

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

## Request Format

All create/update requests use JSON with two fields:

```python
{
    "frontmatter": dict,   # YAML frontmatter keys (optional, defaults to {})
    "body": str            # Markdown body content (optional, defaults to "")
}
```

The server serializes these into a valid Markdown file with YAML frontmatter. Lists, booleans, numbers, and block scalars are formatted correctly.

## Error Responses

| Status | Meaning | Example |
|--------|---------|---------|
| `400` | Path is the wrong type (e.g. file instead of dir) | `"Path is a directory, not a file"` |
| `404` | File or directory does not exist | `"File not found"` |
| `409` | Resource already exists | `"File already exists"` |
| `422` | Request body failed validation | Pydantic validation error |
| `500` | Internal error (e.g. file parse failure) | `"Failed to parse file: ..."` |

## Path Traversal Protection

All paths are resolved against the content root using strict `pathlib` checks. Attempts to escape the content directory (`../../etc/passwd`) are blocked before the route handler runs.

## Atomic Writes

Files are written atomically via a temp-file + `os.replace()` pattern. If a write fails mid-stream, the original file is not corrupted — the temp file is cleaned up automatically.

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
