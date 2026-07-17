"""Tests for GitManager."""
import pytest
from pathlib import Path

from moosey_cms.lib.git import GitManager


@pytest.fixture
def git_repo(tmp_path):
    """Create a temp directory with a git repo and a test file."""
    from git import Repo

    repo = Repo.init(tmp_path)
    # Create an initial commit so the repo has a HEAD
    test_file = tmp_path / "test.md"
    test_file.write_text("initial content\n")
    repo.index.add(["test.md"])
    repo.index.commit("initial commit")
    return tmp_path


@pytest.fixture
def manager(git_repo):
    return GitManager(git_repo)


def test_ensure_repo_existing(git_repo):
    mgr = GitManager(git_repo)
    repo = mgr.ensure_repo()
    assert repo is not None
    assert repo.git_dir is not None


def test_ensure_repo_creates_new(tmp_path):
    mgr = GitManager(tmp_path)
    repo = mgr.ensure_repo()
    assert repo is not None
    assert (tmp_path / ".git").is_dir()


def test_commit_file(manager, git_repo):
    test_file = git_repo / "test.md"
    test_file.write_text("updated content\n")

    hash_id = manager.commit_file(test_file, "content: update test.md (v2)")
    assert hash_id is not None
    assert len(hash_id) > 0


def test_file_history(manager, git_repo):
    history = manager.file_history(git_repo / "test.md")
    assert len(history) >= 1
    assert "hash" in history[0]
    assert "message" in history[0]
    assert "date" in history[0]


def test_file_content_at_does_not_change_worktree(manager, git_repo):
    test_file = git_repo / "test.md"
    original_hash = manager.file_history(test_file)[0]["hash"]
    test_file.write_text("working tree content\n")

    content = manager.file_content_at(test_file, original_hash)

    assert content == "initial content\n"
    assert test_file.read_text() == "working tree content\n"


def test_restore_file(manager, git_repo):
    test_file = git_repo / "test.md"

    # Make a second commit
    test_file.write_text("version 2\n")
    v2_hash = manager.commit_file(test_file, "v2")

    # Make a third commit
    test_file.write_text("version 3\n")
    manager.commit_file(test_file, "v3")

    # Restore to v2
    content = manager.restore_file(test_file, v2_hash)
    assert "version 2" in content
    assert test_file.read_text() == "version 2\n"


def test_push_returns_false_no_remote(tmp_path):
    """push() should return False gracefully when no remote is configured."""
    from git import Repo

    Repo.init(tmp_path)
    mgr = GitManager(tmp_path)
    mgr.ensure_repo()
    result = mgr.push()
    assert result is False
