# Image Processing

moosey-cms provides automatic image resizing, responsive `srcset`, face detection, and CDN support.

## Requirements

Install the `images` extra:

```bash
pip install moosey-cms[images]
```

This installs Pillow (required) and OpenCV (optional — needed only for face detection).

### Face Detection

For `focus=face` support, you need OpenCV:

```bash
pip install opencv-python-headless>=4.9,<5
```

Or install everything at once:

```bash
pip install moosey-cms[all]
```

## Basic Usage

The `image` filter is the primary API. It returns a single processed image URL:

```jinja2
<img src="{{ '/photos/photo.jpg' | image(width=800) }}" alt="Photo">
```

This resizes `photo.jpg` to 800px wide and returns the URL to the processed image.

### Path Conventions

Image paths are relative to your static directory and follow the same convention as other content paths. The image server route defaults to `/__moosey/img/`.

### Deprecation Notice

`image_url` and `responsive_image` are deprecated. Use `image` instead:

| Old | New |
|-----|-----|
| `image_url(path, w=800)` | `image(path, width=800)` |
| `responsive_image(path, widths=[400,800])` | `image(path, widths=[400,800], alt="...")` |

The old filters still work but emit a `DeprecationWarning`.

## Responsive Images (srcset)

Pass a list of widths to generate a full `<img>` tag with `srcset`:

```jinja2
{{ '/photos/photo.jpg' | image(widths=[400, 800, 1200], alt="Mountain view") }}
```

Output:

```html
<img
  src="/__moosey/img/photos/photo.jpg?w=800"
  srcset="/__moosey/img/photos/photo.jpg?w=400 400w,
          /__moosey/img/photos/photo.jpg?w=800 800w,
          /__moosey/img/photos/photo.jpg?w=1200 1200w"
  alt="Mountain view"
>
```

The middle width becomes the default `src` and `sizes="100vw"` is included automatically. Override `sizes`:

```jinja2
{{ photo | image(widths=[400, 800, 1200], sizes="(max-width: 768px) 100vw, 800px", alt="Photo") }}
```

## Parameters

All parameters are optional.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | int | — | Target width in pixels |
| `height` | int | — | Target height in pixels |
| `quality` | int | `85` | JPEG/WebP quality (1-100) |
| `format` | str | — | Force output format (`webp`, `jpeg`, `png`) |
| `focus` | str | — | Crop focus: `face`, `center`, `top`, `bottom`, `left`, `right` |
| `widths` | list[int] | — | Enable responsive srcset with these widths |
| `alt` | str | — | Alt text (used with `widths`) |
| `sizes` | str | `100vw` | Sizes attribute (used with `widths`) |
| `lazy` | bool | `true` | Add `loading="lazy"` (used with `widths`) |

### Examples

Resize to exact dimensions:

```jinja2
{{ photo | image(width=400, height=300) }}
```

Convert to WebP:

```jinja2
{{ photo | image(width=800, format="webp") }}
```

Lower quality for thumbnails:

```jinja2
{{ photo | image(width=200, quality=60) }}
```

### Focus / Crop Modes

Control how the image is cropped when both `width` and `height` are specified:

| Focus | Behavior |
|-------|----------|
| `center` | Crop from center (default) |
| `face` | Detect and center on face (requires OpenCV) |
| `top` | Keep top of image |
| `bottom` | Keep bottom |
| `left` | Keep left side |
| `right` | Keep right side |

```jinja2
{{ photo | image(width=400, height=300, focus="face") }}
```

Face detection uses OpenCV's Haar Cascade classifier. The image is centered on the detected face before cropping.

## CDN Support

Configure an image CDN in `pyproject.toml`:

```toml
[tool.moosey-cms]
dirs.static = "static"

[tool.moosey-cms.img_cdn]
base_url = "https://images.example.com"
```

Then use `image_cdn` to transform URLs through the CDN:

```jinja2
{{ '/photos/photo.jpg' | image_cdn(width=400) }}
```

CDN behavior depends on your provider. The filter appends `?w=400` (and other params) to the CDN URL.

### CDN Parameters

| Param | Description |
|-------|-------------|
| `width` | Image width |
| `height` | Image height |
| `quality` | Compression quality |
| `format` | Output format |

## Caching

Processed images are cached to avoid re-processing on every build. The cache location depends on your configuration:

- Default: cached in memory for the duration of `moosey serve`
- Build: written to `_site/__moosey/img/` alongside output

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Image returns original unchanged | `images` extra not installed | `pip install moosey-cms[images]` |
| `focus=face` has no effect | OpenCV not installed | `pip install opencv-python-headless>=4.9,<5` |
| Image not found (404) | Path prefix mismatch | Ensure path is relative to static dir, no `/static/` prefix |
| DeprecationWarning in logs | Using `image_url` or `responsive_image` | Switch to `image` filter |
| Poor quality output | Quality too low | Increase `quality` parameter (default 85) |
| Wrong crop area | Focus mode not set | Specify `focus` param for explicit control |

### Path Debugging

Images are served from `/__moosey/img/{path}`. Check the resolved URL in your page source — if you see `/static/photo.jpg` instead of `/__moosey/img/photo.jpg`, the image filter isn't being applied (likely missing the `images` extra).
