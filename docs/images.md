# Image Processing

moosey-cms provides automatic image resizing, responsive `srcset`, face detection, and CDN support via a URL-driven pipeline.

## Requirements

Install the `images` extra:

```bash
pip install moosey-cms[images]
```

This installs Pillow (required).

### Face Detection

For `focus=face` support, install OpenCV:

```bash
pip install moosey-cms[faces]
```

Or install everything at once:

```bash
pip install moosey-cms[all]
```

## Setup

Pass a `static` directory to `init_cms` to enable the image pipeline:

```python
init_cms(
    app,
    ...,
    dirs={
        "static": BASE_DIR / "static",
        ...
    },
)
```

The pipeline serves derivatives at `/__moosey/img/{path}`.

## Basic Usage

The `image` filter is the primary API. It returns a processed image URL:

```jinja2
<img src="{{ '/photos/photo.jpg' | image(w=800) }}" alt="Photo">
```

This resizes `photo.jpg` to 800px wide and returns the URL.

### Responsive Images (srcset)

Pass a list of widths to generate a full `<img>` tag with `srcset`:

```jinja2
{{ '/photos/photo.jpg' | image(widths=[400, 800, 1200], alt="Mountain view") }}
```

Output:

```html
<img src="/__moosey/img/photos/photo.jpg?w=800"
     srcset="/__moosey/img/photos/photo.jpg?w=400 400w,
             /__moosey/img/photos/photo.jpg?w=800 800w,
             /__moosey/img/photos/photo.jpg?w=1200 1200w"
     sizes="100vw" loading="lazy" decoding="async">
```

Override `sizes`:

```jinja2
{{ photo | image(widths=[400, 800, 1200], sizes="(max-width: 768px) 100vw, 800px", alt="Photo") }}
```

## Parameters

All parameters are optional.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `w` | int | — | Target width in pixels |
| `h` | int | — | Target height in pixels |
| `ar` | str | `auto` | Aspect ratio: `1x1`, `16x9`, `4x3`, `3x2`, `21x9`, `square`, `wide`, `portrait`, `landscape` |
| `fit` | str | `cover` | `cover`, `contain`, `fill`, `crop`, `scale-down` |
| `focus` | str | `auto` | `center`, `top`, `bottom`, `left`, `right`, `top-left`, `top-right`, `bottom-left`, `bottom-right`, `face`, `point,X,Y` |
| `fmt` | str | `auto` | Output format: `webp`, `avif`, `jpg`, `png` (auto negotiates WebP/AVIF) |
| `q` | int | `82` (webp) / `90` (jpg) | Quality 1–100 |
| `blur` | int | — | Gaussian blur radius 0–100 |
| `sharpen` | int | — | Unsharp mask percent 0–100 |
| `grayscale` | bool | — | Convert to monochrome |
| `brightness` | int | — | Adjust ±100% |
| `contrast` | int | — | Adjust ±100% |
| `saturation` | int | — | Adjust ±100% |
| `dpr` | float | — | Device pixel ratio (0.25–3) |
| `resize` | float | — | Scale ratio (0.01–1) |
| `bg` | str | `#ffffff` | Background color for transparent→opaque conversion |

### Focus / Crop Modes

| Focus | Behavior |
|-------|----------|
| `auto` | Entropy-based saliency detection (default) |
| `center` | Crop from center |
| `face` | Detect and center on face (requires OpenCV) |
| `top` / `bottom` / `left` / `right` | Edge-aligned crop |
| `point,X,Y` | Crop centered at percentage point (0–100) |

```jinja2
{{ photo | image(w=400, h=300, focus="face") }}
```

## CDN Support

Use the `image_cdn_ctx` filter (registered as `image_cdn` in templates) to rewrite image URLs through a CDN:

```python
site_data = {
    "image_cdn": {
        "provider": "cloudflare",   # cloudflare, cloudinary, imgix, imagekit
        "base_url": "https://images.example.com",
    },
}
```

```jinja2
{{ '/photos/photo.jpg' | image_cdn(w=400, q=80) }}
```

Supported providers: Cloudflare (`/cdn-cgi/image/...`), Cloudinary (`/image/upload/...`), imgix (query string), ImageKit (`tr:...`).

## Caching

Processed images are cached on disk in a `.moosey/` subfolder next to the source file, named `<stem>__moosey_<params>.<ext>`. The cache is invalidated automatically by the file watcher when the source changes.

## Deprecation Notice

`image_url` and `responsive_image` are deprecated. Use `image` instead:

| Old | New |
|-----|-----|
| `image_url(path, w=800)` | `image(path, w=800)` |
| `responsive_image(path, widths=[400,800])` | `image(path, widths=[400,800])` |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Image returns original unchanged | `images` extra not installed | `pip install moosey-cms[images]` |
| `focus=face` has no effect | OpenCV not installed | `pip install opencv-python-headless>=4.9,<5` |
| Image not found (404) | Path prefix mismatch | Path is relative to static dir, omit `/static/` prefix |
| DeprecationWarning in logs | Using `image_url` or `responsive_image` | Switch to `image` filter |
| Wrong crop area | Focus mode not set | Specify `focus` param |
| Poor quality output | Quality too low | Increase `q` parameter |
