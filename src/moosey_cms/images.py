from __future__ import annotations

"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

"""
Moosey CMS image pipeline.

URL-driven, hit-once, file-watcher-invalidated image processing.

- Source files live under the user's configured static mount (``dirs["static"]``).
- Derivatives are written into a hidden ``.moosey/`` subfolder alongside the
  source, named ``<stem>__moosey_<params>.<ext>``.
- A FastAPI route ``GET /__moosey/img/{path}`` serves existing derivatives or
  generates them on first hit. Subsequent requests are pure static ``FileResponse``.
- The file watcher hook (registered from :mod:`moosey_cms.main`) deletes a
  derivative set when its source changes.
- Pillow is an optional dep (``moosey-cms[images]``). Without it, the route
  returns 503 and serving filters degrade gracefully to the original URL.
- Face detection is an opt-in extra (``moosey-cms[faces]`` or ``[all]``) using
  ``opencv-python-headless``. Without it, ``focus=face`` serves the original.
"""

import asyncio
import logging
import os
import re
import warnings
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from fastapi import Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, Response
import json
from .lib.crypto import encode, decode
from .lib.cache import cache

log = logging.getLogger("moosey_cms.images")

MAX_DIM = 4000
CACHE_DIR = ".moosey"

IMAGES_AVAILABLE = find_spec("PIL") is not None
FACES_AVAILABLE = IMAGES_AVAILABLE and find_spec("cv2") is not None


def _can_transform(params: Dict[str, Any]) -> bool:
    """Return whether the installed optional dependencies support this request."""
    if not IMAGES_AVAILABLE:
        return False
    return params.get("focus") != "face" or FACES_AVAILABLE


# Aspect-ratio presets. ``auto`` keeps the source ratio. Both colon (`1:1`)
# and x (`1x1`) notations are accepted; the canonical form stored in params
# uses `x` to keep URL and filename consistent and cross-platform safe.
ASPECT_PRESETS: Dict[str, Optional[Tuple[int, int]]] = {
    "1:1": (1, 1),
    "1x1": (1, 1),
    "square": (1, 1),
    "16:9": (16, 9),
    "16x9": (16, 9),
    "wide": (21, 9),
    "4:3": (4, 3),
    "4x3": (4, 3),
    "3:2": (3, 2),
    "3x2": (3, 2),
    "portrait": (3, 4),
    "landscape": (4, 3),
    "21:9": (21, 9),
    "21x9": (21, 9),
    "auto": None,
}

_FIT_OPTIONS = {"cover", "contain", "fill", "crop", "scale-down"}
_FOCUS_OPTIONS = {
    "auto",
    "center",
    "top",
    "bottom",
    "left",
    "right",
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
    "face",
}
_FMT_OPTIONS = {"webp", "avif", "jpg", "png", "jpeg", "auto"}
_META_OPTIONS = {"none", "all", "copyright"}
_RESIZE_OPTIONS = {"lanczos", "bilinear", "nearest", "hamming"}
_DEFAULT_QUALITY = {"webp": 82, "jpg": 90, "jpeg": 90, "png": 100, "avif": 60}

# Aliases (canonical name on the left, accepted variants on the right).
_ALIASES = {
    "w": ("width",),
    "h": ("height",),
    "q": ("quality",),
    "fmt": ("format",),
    "grayscale": ("mono",),
}

_KNOWN_PARAMS = {
    "ar",
    "fit",
    "focus",
    "fmt",
    "q",
    "bg",
    "blur",
    "sharpen",
    "grayscale",
    "brightness",
    "contrast",
    "saturation",
    "dpr",
    "meta",
    "watermark",
    "resize",
    "w",
    "h",
}

_FACE_WARNED = False
_FACE_DETECTOR = None  # cached cv2 CascadeClassifier


# ---------------------------------------------------------------------------
# Param parsing & filename building
# ---------------------------------------------------------------------------


class ImageError(ValueError):
    """Raised for invalid URL params or unsupported operations."""


def _coerce_int(value: Any, name: str, lo: int, hi: int) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ImageError(f"{name} must be an integer")
    if v < lo or v > hi:
        raise ImageError(f"{name} must be between {lo} and {hi}")
    return v


def _clamp_pct(value: Any, name: str) -> Optional[int]:
    return _coerce_int(value, name, -100, 100)


def parse_params(qs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and canonicalize image route query params.

    Rejects unknown keys (raises :class:`ImageError`). Returns a deterministic
    dict suitable for both derivative naming and image generation.
    """
    # Apply aliases first.
    canon: Dict[str, Any] = {}
    for k, v in qs.items():
        target = k
        for canonical, alts in _ALIASES.items():
            if k in alts:
                target = canonical
                break
        canon[target] = v

    # Reject unknown keys.
    unknown = set(canon) - _KNOWN_PARAMS
    if unknown:
        raise ImageError(f"unknown image params: {sorted(unknown)}")

    out: Dict[str, Any] = {}

    # Dimensions
    w = _coerce_int(canon.get("w"), "w", 1, MAX_DIM)
    h = _coerce_int(canon.get("h"), "h", 1, MAX_DIM)
    if w is not None:
        out["w"] = w
    if h is not None:
        out["h"] = h

    # Aspect ratio
    ar = str(canon.get("ar", "auto")).lower()
    # Normalize colon to x so URL and filename are consistent: 1:1 → 1x1
    ar = ar.replace(":", "x")
    if ar not in ASPECT_PRESETS:
        raise ImageError(f"ar must be one of {sorted(ASPECT_PRESETS)}")
    out["ar"] = ar

    # Fit
    fit = str(canon.get("fit", "cover")).lower()
    if fit not in _FIT_OPTIONS:
        raise ImageError(f"fit must be one of {sorted(_FIT_OPTIONS)}")
    out["fit"] = fit

    # Focus (allow point,X,Y)
    focus = canon.get("focus", "auto")
    focus_s = str(focus).lower()
    if focus_s.startswith("point,"):
        try:
            _, px, py = focus_s.split(",")
            px_i, py_i = int(px), int(py)
            if not (0 <= px_i <= 100 and 0 <= py_i <= 100):
                raise ValueError
            out["focus"] = f"point-{px_i}-{py_i}"
        except (ValueError, AttributeError):
            raise ImageError("focus=point,X,Y requires X,Y in 0..100")
    elif focus_s in _FOCUS_OPTIONS:
        out["focus"] = focus_s
    else:
        raise ImageError(f"focus must be one of {sorted(_FOCUS_OPTIONS)} or point,X,Y")

    # Format / quality / meta
    fmt = str(canon.get("fmt", "auto")).lower()
    if fmt not in _FMT_OPTIONS:
        raise ImageError(f"fmt must be one of {sorted(_FMT_OPTIONS)}")
    out["fmt"] = fmt

    q = _coerce_int(canon.get("q"), "q", 1, 100)
    if q is not None:
        out["q"] = q

    meta = str(canon.get("meta", "none")).lower()
    if meta not in _META_OPTIONS:
        raise ImageError(f"meta must be one of {sorted(_META_OPTIONS)}")
    out["meta"] = meta

    # Adjustments
    for k in ("blur", "sharpen"):
        v = _coerce_int(canon.get(k), k, 0, 100)
        if v:
            out[k] = v
    for k in ("brightness", "contrast", "saturation"):
        v = _clamp_pct(canon.get(k), k)
        if v:
            out[k] = v

    # Boolean toggles
    if str(canon.get("grayscale", "")).lower() in ("1", "true", "yes", "on"):
        out["grayscale"] = True

    # Floats
    dpr_raw = canon.get("dpr")
    if dpr_raw is not None and dpr_raw != "":
        try:
            dpr = float(dpr_raw)
        except (TypeError, ValueError):
            raise ImageError("dpr must be a float")
        if not (0.25 <= dpr <= 3):
            raise ImageError("dpr must be between 0.25 and 3")
        out["dpr"] = dpr

    resize_raw = canon.get("resize")
    if resize_raw is not None and resize_raw != "":
        scale = float(resize_raw)
        if not (0.01 <= scale <= 1):
            raise ImageError("resize must be between 0.01 and 1")
        out["resize"] = scale

    # String options
    bg = canon.get("bg")
    if bg:
        out["bg"] = str(bg)

    watermark = canon.get("watermark")
    if watermark:
        out["watermark"] = str(watermark)

    resize_filter = (
        str(canon.get("resize") or "").lower() if False else None
    )  # placeholder
    rf = str(canon.get("rf", "") or canon.get("resize", "") or "").lower()
    # Note: `resize` above is interpreted as a scale ratio. If it's a known
    # filter name, treat it as the resample filter instead. We resolve the
    # ambiguity by attempting float first; if that fails and it's a known
    # resample we fall back here. For clarity we expose `rf` for resample
    # filter and `resize` for scale ratio, but accept `resize=lanczos` as
    # a nicety when no scale was provided.
    if "resize" not in out and rf in _RESIZE_OPTIONS:
        out["rf"] = rf
    elif rf in _RESIZE_OPTIONS and "resize" in out:
        # Both could be supplied; treat `rf` as the filter if present.
        out["rf"] = rf

    return dict(sorted(out.items()))


def _sanitize_value(v: Any) -> str:
    s = str(v).lower()
    # Collapse non-path-safe chars to hyphens, except booleans.
    if isinstance(v, bool):
        return "1" if v else ""
    s = re.sub(r"[^a-z0-9._-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def derive_name(stem: str, params: Dict[str, Any], fmt: str) -> str:
    """Build a deterministic derivative filename.

    Format: ``<stem>__moosey_<k1>-<v1>_<k2>-<v2>.<fmt>``
    Keys are lowercase, sorted. Booleans emit ``<k>`` only when True.
    """
    parts = []
    for k in sorted(params):
        v = params[k]
        if v is None or v == "" or v is False:
            continue
        if v is True:
            parts.append(k)
        else:
            parts.append(f"{k}-{_sanitize_value(v)}")
    body = "_".join(parts)
    suffix = f".{fmt.lstrip('.')}"
    if body:
        return f"{stem}__moosey_{body}{suffix}"
    return f"{stem}__moosey{suffix}"


def derive_path(source: Path, params: Dict[str, Any]) -> Path:
    fmt = params.get("fmt", "auto")
    if fmt == "auto":
        fmt = "webp"  # default; route sets this per Accept header
    name = derive_name(source.stem, params, fmt)
    return source.parent / CACHE_DIR / name


# ---------------------------------------------------------------------------
# Generation (Pillow)
# ---------------------------------------------------------------------------

_GEN_LOCKS: Dict[str, asyncio.Lock] = {}


def _get_lock(key: str) -> asyncio.Lock:
    return _GEN_LOCKS.setdefault(key, asyncio.Lock())


def _apply_aspect(
    img, target_ar: Optional[Tuple[int, int]], fit: str, focus: str
) -> "Image":
    """Crop/resize ``img`` to ``target_ar`` honoring fit & focus."""
    # Lazy PIL
    from PIL import Image  # type: ignore

    if target_ar is None:
        return img
    src_w, src_h = img.size
    tw, th = target_ar
    target_ratio = tw / th
    src_ratio = src_w / src_h

    if fit == "scale-down" and src_ratio == target_ratio:
        return img

    if fit in ("contain", "scale-down"):
        # Resize to fit inside the box, keeping AR. Pad if needed.
        if src_ratio > target_ratio:
            new_w = src_w
            new_h = int(src_w / target_ratio)
        else:
            new_h = src_h
            new_w = int(src_h * target_ratio)
        if fit == "scale-down":
            new_w, new_h = min(src_w, new_w), min(src_h, new_h)
        canvas = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
        resized = img.resize(
            (min(new_w, src_w), min(new_h, src_h)),
            Image.Resampling.LANCZOS,
        )
        canvas.paste(
            resized, ((new_w - resized.width) // 2, (new_h - resized.height) // 2)
        )
        return canvas

    # cover / fill / crop - same AR box crop semantics
    if src_ratio > target_ratio:
        crop_h = src_h
        crop_w = int(src_h * target_ratio)
    else:
        crop_w = src_w
        crop_h = int(src_w / target_ratio)

    focus_box = None

    # When focus=face, aim at a padded head/shoulders box rather than the raw
    # Haar face rectangle; the raw rectangle excludes hair and chin.
    if focus == "face":
        box = face_box_path(img)
        if box is not None:
            focus_box = _expand_face_box(box, src_w, src_h)
            bx, by, bw, bh = box
            need_w = max(crop_w, bw)
            need_h = max(crop_h, bh)
            if need_w > crop_w or need_h > crop_h:
                if need_w / need_h > target_ratio:
                    crop_w = min(need_w, src_w)
                    crop_h = min(int(crop_w / target_ratio), src_h)
                else:
                    crop_h = min(need_h, src_h)
                    crop_w = min(int(crop_h * target_ratio), src_w)
                crop_w = min(crop_w, src_w)
                crop_h = min(crop_h, src_h)

    if focus_box is not None:
        left, top = _shift_to_box(focus_box, src_w, src_h, crop_w, crop_h)
    else:
        left, top = _focus_offset(src_w, src_h, crop_w, crop_h, focus, img)
    return img.crop((left, top, left + crop_w, top + crop_h))


def _focus_offset(
    src_w: int, src_h: int, crop_w: int, crop_h: int, focus: str, img
) -> Tuple[int, int]:
    """Compute crop top-left for the given focus keyword."""
    focus = focus or "auto"
    if focus == "auto":
        box = saliency_box(img, crop_w / crop_h)
        if box is not None:
            return box[0], box[1]
        focus = "center"

    if focus == "face":
        box = face_box_path(img)  # uses underlying path via img.filename
        if box is not None:
            return _shift_to_box(
                _expand_face_box(box, src_w, src_h),
                src_w,
                src_h,
                crop_w,
                crop_h,
            )
        # No trustworthy face found - for portraits keep the top (heads are
        # often near the top of headshots); for landscapes fall back to center.
        focus = "top" if src_h > src_w else "center"

    if focus.startswith("point-"):
        try:
            _, px, py = focus.split("-")
            return int(int(px) / 100 * (src_w - crop_w)), int(
                int(py) / 100 * (src_h - crop_h)
            )
        except Exception:
            pass

    presets = {
        "center": ((src_w - crop_w) // 2, (src_h - crop_h) // 2),
        "top": ((src_w - crop_w) // 2, 0),
        "bottom": ((src_w - crop_w) // 2, src_h - crop_h),
        "left": (0, (src_h - crop_h) // 2),
        "right": (src_w - crop_w, (src_h - crop_h) // 2),
        "top-left": (0, 0),
        "top-right": (src_w - crop_w, 0),
        "bottom-left": (0, src_h - crop_h),
        "bottom-right": (src_w - crop_w, src_h - crop_h),
    }
    return presets.get(focus, presets["center"])


def _expand_face_box(box, src_w, src_h) -> Tuple[int, int, int, int]:
    """Return a padded face box that includes hair/headroom and some shoulders."""
    bx, by, bw, bh = box
    pad_x = int(bw * 0.45)
    pad_top = int(bh * 0.75)
    pad_bottom = int(bh * 0.90)

    left = max(0, bx - pad_x)
    top = max(0, by - pad_top)
    right = min(src_w, bx + bw + pad_x)
    bottom = min(src_h, by + bh + pad_bottom)

    return left, top, max(1, right - left), max(1, bottom - top)


def _plausible_face_box(box, src_w: int, src_h: int) -> bool:
    """Reject tiny false positives that are unlikely to be the subject face."""
    if box is None:
        return False
    _bx, _by, bw, bh = box
    short_side = max(1, min(src_w, src_h))
    min_face = max(30, int(short_side * 0.08))
    return bw >= min_face and bh >= min_face


def _shift_to_box(box, src_w, src_h, crop_w, crop_h) -> Tuple[int, int]:
    """Center the crop on the bounding box, then shift so the full box fits."""
    bx, by, bw, bh = box
    cx = bx + bw // 2
    cy = by + bh // 2
    left = max(0, min(cx - crop_w // 2, src_w - crop_w))
    top = max(0, min(cy - crop_h // 2, src_h - crop_h))
    # Shift to ensure the entire bounding box is within the crop window.
    if bx + bw > left + crop_w:
        left = min(bx + bw - crop_w, src_w - crop_w)
    if bx < left:
        left = max(bx, 0)
    if by + bh > top + crop_h:
        top = min(by + bh - crop_h, src_h - crop_h)
    if by < top:
        top = max(by, 0)
    return left, top


def saliency_box(img, target_ar: float) -> Optional[Tuple[int, int, int, int]]:
    """Pure-Pillow entropy/saliency heuristic. Returns (left, top, w, h)."""
    try:
        from PIL import Image, ImageFilter  # type: ignore
    except ImportError:
        return None
    src_w, src_h = img.size
    small = img.copy()
    small.thumbnail((200, 200))
    sw, sh = small.size

    # Compute edge density map (Laplacian proxy via simple filters).
    gray = small.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    import math

    cell = max(8, sw // 10)
    max_score = -1.0
    best = (0, 0)

    target_ratio = target_ar
    grid_w = sw
    grid_h = sh
    cw = min(grid_w, int(grid_h * target_ratio))
    ch = int(cw / target_ratio)
    if ch > grid_h:
        ch = grid_h
        cw = int(ch * target_ratio)

    px = edges.load()
    for gy in range(0, grid_h - ch + 1, max(1, cell // 2)):
        for gx in range(0, grid_w - cw + 1, max(1, cell // 2)):
            score = 0.0
            for y in range(gy, gy + ch, 4):
                for x in range(gx, gx + cw, 4):
                    score += px[x, y]
            if score > max_score:
                max_score = score
                best = (gx, gy)

    # Scale back up to source coordinates.
    sx = src_w / sw
    sy = src_h / sh
    left = int(best[0] * sx)
    top = int(best[1] * sy)
    return left, top, int(cw * sx), int(ch * sy)


def _get_face_detector():
    """Lazily import opencv and build a Haar cascade. None if unavailable."""
    global _FACE_WARNED, _FACE_DETECTOR
    if _FACE_DETECTOR is not None:
        return _FACE_DETECTOR
    try:
        import cv2  # type: ignore
        from cv2.data import haarcascades  # type: ignore

        path = os.path.join(haarcascades, "haarcascade_frontalface_default.xml")
        _FACE_DETECTOR = cv2.CascadeClassifier(path)
        if _FACE_DETECTOR.empty():
            _FACE_DETECTOR = None
    except ImportError:
        pass
    if _FACE_DETECTOR is None and not _FACE_WARNED:
        msg = (
            "focus=face: face detection unavailable because "
            "opencv-python-headless is not installed. Image crops will use "
            "top-focus (portrait) or center-focus (landscape) as a fallback.\n"
            "  Install the missing dependency with:\n"
            "    pip install moosey-cms[faces]\n"
            "    # or with uv:\n"
            "    uv add moosey-cms[faces]\n"
        )
        log.warning(msg)
        warnings.warn(msg)
        _FACE_WARNED = True
    return _FACE_DETECTOR


def face_box_path(img) -> Optional[Tuple[int, int, int, int]]:
    """Detect a face in image. Returns (x, y, w, h) or None."""
    detector = _get_face_detector()
    if detector is None:
        return None
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        arr = np.array(img.convert("RGB"))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        short_side = max(1, min(img.size))
        min_face = max(30, int(short_side * 0.08))
        faces = detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_face, min_face)
        )
        if len(faces):
            # Pick the largest detected face.
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            box = int(x), int(y), int(w), int(h)
            if _plausible_face_box(box, img.width, img.height):
                return box
    except Exception as exc:
        log.debug("face detection failed: %s", exc)
    return None


def _apply_ops(img, params: Dict[str, Any]):
    """Apply blur, sharpen, grayscale, brightness, contrast, saturation."""
    try:
        from PIL import Image, ImageEnhance, ImageFilter  # type: ignore
    except ImportError:
        return img

    blur = params.get("blur")
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur / 10))
    sharpen = params.get("sharpen")
    if sharpen:
        img = img.filter(
            ImageFilter.UnsharpMask(radius=2, percent=int(sharpen), threshold=3)
        )
    if params.get("grayscale"):
        img = img.convert("L").convert("RGB")
    for k, enhancer in (
        ("brightness", ImageEnhance.Brightness),
        ("contrast", ImageEnhance.Contrast),
        ("saturation", ImageEnhance.Color),
    ):
        v = params.get(k)
        if v:
            img = enhancer(img).enhance(1 + v / 100)
    return img


def _flatten(img, bg: str):
    """Flatten RGBA onto bg color for opaque formats."""
    if img.mode in ("RGBA", "LA", "P"):
        try:
            from PIL import Image  # type: ignore
        except ImportError:
            return img
        bg_color = "#ffffff"
        if bg:
            bg_color = bg if bg.startswith("#") else f"#{bg.lstrip('#')}"
        canvas = Image.new("RGB", img.size, bg_color)
        canvas.paste(img, mask=img.split()[-1] if "A" in img.getbands() else None)
        return canvas
    return img


def _save(img, target: Path, fmt: str, quality: int, meta: str):
    """Persist image with format + quality + meta policy."""
    from PIL import Image  # type: ignore

    save_kwargs: Dict[str, Any] = {}
    if fmt in ("jpg", "jpeg"):
        img = _flatten(img, "#ffffff")
        save_format = "JPEG"
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
        save_kwargs["progressive"] = True
    elif fmt == "png":
        save_format = "PNG"
        save_kwargs["optimize"] = True
    elif fmt == "avif":
        save_format = "AVIF"
        save_kwargs["quality"] = quality
    else:  # webp
        save_format = "WEBP"
        save_kwargs["quality"] = quality
        save_kwargs["method"] = 4

    if meta != "all":
        save_kwargs["exif"] = b""
        save_kwargs["icc_profile"] = None
    # copyright-only policy: strip everything except orientation/copyright exif.
    # Pillow doesn't make this granular; for now meta=copyright maps to none.

    target.parent.mkdir(parents=True, exist_ok=True)
    img.save(target, format=save_format, **save_kwargs)


def generate(source: Path, target: Path, params: Dict[str, Any]) -> None:
    """Synchronously generate ``target`` from ``source`` per ``params``.

    Pillow is required; raises ``ImageError`` if Pillow is missing.
    """

    try:
        from PIL import Image  # type: ignore
    except ImportError as exc:
        raise ImageError("Pillow is required for image generation") from exc

    fmt = params.get("fmt", "auto")
    if fmt == "auto":
        fmt = "webp"
    if fmt == "jpeg":
        fmt = "jpg"

    quality = params.get("q") or _DEFAULT_QUALITY.get(fmt, 82)

    with Image.open(source) as img:
        img.load()
        # Apply dpr multiplier to w/h before forcing AR.
        dpr = params.get("dpr", 1)
        w = int(params.get("w", 0) * dpr) if params.get("w") else 0
        h = int(params.get("h", 0) * dpr) if params.get("h") else 0


        # Resize scale ratio (alternative to w/h).
        ratio = params.get("resize")
        if ratio and not w and not h:
            w = int(img.width * ratio)
            h = int(img.height * ratio)

        # Aspect-ratio crop
        ar = params.get("ar", "auto")
        target_ar = ASPECT_PRESETS.get(ar)

        if w and h and ar == "auto":
            target_ar = (w, h)
        if target_ar:
            img = _apply_aspect(
                img, target_ar, params.get("fit", "cover"), params.get("focus", "auto")
            )
            # The AR crop produced the right ratio; now honor either one or
            # both explicit dimensions.
            if w or h:
                new_w = w or int(img.width * h / img.height)
                new_h = h or int(img.height * w / img.width)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        elif w or h:
            # No AR, just scale.
            new_w = w or int(img.width * h / img.height)
            new_h = h or int(img.height * w / img.width)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Image ops (blur, sharpen, brightness, etc.)
        img = _apply_ops(img, params)
        if img.mode == "P":
            img = img.convert("RGBA")

        _save(img, target, fmt, int(quality), params.get("meta", "none"))



# ---------------------------------------------------------------------------
# Invalidation
# ---------------------------------------------------------------------------


def invalidate(source: Path) -> None:
    """Remove derivatives derived from ``source`` by deleting the
    ``.moosey/`` subfolder of its parent directory.

    Coarse but correct; safe to call on non-image paths.
    """
    try:
        cache_dir = source.parent / CACHE_DIR
        if cache_dir.is_dir():
            stem = source.stem
            for entry in cache_dir.iterdir():
                if entry.name.startswith(f"{stem}__moosey"):
                    try:
                        entry.unlink()
                    except OSError:
                        pass
    except Exception as exc:
        log.debug("invalidate failed for %s: %s", source, exc)


# ---------------------------------------------------------------------------
# Route

_MIME_MAP = {
    "webp": "image/webp",
    "avif": "image/avif",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


def _accept_webp(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "image/webp" in accept or "image/avif" in accept





def register_routes(
    app,
    static_dir: Path,
    route_prefix: str = "/__moosey/img",
    max_bytes: int = 50_000_000,
) -> None:
    """Register the image pipeline route on ``app``.

    Parameters
    ----------
    app:
        The FastAPI application.
    static_dir:
        Root directory for source image files.
    route_prefix:
        URL prefix for the image route (default ``"/__moosey/img"``).
        The full route pattern becomes ``{route_prefix}/{{path:path}}``.
    max_bytes:
        Maximum source file size in bytes (default 50 MB).
    """

    @app.get(f"{route_prefix}/{{hash_path:path}}")
    async def _moosey_img(hash_path: str, request: Request, background_tasks: BackgroundTasks) -> Response:

        encoded, fmt = hash_path.split(".")
        target = (static_dir / ".moosey" / hash_path).resolve()

        # Path-traversal check: source must live under static_dir.
        try:
            target.relative_to(static_dir.resolve())
        except ValueError:
            return JSONResponse({"detail": "forbidden"}, status_code=403)

        if target.is_file() :
            # return immediately
            return FileResponse(
                str(target),
                media_type=_MIME_MAP.get(fmt, "application/octet-stream"),
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                },
            )

        # decode
        config = getattr(request.app.state, "config", {})
        crypto_key = config.crypto.key

        try:

            json_str = decode(encoded, key=crypto_key    )
            file_data = json.loads(json_str)

            src = file_data.get("src")

            if not src:
                return JSONResponse({"detail": "not found"}, status_code=404)

            # get original file
            original_file = (static_dir / file_data.get("src").lstrip('/')).resolve()

            if not original_file.is_file():
                return JSONResponse({"detail": "not found"}, status_code=404)

            params = file_data.get("params") or {}
            if not _can_transform(params):
                return FileResponse(
                    str(original_file),
                    headers={"Cache-Control": "public, max-age=31536000, immutable"},
                )

            # run bg process
            background_tasks.add_task(
                _generate_image, source=original_file, target=target, params=params
            )


            # serve
            return FileResponse(
                str(original_file),
                media_type=_MIME_MAP.get(fmt, "application/octet-stream"),
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                },
            )


        except Exception as exc:
            print(exc)
            return JSONResponse({"detail": str(exc)}, status_code=400)




async def _generate_image(source, target,params ):
    if not _can_transform(params):
        return

    from filelock import FileLock, Timeout

    # print(source, target,params)

    try:
        lock = FileLock(target, timeout=20)

        with lock:
            # process
            generate(source, target, params)

    except Timeout:
        print(f"Could not acquire lock within {timeout} seconds")

    except ImageError as exc:
        print(exc)

    

# ---------------------------------------------------------------------------
# Filter-side helpers (used by filters.py)
# ---------------------------------------------------------------------------


# don't run this each time.....
@cache(ttl=3600 * 24 * 30, maxsize=10000)
def image_url_filter(
    src: str, crypto_key=str, _route_prefix: str = "/__moosey/img/", **params
) -> str:
    """Build a ``/__moosey/img/...?…`` URL from a static path + kwargs."""

    clean = src.lstrip("/")
    # Strip leading "static/" if present so paths like "/static/x.jpg" or
    # "static/x.jpg" resolve correctly against static_dir.
    if clean.startswith("static/"):
        clean = clean[len("static/") :]
    prefix = _route_prefix.rstrip("/") + "/"

    if not params:
        return src

    try:
        canon = parse_params(params)
    except ImageError:
        return src

    if not _can_transform(canon):
        return src

    data = dict(src=src, params=params)

    encoded = encode(json.dumps(data),     key=crypto_key    )
    url_path = f"{prefix}{encoded}.{canon.get('fmt', 'jpg')}"

    # print(canon.get('fmt', 'jpg'))
    return url_path


def responsive_image_html(
    src: str,
    widths=(400, 800, 1200, 1600),
    sizes: str = "100vw",
    loading: str = "lazy",
    decoding: str = "async",
    _route_prefix: str = "/__moosey/img/",
    **shared,
) -> str:
    """Render a complete ``<img src=… srcset=… sizes=… loading=… decoding=…>``."""
    srcset_parts = []
    for w in widths:
        url = image_url_filter(src, _route_prefix=_route_prefix, w=w, **shared)
        srcset_parts.append(f"{url} {w}w")
    srcset = ", ".join(srcset_parts)
    src_default = image_url_filter(
        src, _route_prefix=_route_prefix, w=widths[0], **shared
    )
    # Try to find an aspect hint for width/height detection.
    ar = shared.get("ar")
    width_attr = height_attr = ""
    if ar and ar != "auto":
        try:
            ratio_str = str(ar)
            if ":" in ratio_str:
                a, b = ratio_str.split(":", 1)
                ratio = float(a) / float(b)
                width_attr = f' width="{widths[-1]}"'
                height_attr = f' height="{int(widths[-1] / ratio)}"'
        except Exception:
            pass
    return (
        f'<img src="{src_default}" srcset="{srcset}" sizes="{sizes}"'
        f'{width_attr}{height_attr} loading="{loading}"'
        f' decoding="{decoding}">'
    )


def image_dimensions_impl(src: str, static_dir: Optional[Path] = None) -> str:
    """Read local image dimensions via Pillow. Returns ``width="…" height="…"``.
    Empty string if Pillow not installed or file not local/missing."""
    if not src:
        return ""
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return ""
    candidate = None
    if static_dir is not None:
        candidate = (static_dir / src.lstrip("/")).resolve()
    if candidate is None or not candidate.is_file():
        return ""
    try:
        with Image.open(candidate) as img:
            w, h = img.size
        return f' width="{w}" height="{h}"'
    except Exception:
        return ""


def dominant_color_impl(
    src: str, default: str = "#0b172a", static_dir: Optional[Path] = None
) -> str:
    """Return the dominant hex color of the image, or ``default`` on error."""
    if not src:
        return default
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return default
    if static_dir is None:
        return default
    candidate = (static_dir / src.lstrip("/")).resolve()
    if not candidate.is_file():
        return default
    try:
        with Image.open(candidate) as img:
            img = img.convert("RGB").resize((1, 1))
            r, g, b = img.getpixel((0, 0))
            return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return default


# CDN adapters (Tier 3). Provider-specific URL transforms. No file IO.


def image_cdn_impl(
    src: str, *, provider: str = "cloudflare", base_url: Optional[str] = None, **params
) -> str:
    if not base_url:
        return src
    src = src.lstrip("/")
    base = base_url.rstrip("/")

    if provider == "cloudflare":
        # Cloudflare Image Resizing uses /cdn-cgi/image/<options>/<path>
        opts = []
        for k, v in params.items():
            if k in ("w", "width"):
                opts.append(f"width={v}")
            elif k in ("h", "height"):
                opts.append(f"height={v}")
            elif k in ("fmt", "format"):
                opts.append(f"format={v}")
            elif k in ("q", "quality"):
                opts.append(f"quality={v}")
            elif k == "fit":
                opts.append(f"fit={v}")
            elif k == "grayscale":
                opts.append("gravity=auto")
        opts_str = ",".join(opts) if opts else "auto"
        return f"{base}/cdn-cgi/image/{opts_str}/{src}"

    if provider == "cloudinary":
        # cloudinary:/<cloud_name>/image/upload/<transformations>/<path>
        parts = []
        for k, v in params.items():
            kk = {
                "w": "w",
                "h": "h",
                "fmt": "f",
                "q": "q",
                "fit": "c",
                "ar": "ar",
                "dpr": "dpr",
            }.get(k, k)
            if kk == "c":
                v = {"cover": "fill", "contain": "fit", "scale-down": "scale"}.get(v, v)
            if k == "grayscale":
                parts.append("e_grayscale")
            else:
                parts.append(f"{kk}_{v}")
        transform = ",".join(parts) if parts else "f_auto"
        return f"{base}/image/upload/{transform}/{src}"

    if provider == "imgix":
        # imgix: signed-preserving simple query-string. base_url should already
        # include the host prefix.
        from urllib.parse import urlencode as _ue

        d = {}
        for k, v in params.items():
            kk = {"w": "w", "h": "h", "fmt": "fmt", "q": "q"}.get(k, k)
            if k == "fmt":
                v = v
            d[kk] = v
        return f"{base}/{src}?{_ue(d, doseq=True)}"

    if provider == "imagekit":
        # ImageKit tr: prefix. Assume base_url ends with trailing path component.
        tr = []
        for k, v in params.items():
            kk = {"w": "w", "h": "h", "fmt": "f", "q": "q"}.get(k, k)
            tr.append(f"{kk}-{v}")
        tr_str = "tr:" + ",".join(tr) if tr else ""
        return f"{base}/{tr_str}/{src}" if tr_str else f"{base}/{src}"

    return src
