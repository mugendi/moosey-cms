# Image Picker for Admin Editor

**Date:** 2026-07-10  
**Status:** Approved  
**Scope:** Static file API + visual image picker + TUI Editor integration

---

## Problem

The TUI Editor in the admin dashboard has no toolbar button for inserting images. When images are added via TUI's default mechanism, they are base64-encoded inline — bloating markdown files and breaking portability. Users need a way to browse their static directory, upload new images, and insert them as relative markdown paths.

## Goals

1. Add a visual image picker to the admin editor that browses the configured `static.dir`
2. Support uploading new images directly from the picker
3. Support creating subdirectories from the picker (for future file explorer reuse)
4. Insert images as `![alt](/static/path)` — standard markdown, no base64
5. Keep the picker HTML/JS in the user-editable admin template (`editor.html`)

## Non-Goals

- File explorer UI (future work — this API enables it)
- Image editing/cropping in the picker
- CDN URL rewriting at insert time (handled by existing `image_cdn` filter at render time)

---

## Backend: Static File API

### New endpoints (registered on admin router when `dirs["static"]` is configured)

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/{prefix}/static[/subpath]` | List files and directories in the static dir |
| `POST` | `/{prefix}/static/upload/{path:path}` | Upload a file (multipart form data) |
| `POST` | `/{prefix}/static/mkdir/{path:path}` | Create a directory |

### GET `/{prefix}/static[/subpath]`

List contents of the static directory. Returns a mix of files and subdirectories.

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
      "is_image": true,
      "url": "/static/images/photo.jpg"
    },
    {
      "name": "blog",
      "path": "images/blog",
      "type": "directory",
      "size": 0,
      "modified": "2026-07-10T12:00:00",
      "is_image": false,
      "url": null
    }
  ]
}
```

**Image detection:** `is_image` is `true` for extensions: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.avif`, `.bmp`, `.ico`.

**URL construction:** For files with `is_image: true`, the `url` field is `/{static_route}/{path}` where `static_route` comes from the static config (default `/static`). This URL can be used directly in `<img src>` for previews.

**Security:** Uses `get_secure_target()` with `static_dir` as root — prevents path traversal.

### POST `/{prefix}/static/upload/{path:path}`

Upload a file to the static directory. The `path` includes the filename (e.g., `images/photo.jpg`). Parent directories are created automatically.

**Request:** `multipart/form-data` with a `file` field.

**Response:**
```json
{
  "path": "images/photo.jpg",
  "url": "/static/images/photo.jpg",
  "status": "created"
}
```

**Validation:**
- Reject files larger than a configurable limit (default 10MB)
- Reject paths with `..` segments
- Overwrite existing files (PUT-like behavior for uploads)

### POST `/{prefix}/static/mkdir/{path:path}`

Create a directory in the static tree.

**Response:**
```json
{
  "path": "images/blog",
  "status": "created"
}
```

**Validation:**
- 409 if directory already exists
- Reject paths with `..` segments

### Route registration

Routes are registered in `register_admin_routes()` alongside existing content routes. The static dir path and URL route prefix are passed from `init_cms()` via the admin config dict (extended with `_static_dir` and `_static_route` internal keys).

---

## Frontend: Image Picker Modal

### Location

The picker modal HTML and JS live in `editor.html` (the user-editable admin template). Users can customize the picker's appearance and behavior by editing this template.

### Layout

```
┌─────────────────────────────────────────────────┐
│  Image Picker                          [×]      │
├─────────────────────────────────────────────────┤
│  Root > images > blog >                         │
├─────────────────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐              │
│  │ 📁  │ │ 🖼️  │ │ 🖼️  │ │ 🖼️  │              │
│  │sub/ │ │a.jpg│ │b.jpg│ │c.png│              │
│  └─────┘ └─────┘ └─────┘ └─────┘              │
│  ┌─────┐                                       │
│  │ 🖼️  │                                       │
│  │d.webp                                       │
│  └─────┘                                       │
├─────────────────────────────────────────────────┤
│  [Upload] [New Folder]                   [Cancel]│
└─────────────────────────────────────────────────┘
```

### Components

1. **Breadcrumb navigation:** Clickable path segments. Click a segment to navigate back up.

2. **Grid view:** CSS grid of image thumbnails. Each cell shows:
   - For directories: folder icon + name. Click → navigate into it.
   - For images: `<img>` preview using the `url` field + filename below. Click → insert and close.
   - For non-image files: file icon + name (shown but not selectable for image insertion).

3. **Upload button:** Opens a native file input. Selected file → `POST /{prefix}/static/upload/{current_path}` with FormData. On success → refresh grid.

4. **New Folder button:** Prompt for folder name → `POST /{prefix}/static/mkdir/{current_path}/{name}`. On success → refresh grid.

5. **Empty state:** "No images yet. Upload one!" message with an Upload button.

### Behavior

- Modal opens when the toolbar image button is clicked
- Starts at static dir root
- Click image → insert `![filename](url)` at TUI Editor cursor position, close modal
- Click folder → navigate into it
- Click breadcrumb → navigate to that level
- Upload → refresh current view, scroll to new file
- Escape key or × button → close modal without inserting

### Graceful degradation

If `dirs["static"]` is not configured:
- The image toolbar button is hidden
- The editor works normally without image picking
- No JavaScript errors

---

## TUI Editor Integration

### Custom toolbar button

Replace TUI Editor's default image button with a custom one that opens the picker:

```javascript
var imageButton = {
    name: 'image',
    tooltip: 'Insert image',
    command: 'openImagePicker',
    svg: '<svg>...</svg>'  // camera/image icon
};

// Register custom command
tuiEditor.addCommand('openImagePicker', function() {
    openImagePickerModal();
});

tuiEditor.toolbar.addItem(imageButton, 8);  // after link button
```

### Disable base64 insertion

Do NOT register `addImageBlobHook` — this prevents TUI Editor from converting pasted/dropped images to base64. The only way to insert images is through the picker or manual markdown.

### Image insertion

When an image is selected in the picker:
1. Get cursor position from TUI Editor
2. Insert markdown text: `![filename](/static/path/to/image.jpg)`
3. Close the modal

For the fallback textarea editor:
1. Insert markdown text at cursor position
2. Close the modal

---

## Files to modify

| File | Change |
|------|--------|
| `src/moosey_cms/admin.py` | Add static file API endpoints |
| `src/moosey_cms/main.py` | Pass static dir info to admin config |
| `src/moosey_cms/_admin_templates/editor.html` | Add image picker modal, custom toolbar button, picker JS |
| `example/templates/admin/editor.html` | Sync with source |
| `tests/test_admin.py` | Add tests for static file API |
| `docs/admin.md` | Document static file API endpoints |

---

## Testing

1. **Unit tests for static API:**
   - List root directory
   - List subdirectory
   - List with path traversal (should reject)
   - Upload file
   - Upload file to nested path (auto-create dirs)
   - Create directory
   - Create directory that already exists (409)
   - Image detection (`is_image` flag)

2. **Integration tests:**
   - Editor template renders with image picker
   - Image picker modal opens/closes
   - Toolbar button present when static dir configured
   - Toolbar button hidden when no static dir

3. **Manual testing:**
   - Upload an image via picker, verify it appears in grid
   - Navigate into subdirectory
   - Create folder, upload into it
   - Select image, verify markdown inserted correctly
