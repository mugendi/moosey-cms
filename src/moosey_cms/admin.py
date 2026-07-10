"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import mimetypes
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse

from .helpers import get_secure_target, parse_markdown_file


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class FilePayload(BaseModel):
    """Body for creating or updating a content file."""
    frontmatter: Dict[str, Any] = Field(default_factory=dict)
    body: str = Field(default="")


class DirCreateRequest(BaseModel):
    """Body for creating a directory (currently empty, reserved for future use)."""
    pass


class Entry(BaseModel):
    """One item returned by the list endpoint."""
    name: str
    path: str
    type: str  # "file" | "directory"
    size: int = 0
    modified: Optional[str] = None
    title: Optional[str] = None
    is_index: bool = False


class ListResponse(BaseModel):
    """Response for the list endpoint."""
    path: str
    entries: List[Entry]


class FileResponse(BaseModel):
    """Response for the file detail endpoint."""
    path: str
    frontmatter: Dict[str, Any]
    body: str
    size: int = 0
    modified: Optional[str] = None


class StaticEntry(BaseModel):
    """One item returned by the static directory list endpoint."""
    name: str
    path: str
    type: str  # "file" | "directory"
    media_type: str = "other"  # "image" | "pdf" | "video" | "audio" | "other"
    size: int = 0
    modified: Optional[str] = None
    mime_type: Optional[str] = None
    url: Optional[str] = None


class StaticListResponse(BaseModel):
    """Response for the static directory list endpoint."""
    path: str
    entries: List[StaticEntry]


class StaticUploadResponse(BaseModel):
    """Response for the static file upload endpoint."""
    path: str
    url: str
    mime_type: Optional[str] = None
    status: str


class StaticMkdirResponse(BaseModel):
    """Response for the static directory creation endpoint."""
    path: str
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_path(user_path: str, content_dir: Path) -> Path:
    """Resolve *user_path* relative to *content_dir*, blocking traversal."""
    return get_secure_target(user_path, relative_to_path=content_dir)


def _file_entry(file_path: Path, content_dir: Path) -> Entry:
    """Build an :class:`Entry` for a single file or directory."""
    stat = file_path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

    rel = file_path.relative_to(content_dir)
    url_path = str(rel).replace("\\", "/")
    is_dir = file_path.is_dir()
    title = None
    is_index = False

    if is_dir:
        index_file = file_path / "index.md"
        is_index = index_file.exists()
        if is_index:
            try:
                post = frontmatter.load(index_file)
                title = post.metadata.get("title")
            except Exception:
                pass
    elif file_path.suffix == ".md":
        try:
            post = frontmatter.load(file_path)
            title = post.metadata.get("title")
        except Exception:
            pass

    return Entry(
        name=file_path.name,
        path=url_path,
        type="directory" if is_dir else "file",
        size=0 if is_dir else stat.st_size,
        modified=modified,
        title=title,
        is_index=is_index,
    )


IMAGE_EXTS = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".avif", ".bmp", ".ico", ".tiff", ".tif",
})
VIDEO_EXTS = frozenset({".mp4", ".webm", ".ogg", ".mov", ".avi"})
AUDIO_EXTS = frozenset({".mp3", ".wav", ".ogg", ".flac", ".aac"})

def classify_static_type(file_path: Path) -> str:
    """Return the media type label for *file_path* based on its extension."""
    ext = file_path.suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext == ".pdf":
        return "pdf"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    return "other"


def _static_entry(file_path: Path, static_dir: Path, static_route: str) -> StaticEntry:
    """Build a StaticEntry for a file or directory inside the static dir."""
    stat = file_path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
    rel = file_path.relative_to(static_dir)
    url_path = str(rel).replace("\\", "/")
    is_dir = file_path.is_dir()

    media = "other"
    mime_type = None
    url = None
    if not is_dir:
        media = classify_static_type(file_path)
        mime_type, _ = mimetypes.guess_type(file_path.name)
        url = f"{static_route.rstrip('/')}/{url_path}"

    return StaticEntry(
        name=file_path.name,
        path=url_path,
        type="directory" if is_dir else "file",
        media_type=media,
        size=0 if is_dir else stat.st_size,
        modified=modified,
        mime_type=mime_type,
        url=url,
    )


def _atomic_write(file_path: Path, content: str) -> None:
    """Write *content* to *file_path* atomically (temp → rename)."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=file_path.parent, suffix=".tmp", prefix=".moosey-"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, file_path)
    except BaseException:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

def register_admin_routes(
    router: APIRouter,
    dirs: Dict[str, Path],
    mode: str,
    admin_config: dict,
) -> None:
    """Register all admin CRUD endpoints on *router*.

    Parameters
    ----------
    router:
        The FastAPI ``APIRouter`` to attach routes to.
    dirs:
        Resolved directory dict (``content``, ``templates``, …).
    mode:
        ``"development"`` or ``"production"``.
    admin_config:
        Dict with ``"prefix"`` (e.g. ``"admin/content"``) and ``"templates"``
        (templates subdirectory name) keys.
    """
    prefix = admin_config["prefix"]
    templates_subdir = admin_config["templates"]

    content_dir: Path = dirs["content"]

    # ------------------------------------------------------------------
    # LIST — directory contents with metadata
    # ------------------------------------------------------------------

    @router.get(f"/{prefix}/list", response_model=ListResponse)
    @router.get(f"/{prefix}/list/{{subpath:path}}", response_model=ListResponse)
    async def admin_list(subpath: str = "") -> ListResponse:
        if subpath:
            target = _safe_path(subpath, content_dir)
        else:
            target = content_dir

        if not target.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        if not target.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        entries: List[Entry] = []
        for item in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if item.name.startswith("."):
                continue
            entries.append(_file_entry(item, content_dir))

        return ListResponse(
            path=subpath or "",
            entries=entries,
        )

    # ------------------------------------------------------------------
    # FILE — read
    # ------------------------------------------------------------------

    @router.get(f"/{prefix}/file/{{file_path:path}}", response_model=FileResponse)
    async def admin_get_file(file_path: str) -> FileResponse:
        target = _safe_path(file_path, content_dir)

        if not target.exists():
            raise HTTPException(status_code=404, detail="File not found")
        if target.is_dir():
            raise HTTPException(status_code=400, detail="Path is a directory, not a file")

        try:
            post = parse_markdown_file(target)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to parse file: {exc}")

        stat = target.stat()
        return FileResponse(
            path=str(target.relative_to(content_dir)).replace("\\", "/"),
            frontmatter=post.metadata,
            body=post.content,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        )

    # ------------------------------------------------------------------
    # FILE — create
    # ------------------------------------------------------------------

    @router.post(f"/{prefix}/file/{{file_path:path}}", status_code=201)
    async def admin_create_file(file_path: str, payload: FilePayload) -> Dict[str, str]:
        target = _safe_path(file_path, content_dir)

        if target.exists():
            raise HTTPException(status_code=409, detail="File already exists")

        md = _build_markdown(payload.frontmatter, payload.body)
        _atomic_write(target, md)

        return {"path": str(target.relative_to(content_dir)).replace("\\", "/"), "status": "created"}

    # ------------------------------------------------------------------
    # FILE — update
    # ------------------------------------------------------------------

    @router.put(f"/{prefix}/file/{{file_path:path}}")
    async def admin_update_file(file_path: str, payload: FilePayload) -> Dict[str, str]:
        target = _safe_path(file_path, content_dir)

        if not target.exists():
            raise HTTPException(status_code=404, detail="File not found")
        if target.is_dir():
            raise HTTPException(status_code=400, detail="Path is a directory, not a file")

        md = _build_markdown(payload.frontmatter, payload.body)
        _atomic_write(target, md)

        return {"path": str(target.relative_to(content_dir)).replace("\\", "/"), "status": "updated"}

    # ------------------------------------------------------------------
    # FILE — delete
    # ------------------------------------------------------------------

    @router.delete(f"/{prefix}/file/{{file_path:path}}")
    async def admin_delete_file(file_path: str) -> Dict[str, str]:
        target = _safe_path(file_path, content_dir)

        if not target.exists():
            raise HTTPException(status_code=404, detail="File not found")
        if target.is_dir():
            raise HTTPException(status_code=400, detail="Path is a directory, not a file")

        target.unlink()
        return {"path": str(target.relative_to(content_dir)).replace("\\", "/"), "status": "deleted"}

    # ------------------------------------------------------------------
    # DIR — create
    # ------------------------------------------------------------------

    @router.post(f"/{prefix}/dir/{{dir_path:path}}", status_code=201)
    async def admin_create_dir(dir_path: str) -> Dict[str, str]:
        target = _safe_path(dir_path, content_dir)

        if target.exists():
            raise HTTPException(status_code=409, detail="Directory already exists")

        target.mkdir(parents=True, exist_ok=False)
        return {"path": str(target.relative_to(content_dir)).replace("\\", "/"), "status": "created"}

    # ------------------------------------------------------------------
    # DIR — delete (recursive)
    # ------------------------------------------------------------------

    @router.delete(f"/{prefix}/dir/{{dir_path:path}}")
    async def admin_delete_dir(dir_path: str) -> Dict[str, str]:
        target = _safe_path(dir_path, content_dir)

        if not target.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        if not target.is_dir():
            raise HTTPException(status_code=400, detail="Path is a file, not a directory")
        if target == content_dir:
            raise HTTPException(status_code=400, detail="Cannot delete the content root")

        shutil.rmtree(target)
        return {"path": str(target.relative_to(content_dir)).replace("\\", "/"), "status": "deleted"}

    # ------------------------------------------------------------------
    # HTML Dashboard Routes
    # ------------------------------------------------------------------

    async def _render_admin_template(request, template_name, context):
        templates = request.app.state.templates
        try:
            template = templates.get_template(template_name)
        except Exception:
            return HTMLResponse(
                content=(
                    f"<h1>Admin template not found</h1>"
                    f"<p>Expected <code>{template_name}</code> in your templates directory.</p>"
                    f"<p>Run <code>moosey-cms setup --templates ./templates</code> to install.</p>"
                ),
                status_code=500,
            )
        rendered = await template.render_async({**context, "request": request})
        return HTMLResponse(content=rendered)

    @router.get(f"/{prefix}/", include_in_schema=False)
    @router.get(f"/{prefix}", include_in_schema=False)
    async def admin_dashboard(request: Request):
        return await _render_admin_template(request, f"{templates_subdir}/dashboard.html", {
            "admin_config": admin_config, "mode": mode,
        })

    @router.get(f"/{prefix}/browse/", include_in_schema=False)
    @router.get(f"/{prefix}/browse/{{subpath:path}}", include_in_schema=False)
    async def admin_browse_page(request: Request, subpath: str = ""):
        return await _render_admin_template(request, f"{templates_subdir}/list.html", {
            "admin_config": admin_config, "mode": mode, "subpath": subpath,
        })

    @router.get(f"/{prefix}/edit/", include_in_schema=False)
    @router.get(f"/{prefix}/edit/{{file_path:path}}", include_in_schema=False)
    async def admin_editor_page(request: Request, file_path: str = ""):
        return await _render_admin_template(request, f"{templates_subdir}/editor.html", {
            "admin_config": admin_config, "mode": mode, "file_path": file_path,
        })

    # ------------------------------------------------------------------
    # STATIC — file browsing, upload, and directory creation
    # ------------------------------------------------------------------

    static_dir = admin_config.get("_static_dir")
    static_route = admin_config.get("_static_route", "/static")

    if static_dir is not None:

        def _safe_static_path(user_path: str) -> Path:
            return get_secure_target(user_path, relative_to_path=static_dir)

        @router.get(f"/{prefix}/static", response_model=StaticListResponse)
        @router.get(f"/{prefix}/static/{{subpath:path}}", response_model=StaticListResponse)
        async def admin_static_list(subpath: str = "") -> StaticListResponse:
            if subpath:
                target = _safe_static_path(subpath)
            else:
                target = static_dir

            if not target.exists():
                raise HTTPException(status_code=404, detail="Directory not found")
            if not target.is_dir():
                raise HTTPException(status_code=400, detail="Path is not a directory")

            entries: List[StaticEntry] = []
            for item in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                if item.name.startswith("."):
                    continue
                entries.append(_static_entry(item, static_dir, static_route))

            return StaticListResponse(path=subpath or "", entries=entries)

        @router.post(f"/{prefix}/static/upload/{{file_path:path}}", status_code=201)
        async def admin_static_upload(file_path: str, request: Request) -> StaticUploadResponse:
            target = _safe_static_path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            form = await request.form()
            upload = form.get("file")
            if upload is None:
                raise HTTPException(status_code=400, detail="No file provided")

            contents = await upload.read()
            if len(contents) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File too large (max 10MB)")

            fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=".tmp", prefix=".moosey-")
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(contents)
                os.replace(tmp, target)
            except BaseException:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise

            mime_type, _ = mimetypes.guess_type(target.name)
            rel = str(target.relative_to(static_dir)).replace("\\", "/")
            url = f"{static_route.rstrip('/')}/{rel}"

            return StaticUploadResponse(path=rel, url=url, mime_type=mime_type, status="created")

        @router.post(f"/{prefix}/static/mkdir/{{dir_path:path}}", status_code=201)
        async def admin_static_mkdir(dir_path: str) -> StaticMkdirResponse:
            target = _safe_static_path(dir_path)
            if target.exists():
                raise HTTPException(status_code=409, detail="Directory already exists")
            target.mkdir(parents=True, exist_ok=False)
            rel = str(target.relative_to(static_dir)).replace("\\", "/")
            return StaticMkdirResponse(path=rel, status="created")


# ---------------------------------------------------------------------------
# Markdown builder
# ---------------------------------------------------------------------------

def _build_markdown(meta: Dict[str, Any], body: str) -> str:
    """Serialize frontmatter dict + body into a Markdown file string."""
    if meta:
        fm_lines = ["---"]
        for key, value in meta.items():
            if isinstance(value, list):
                fm_lines.append(f"{key}:")
                for item in value:
                    fm_lines.append(f"  - {item}")
            elif isinstance(value, bool):
                fm_lines.append(f"{key}: {'true' if value else 'false'}")
            elif isinstance(value, (int, float)):
                fm_lines.append(f"{key}: {value}")
            elif isinstance(value, str) and ("\n" in value or ":" in value or "#" in value):
                # Use block scalar for strings with special chars
                fm_lines.append(f"{key}: |")
                for line in value.split("\n"):
                    fm_lines.append(f"  {line}")
            else:
                fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        frontmatter_block = "\n".join(fm_lines) + "\n"
    else:
        frontmatter_block = ""

    # Ensure body ends with a single newline
    body_clean = body.rstrip("\n") + "\n" if body else "\n"

    return frontmatter_block + "\n" + body_clean
