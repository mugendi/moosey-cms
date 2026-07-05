# Images

Moosey CMS has a tiered image pipeline. Source files live under your
configured static mount. Derivatives are written into a `.moosey/` subfolder
alongside each source. Once generated, derivatives are served as static
`FileResponse`s — no CPU on cache hits.

---

## 1. Installation

```bash
uv add moosey-cms           # core (no image processing)
uv add "moosey-cms[all]"    # everything: Pillow + OpenCV face detection
```

Or install selectively:

| Extra | What it adds |
|---|---|
| `[images]` | Pillow — on-disk image processing, `image_dimensions`, `dominant_color` |
| `[faces]` | Pillow + OpenCV — `focus=face` in image crops |
| `[cdn]` | Nothing extra — pure URL rewriting via `image_cdn` filter |
| `[all]` | Everything above |

---

## 2. Enable the on-disk image route

Pass `"static": <path>` in `dirs` to `init_cms`:

```python
init_cms(
    app=app, ...,
    dirs={
        "content": CONTENT_DIR,
        "templates": TEMPLATES_DIR,
        "static": STATIC_DIR,   # enables the image pipeline route
    },
)
```

Without it, the route isn't registered; `image` still emits URLs that 404
harmlessly, and `image_dimensions`/`dominant_color` degrade to empty/default.

### Custom route prefix

By default the image pipeline route is registered at `/__moosey/img/{path:path}`.
You can override the prefix by passing a dict instead of a plain path:

```python
init_cms(
    app=app, ...,
    dirs={
        "content": CONTENT_DIR,
        "templates": TEMPLATES_DIR,
        "static": {
            "dir": STATIC_DIR,
            "route": "/static/dynamic-images",
        },
    },
)
```

The full route becomes `/static/dynamic-images/{path:path}`. The old
`/__moosey/img/{path:path}` prefix is not registered when you use the dict
form — only your custom route serves image derivatives.

---

## 3. The `image` filter

A single filter handles both simple URLs and responsive `<img>` tags. It
automatically picks up the route prefix you configured via `dirs["static"]`.

### Simple (returns a URL)

```jinja
<img src="{{ '/images/hero.jpg' | image(w=800, fmt='webp') }}">
```

### Responsive (returns a full `<img>` tag with srcset)

```jinja
{{ '/images/hero.jpg' | image(
     widths=(400, 800, 1200, 1600),
     sizes="(min-width: 1024px) 33vw, 100vw",
     ar="16:9",
     fmt="webp"
   ) | safe }}
```

Output:

```html
<img src="/__moosey/img/intro.jpg?ar=16:9&...&w=400"
     srcset="/__moosey/img/...&w=400 400w,
             /__moosey/img/...&w=800 800w,
             /__moosey/img/...&w=1200 1200w,
             /__moosey/img/...&w=1600 1600w"
     sizes="(min-width: 1024px) 33vw, 100vw"
     width="1600" height="900"
     loading="lazy"
     decoding="async">
```

`width` and `height` are only added when `ar=` is non-`auto` (so the browser
knows the intrinsic ratio for CLS prevention).

### Face-focused crop

```jinja
{% for member in team %}
  <img src="{{ member.photo | image(ar='square', focus='face', h=200, fmt='webp') }}">
{% endfor %}
```

### Path convention

Omit the `/static/` prefix — the filter resolves paths against your configured
`dirs["static"]` automatically:

```jinja
{# correct #}
{{ '/images/hero.jpg' | image(w=800) }}

{# wrong — double-strips "static/", wastes a prefix #}
{{ '/static/images/hero.jpg' | image(w=800) }}
```

### Deprecated filters

`image_url` and `responsive_image` still work but emit a `DeprecationWarning`.
Migrate to the unified `image` filter:

| Old | New |
|---|---|
| `image_url(src, w=800)` | `image(src, w=800)` |
| `responsive_image(src, widths=(400,800))` | `image(src, widths=(400,800))` |

---

## 4. URL parameter reference

The image route (default `/__moosey/img/{path}`) accepts these query params.
They're also the kwargs that `image(src, **params)` forwards into the URL.

| Param | Type | Values | Default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `w` / `width` | int | 1–4000 | source | Target width. |
| `h` / `height` | int | 1–4000 | source | Target height. |
| `ar` | str | `1:1`, `16:9`, `4:3`, `3:2`, `21:9`, `square`, `portrait`, `landscape`, `wide`, `auto` | `auto` | Output aspect ratio. Absent → keeps source ratio. |
| `fit` | str | `cover`, `contain`, `fill`, `crop`, `scale-down` | `cover` | CSS object-fit semantics. |
| `focus` | str | `auto`, `center`, `top`, `bottom`, `left`, `right`, `top-left`, `top-right`, `bottom-left`, `bottom-right`, `face`, `point,X,Y` | `auto` | Crop anchor. `face` uses OpenCV if installed; falls back to `top`/`center`. |
| `fmt` / `format` | str | `webp`, `avif`, `jpg`/`jpeg`, `png`, `auto` | `auto` | `auto` picks `avif` if supported, else `webp`, else `jpg`. |
| `q` / `quality` | int | 1–100 | varies | Default: webp 82, jpg 90, png 100, avif 60. |
| `bg` | str | hex (`#RRGGBB`) `white` `black` `transparent` | `transparent` | Background for transparent→jpg flattening. |
| `blur` | int | 0–100 | 0 | Gaussian blur radius (÷10). |
| `sharpen` | int | 0–100 | 0 | Unsharp-mask strength. |
| `grayscale` / `mono` | bool | — | false | Grayscale output. |
| `brightness` | int | -100–100 | 0 | Brighten/darken. |
| `contrast` | int | -100–100 | 0 | Contrast adjustment. |
| `saturation` | int | -100–100 | 0 | Saturation (HSV). |
| `dpr` | float | 0.25–3 | 1 | Retina multiplier for srcset widths. |
| `meta` | str | `none`, `all`, `copyright` | `none` | EXIF policy (strip all for privacy). |
| `watermark` | str | path + `|pos|opacity` | — | e.g. `/static/wm.png|bottom-right|0.3`. |
| `resize` | float | 0.01–1 | — | Scale ratio (alternative to w/h). |

Unknown params are rejected with **400** rather than silently ignored.

---

## 5. Filename encoding

```
/static/images/process/.moosey/intro__moosey_ar-1x1_focus-face_h-800_fmt-webp_q-80.webp
└─────────────────────────┘   └──────────────────────────────────────────────────┘
     source parent dir              derivative filename
```

Rules (deterministic, sorted by key):
1. Drop the raw path; use `<stem>` only.
2. Build a sorted list of `[k, v]` pairs from the params (excluding `fmt`, which becomes the extension).
3. Join each pair with `-`, join pairs with `_`, prepend `__moosey_`.
4. Lowercase keys; strip non-`[a-z0-9._-]` from values; percent-encode `point,50,50` → `point-50-50`.
5. Final extension = `fmt` value (or `webp` under `fmt=auto` + browser accept).

Add `**/.moosey/` to your `.gitignore`.

---

## 6. Caching & invalidation

- **Hit:** `FileResponse` the cached derivative.
- **Miss:** Lock on `(source, params)`; generate; if the lock is contended, await and re-check disk.
- **Watcher event on source:** `images.invalidate(source_path)` deletes every derivative whose name starts with `<stem>__moosey`.
- **Manual invalidation:** `from moosey_cms import invalidate; invalidate(Path("/static/x.jpg"))`.
- **Derivatives persist** across template edits and FastAPI restarts.

---

## 7. CDN adapter (`image_cdn` filter)

Pure URL rewriting — no server-side processing, no disk cache, no Pillow dep.

```python
site_data = {
    "image_cdn": {
        "provider": "cloudflare",
        "base_url": "https://im.example.com",
    },
}
```

```jinja
{{ src | image_cdn(w=800, fmt='webp', q=80) }}
```

| Provider | Sample output |
|---|---|
| cloudflare | `https://im.example.com/cdn-cgi/image/width=800,format=webp,quality=80/static/x.jpg` |
| cloudinary | `https://res.cloudinary.com/demo/image/upload/w_800,f_webp,q_80/static/x.jpg` |
| imgix | `https://im.example.com/static/x.jpg?w=800&fmt=webp&q=80` |
| imagekit | `https://im.example.com/tr:w-800,f-webp,q-80/static/x.jpg` |

---

## 8. `image_dimensions` and `dominant_color`

Read-only metadata helpers. They require Pillow (`moosey-cms[images]`) and a
local source. They degrade gracefully to empty strings when Pillow is missing.

```jinja
<img src="{{ src }}" {{ src | image_dimensions | safe }} alt="…">
<div class="card" style="background:{{ src | dominant_color(default='#0b172a') }}">…</div>
```

`dominant_color` returns a 1×1-resized hex color, ideal for low-quality image
placeholders (LQIP).

---

## 9. Face detection (`focus=face`)

```bash
uv add "moosey-cms[faces]"
```

When installed, the Haar Cascade classifier is loaded on first use. The largest
detected face becomes the crop anchor. Multiple faces: the largest wins; smaller
faces bias the crop center toward them.

**Without `[faces]`:** `focus=face` falls back to `top` (portrait) or `center`
(landscape) with a one-time warning (`log.warning` + `warnings.warn`).

The detector is cached on `moosey_cms.images._FACE_DETECTOR`, so subsequent
requests cost ~50–200ms per image.

---

## 10. Saliency / "active zones" (`focus=auto`)

When no focus is specified, Moosey uses **entropy + edge density** heuristics
to find the most visually active region:

1. Downsample to ~200×200.
2. Grayscale + edge filter (FIND_EDGES).
3. Slide a 10×10 grid; score each cell by edge intensity (every 4th pixel).
4. Pick the highest-scoring cell that fits the target aspect ratio.

Pure-Pillow, single-pass — typically <50ms per image.

---

## 11. Security

- **Path traversal:** `pathlib.resolve().relative_to(static_dir)` — returns 403 on traversal.
- **DoS caps:** Source size limit 50MB, max dimension 4000px, max quality 100.
- **Concurrency:** `asyncio.Lock` keyed by target path prevents duplicate generation.
- **No URL signing:** derivatives are public. Wrap behind auth middleware if needed.
- **Watermark paths** are resolved under the static mount and path-protected.

---

## 12. Self-hosting notes

- Mount source images under the same directory as `dirs["static"]`.
- Filter URLs accept paths with or without a leading slash.
- Ship `.moosey/` dirs with your deploy for zero first-request latency.
- `image` filter path convention: omit `/static/` prefix.

---

## 13. Troubleshooting

| Symptom | Fix |
|---|---|
| `image` returns URLs that 404 | Add `"static": STATIC_DIR` to `dirs` in `init_cms` |
| `image_dimensions` returns "" | `uv add "moosey-cms[images]"` |
| `focus=face` warns and falls back | `uv add "moosey-cms[faces]"` |
| Derivative stale after source swap | `from moosey_cms import invalidate; invalidate(Path("/path/to/source.jpg"))` |
| 400 `unknown image params` | Typo in template — check param reference |
| 413 `too large` | Source > 50MB — resize before deploy |
| 500 `generation error` | Source is corrupted — check the file |
