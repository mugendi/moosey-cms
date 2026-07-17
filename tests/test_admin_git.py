"""Tests for git-integrated admin endpoints."""
import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import frontmatter


@pytest.fixture
def git_content_dir(tmp_path):
    """Content dir with a git repo initialized."""
    from moosey_cms.lib.git import GitManager

    d = tmp_path / "content"
    d.mkdir()
    mgr = GitManager(d)
    mgr.ensure_repo()
    return d


@pytest.fixture
def app(git_content_dir):
    from moosey_cms.admin import register_admin_routes
    from moosey_cms.lib.config import CMSConfig
    from fastapi import APIRouter

    application = FastAPI()
    application.state.site_data = {"name": "Test"}
    application.state.mode = "development"
    application.state.config = CMSConfig()

    router = APIRouter()
    register_admin_routes(
        router=router,
        dirs={"content": git_content_dir},
        mode="development",
        admin_config={
            "prefix": "admin/content",
            "templates": "admin",
            "git": {"auto_push": False},
        },
    )
    application.include_router(router)
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


def test_create_file_has_version(client, git_content_dir):
    resp = client.post(
        "/admin/content/file/test.md",
        json={"frontmatter": {"title": "Test"}, "body": "Hello"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "created"

    post = frontmatter.load(git_content_dir / "test.md")
    assert post.metadata.get("version") == 1


def test_update_file_bumps_version(client, git_content_dir):
    # Create
    client.post(
        "/admin/content/file/test.md",
        json={"frontmatter": {"title": "Test"}, "body": "v1"},
    )

    # Update
    resp = client.put(
        "/admin/content/file/test.md",
        json={"frontmatter": {"title": "Test"}, "body": "v2"},
    )
    assert resp.status_code == 200

    post = frontmatter.load(git_content_dir / "test.md")
    assert post.metadata.get("version") == 2


def test_file_history(client, git_content_dir):
    # Create a file
    client.post(
        "/admin/content/file/history-test.md",
        json={"frontmatter": {"title": "Hist"}, "body": "Hello"},
    )

    resp = client.get("/admin/content/file-history/history-test.md")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["history"]) >= 1
    assert "hash" in data["history"][0]


def test_rollback(client, git_content_dir):
    # Create
    client.post(
        "/admin/content/file/rollback-test.md",
        json={"frontmatter": {"title": "RB"}, "body": "original"},
    )

    # Update
    client.put(
        "/admin/content/file/rollback-test.md",
        json={"frontmatter": {"title": "RB"}, "body": "updated"},
    )

    # Get history
    hist_resp = client.get("/admin/content/file-history/rollback-test.md")
    history = hist_resp.json()["history"]
    assert len(history) >= 2

    # Rollback to the first commit (create)
    original_hash = history[-1]["hash"]
    resp = client.post(
        "/admin/content/rollback/rollback-test.md",
        json={"commit": original_hash},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rolled_back"

    # Verify file content was restored
    post = frontmatter.load(git_content_dir / "rollback-test.md")
    assert post.content.strip() == "original"
    assert post.metadata.get("version") == 3  # bumped from 2


def test_rollback_invalid_hash(client, git_content_dir):
    """Rollback with invalid commit hash should return 400."""
    client.post(
        "/admin/content/file/invalid-test.md",
        json={"frontmatter": {"title": "Inv"}, "body": "Hello"},
    )

    resp = client.post(
        "/admin/content/rollback/invalid-test.md",
        json={"commit": "nonexistent123"},
    )
    assert resp.status_code == 400


def test_rollback_missing_commit_field(client, git_content_dir):
    """Rollback without commit field should return 400."""
    client.post(
        "/admin/content/file/missing-test.md",
        json={"frontmatter": {"title": "Miss"}, "body": "Hello"},
    )

    resp = client.post(
        "/admin/content/rollback/missing-test.md",
        json={},
    )
    assert resp.status_code == 400


def test_delete_file_no_commit(client, git_content_dir):
    """File deletion should not create a git commit."""
    # Create
    client.post(
        "/admin/content/file/del-test.md",
        json={"frontmatter": {"title": "Del"}, "body": "Goodbye"},
    )

    # Delete
    resp = client.delete("/admin/content/file/del-test.md")
    assert resp.status_code == 200
    assert not (git_content_dir / "del-test.md").exists()


# ------------------------------------------------------------------
# auto_push tests
# ------------------------------------------------------------------


@pytest.fixture
def auto_push_app(git_content_dir):
    """App with auto_push=True."""
    from moosey_cms.admin import register_admin_routes
    from moosey_cms.lib.config import CMSConfig
    from fastapi import FastAPI
    from fastapi import APIRouter

    application = FastAPI()
    application.state.site_data = {"name": "Test"}
    application.state.mode = "development"
    application.state.config = CMSConfig()

    router = APIRouter()
    register_admin_routes(
        router=router,
        dirs={"content": git_content_dir},
        mode="development",
        admin_config={
            "prefix": "admin/content",
            "templates": "admin",
            "git": {"auto_push": True},
        },
    )
    application.include_router(router)
    return application


@pytest.fixture
def auto_push_client(auto_push_app):
    return TestClient(auto_push_app)


def test_auto_push_triggers_push(auto_push_client, git_content_dir):
    """When auto_push=True, git_mgr.push() should be called after commit."""
    from unittest.mock import patch

    with patch("moosey_cms.admin.GitManager.push") as mock_push:
        resp = auto_push_client.post(
            "/admin/content/file/push-test.md",
            json={"frontmatter": {"title": "Push"}, "body": "Hello"},
        )
        assert resp.status_code == 201
        mock_push.assert_called_once()


def test_auto_push_triggers_push_on_update(auto_push_client, git_content_dir):
    """When auto_push=True, push() should also be called on file update."""
    from unittest.mock import patch

    # Create first
    auto_push_client.post(
        "/admin/content/file/push-update.md",
        json={"frontmatter": {"title": "Push"}, "body": "v1"},
    )

    with patch("moosey_cms.admin.GitManager.push") as mock_push:
        resp = auto_push_client.put(
            "/admin/content/file/push-update.md",
            json={"frontmatter": {"title": "Push"}, "body": "v2"},
        )
        assert resp.status_code == 200
        mock_push.assert_called_once()


def test_no_auto_push_skips_push(client, git_content_dir):
    """When auto_push=False, push() should NOT be called."""
    from unittest.mock import patch

    with patch("moosey_cms.admin.GitManager.push") as mock_push:
        resp = client.post(
            "/admin/content/file/no-push.md",
            json={"frontmatter": {"title": "NoPush"}, "body": "Hello"},
        )
        assert resp.status_code == 201
        mock_push.assert_not_called()
