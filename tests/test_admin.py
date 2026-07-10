"""
Tests for the admin CRUD API (src/moosey_cms/admin.py).

Covers all 7 endpoints (list, get, create, update, delete file; create, delete dir),
the _build_markdown helper, and path traversal protection.
"""

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRouter
from starlette.testclient import TestClient

from moosey_cms.admin import (
    FilePayload,
    _build_markdown,
    register_admin_routes,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_MD = """\
---
title: {title}
tags:
  - python
  - fastapi
order: 3
draft: false
---

Body content here.
"""


@pytest.fixture
def content_dir(tmp_path):
    """Create a content directory with sample markdown files."""
    d = tmp_path / "content"
    d.mkdir()

    (d / "index.md").write_text(SAMPLE_MD.format(title="Home"))
    (d / "about.md").write_text(SAMPLE_MD.format(title="About Us"))

    blog = d / "blog"
    blog.mkdir()
    (blog / "index.md").write_text(SAMPLE_MD.format(title="Blog"))
    (blog / "hello.md").write_text(SAMPLE_MD.format(title="Hello World"))

    # Dotfile — should be skipped in listings
    (d / ".hidden.md").write_text("---\ntitle: Hidden\n---\nSecret.")

    return d


@pytest.fixture
def client(content_dir):
    """Create a TestClient with admin routes registered."""
    app = FastAPI()
    router = APIRouter()
    register_admin_routes(
        router,
        dirs={"content": content_dir},
        mode="development",
        admin_config={"prefix": "admin", "templates": "admin"},
    )
    app.include_router(router)
    return TestClient(app)


PREFIX = "admin"


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------

class TestAdminList:
    def test_list_root(self, client):
        resp = client.get(f"/{PREFIX}/list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["path"] == ""
        names = [e["name"] for e in data["entries"]]
        # Dirs come first, then files, alphabetically
        assert "blog" in names
        assert "about.md" in names
        assert "index.md" in names

    def test_list_dirs_first(self, client):
        resp = client.get(f"/{PREFIX}/list")
        entries = resp.json()["entries"]
        types = [e["type"] for e in entries]
        # All directories before all files
        dir_end = types.index("file")
        assert all(t == "directory" for t in types[:dir_end])
        assert all(t == "file" for t in types[dir_end:])

    def test_list_subpath(self, client):
        resp = client.get(f"/{PREFIX}/list/blog")
        assert resp.status_code == 200
        data = resp.json()
        assert data["path"] == "blog"
        names = [e["name"] for e in data["entries"]]
        assert "hello.md" in names
        assert "index.md" in names

    def test_list_returns_title_from_frontmatter(self, client):
        resp = client.get(f"/{PREFIX}/list")
        entries = resp.json()["entries"]
        about = next(e for e in entries if e["name"] == "about.md")
        assert about["title"] == "About Us"

    def test_list_dir_with_index_md(self, client):
        resp = client.get(f"/{PREFIX}/list")
        entries = resp.json()["entries"]
        blog = next(e for e in entries if e["name"] == "blog")
        assert blog["is_index"] is True
        assert blog["title"] == "Blog"

    def test_list_skips_dotfiles(self, client):
        resp = client.get(f"/{PREFIX}/list")
        names = [e["name"] for e in resp.json()["entries"]]
        assert ".hidden.md" not in names

    def test_list_not_found(self, client):
        resp = client.get(f"/{PREFIX}/list/nonexistent")
        assert resp.status_code == 404

    def test_list_path_is_file(self, client):
        resp = client.get(f"/{PREFIX}/list/about.md")
        assert resp.status_code == 400

    def test_list_empty_dir(self, content_dir):
        empty = content_dir / "empty"
        empty.mkdir()
        app = FastAPI()
        router = APIRouter()
        register_admin_routes(
            router,
            dirs={"content": content_dir},
            mode="development",
            admin_config={"prefix": "admin", "templates": "admin"},
        )
        app.include_router(router)
        c = TestClient(app)
        resp = c.get(f"/{PREFIX}/list/empty")
        assert resp.status_code == 200
        assert resp.json()["entries"] == []


# ---------------------------------------------------------------------------
# GET FILE
# ---------------------------------------------------------------------------

class TestAdminGetFile:
    def test_get_file(self, client):
        resp = client.get(f"/{PREFIX}/file/about.md")
        assert resp.status_code == 200
        data = resp.json()
        assert data["path"] == "about.md"
        assert data["frontmatter"]["title"] == "About Us"
        assert "Body content here." in data["body"]
        assert data["size"] > 0
        assert data["modified"] is not None

    def test_get_file_not_found(self, client):
        resp = client.get(f"/{PREFIX}/file/nope.md")
        assert resp.status_code == 404

    def test_get_file_is_directory(self, client):
        resp = client.get(f"/{PREFIX}/file/blog")
        assert resp.status_code == 400

    def test_get_file_frontmatter_fields(self, client):
        resp = client.get(f"/{PREFIX}/file/about.md")
        fm = resp.json()["frontmatter"]
        assert fm["title"] == "About Us"
        assert fm["tags"] == ["python", "fastapi"]
        assert fm["order"] == 3
        assert fm["draft"] is False

    def test_get_file_body_content(self, client):
        resp = client.get(f"/{PREFIX}/file/about.md")
        assert resp.json()["body"].strip() == "Body content here."


# ---------------------------------------------------------------------------
# CREATE FILE
# ---------------------------------------------------------------------------

class TestAdminCreateFile:
    def test_create_file(self, client, content_dir):
        payload = {"frontmatter": {"title": "New Post"}, "body": "Hello!"}
        resp = client.post(f"/{PREFIX}/file/blog/new.md", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["path"] == "blog/new.md"
        assert data["status"] == "created"
        # File exists on disk
        assert (content_dir / "blog" / "new.md").exists()

    def test_create_file_already_exists(self, client):
        payload = {"frontmatter": {"title": "About"}, "body": "x"}
        resp = client.post(f"/{PREFIX}/file/about.md", json=payload)
        assert resp.status_code == 409

    def test_create_file_with_frontmatter(self, client, content_dir):
        payload = {
            "frontmatter": {"title": "Test", "tags": ["a", "b"], "draft": True},
            "body": "Content.",
        }
        resp = client.post(f"/{PREFIX}/file/test.md", json=payload)
        assert resp.status_code == 201
        # Read back and verify
        resp2 = client.get(f"/{PREFIX}/file/test.md")
        fm = resp2.json()["frontmatter"]
        assert fm["title"] == "Test"
        assert fm["tags"] == ["a", "b"]
        assert fm["draft"] is True

    def test_create_file_with_lists(self, client, content_dir):
        payload = {
            "frontmatter": {"tags": ["x", "y", "z"]},
            "body": "",
        }
        resp = client.post(f"/{PREFIX}/file/list-test.md", json=payload)
        assert resp.status_code == 201
        # Verify on disk
        raw = (content_dir / "list-test.md").read_text()
        assert "  - x" in raw
        assert "  - y" in raw
        assert "  - z" in raw

    def test_create_file_nested_path(self, client, content_dir):
        payload = {"frontmatter": {"title": "Deep"}, "body": "Deep content."}
        resp = client.post(f"/{PREFIX}/file/a/b/c/deep.md", json=payload)
        assert resp.status_code == 201
        assert (content_dir / "a" / "b" / "c" / "deep.md").exists()


# ---------------------------------------------------------------------------
# UPDATE FILE
# ---------------------------------------------------------------------------

class TestAdminUpdateFile:
    def test_update_file(self, client, content_dir):
        payload = {"frontmatter": {"title": "Updated"}, "body": "New body."}
        resp = client.put(f"/{PREFIX}/file/about.md", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "updated"
        # Verify on disk
        resp2 = client.get(f"/{PREFIX}/file/about.md")
        assert resp2.json()["frontmatter"]["title"] == "Updated"
        assert resp2.json()["body"] == "New body."

    def test_update_file_not_found(self, client):
        payload = {"frontmatter": {}, "body": "x"}
        resp = client.put(f"/{PREFIX}/file/nope.md", json=payload)
        assert resp.status_code == 404

    def test_update_file_is_directory(self, client):
        payload = {"frontmatter": {}, "body": "x"}
        resp = client.put(f"/{PREFIX}/file/blog", json=payload)
        assert resp.status_code == 400

    def test_update_file_overwrites_body(self, client, content_dir):
        # Create a file with known content
        (content_dir / "overwrite.md").write_text("---\ntitle: Old\n---\nOld body.")
        payload = {"frontmatter": {"title": "New"}, "body": "Completely different."}
        resp = client.put(f"/{PREFIX}/file/overwrite.md", json=payload)
        assert resp.status_code == 200
        raw = (content_dir / "overwrite.md").read_text()
        assert "Old body." not in raw
        assert "Completely different." in raw


# ---------------------------------------------------------------------------
# DELETE FILE
# ---------------------------------------------------------------------------

class TestAdminDeleteFile:
    def test_delete_file(self, client, content_dir):
        # Create a file to delete
        (content_dir / "to-delete.md").write_text("---\ntitle: Delete Me\n---\nBye.")
        resp = client.delete(f"/{PREFIX}/file/to-delete.md")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"
        assert not (content_dir / "to-delete.md").exists()

    def test_delete_file_not_found(self, client):
        resp = client.delete(f"/{PREFIX}/file/nope.md")
        assert resp.status_code == 404

    def test_delete_file_is_directory(self, client):
        resp = client.delete(f"/{PREFIX}/file/blog")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# CREATE DIR
# ---------------------------------------------------------------------------

class TestAdminCreateDir:
    def test_create_dir(self, client, content_dir):
        resp = client.post(f"/{PREFIX}/dir/new-section")
        assert resp.status_code == 201
        data = resp.json()
        assert data["path"] == "new-section"
        assert data["status"] == "created"
        assert (content_dir / "new-section").is_dir()

    def test_create_dir_already_exists(self, client):
        resp = client.post(f"/{PREFIX}/dir/blog")
        assert resp.status_code == 409

    def test_create_dir_nested(self, client, content_dir):
        resp = client.post(f"/{PREFIX}/dir/a/b/c")
        assert resp.status_code == 201
        assert (content_dir / "a" / "b" / "c").is_dir()


# ---------------------------------------------------------------------------
# DELETE DIR
# ---------------------------------------------------------------------------

class TestAdminDeleteDir:
    def test_delete_dir(self, client, content_dir):
        # Create a dir with content to delete
        target = content_dir / "to-delete"
        target.mkdir()
        (target / "file.md").write_text("content")
        resp = client.delete(f"/{PREFIX}/dir/to-delete")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"
        assert not target.exists()

    def test_delete_dir_not_found(self, client):
        resp = client.delete(f"/{PREFIX}/dir/nonexistent")
        assert resp.status_code == 404

    def test_delete_dir_is_file(self, client):
        resp = client.delete(f"/{PREFIX}/dir/about.md")
        assert resp.status_code == 400

    def test_delete_dir_content_root(self, client):
        resp = client.delete(f"/{PREFIX}/dir/")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# _build_markdown (unit tests)
# ---------------------------------------------------------------------------

class TestBuildMarkdown:
    def test_build_markdown_empty(self):
        result = _build_markdown({}, "")
        assert result == "\n\n"

    def test_build_markdown_lists(self):
        result = _build_markdown({"tags": ["a", "b", "c"]}, "body")
        assert "  - a" in result
        assert "  - b" in result
        assert "  - c" in result

    def test_build_markdown_bools(self):
        result = _build_markdown({"draft": True, "published": False}, "")
        assert "draft: true" in result
        assert "published: false" in result

    def test_build_markdown_block_scalar(self):
        result = _build_markdown({"title": "Hello: World #1"}, "")
        assert "title: |" in result
        assert "  Hello: World #1" in result

    def test_build_markdown_numbers(self):
        result = _build_markdown({"order": 3, "weight": 2.5}, "")
        assert "order: 3" in result
        assert "weight: 2.5" in result

    def test_build_markdown_roundtrip(self, content_dir):
        """Create via admin, read back — data matches."""
        app = FastAPI()
        router = APIRouter()
        register_admin_routes(
            router,
            dirs={"content": content_dir},
            mode="development",
            admin_config={"prefix": "admin", "templates": "admin"},
        )
        app.include_router(router)
        c = TestClient(app)

        payload = {
            "frontmatter": {"title": "Roundtrip", "tags": ["x"], "order": 7},
            "body": "Test body.",
        }
        c.post(f"/{PREFIX}/file/roundtrip.md", json=payload)
        resp = c.get(f"/{PREFIX}/file/roundtrip.md")
        data = resp.json()
        assert data["frontmatter"]["title"] == "Roundtrip"
        assert data["frontmatter"]["tags"] == ["x"]
        assert data["frontmatter"]["order"] == 7
        assert data["body"] == "Test body."


# ---------------------------------------------------------------------------
# Path traversal protection
# ---------------------------------------------------------------------------

class TestPathTraversal:
    def test_traversal_rejected(self, client):
        resp = client.get(f"/{PREFIX}/file/../../etc/passwd")
        assert resp.status_code in (400, 404, 422)

    def test_null_byte_rejected(self, client):
        resp = client.get(f"/{PREFIX}/file/%00../../etc/passwd")
        assert resp.status_code in (400, 404, 422)

    def test_absolute_path_rejected(self, client):
        resp = client.get(f"/{PREFIX}/file//etc/passwd")
        assert resp.status_code in (400, 404, 422)
