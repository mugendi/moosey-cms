"""
Git operations for Moosey CMS file versioning.

Uses gitpython to commit, push, list history, and restore files.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from git import Repo

logger = logging.getLogger(__name__)


class GitManager:
    """Wraps gitpython for content file versioning."""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        self._repo: Optional[Repo] = None

    def ensure_repo(self) -> Repo:
        """Return the git Repo, creating one if it doesn't exist."""
        if self._repo is not None:
            return self._repo

        git_dir = self.repo_path / ".git"
        if git_dir.is_dir():
            self._repo = Repo(self.repo_path)
        else:
            self._repo = Repo.init(self.repo_path)
            logger.info("Initialized git repo at %s", self.repo_path)

        return self._repo

    def commit_file(self, file_path: Path, message: str) -> Optional[str]:
        """Stage and commit a single file. Returns commit hash or None."""
        repo = self.ensure_repo()
        file_path = Path(file_path).resolve()

        try:
            rel = file_path.relative_to(self.repo_path)
        except ValueError:
            logger.error("File %s is outside repo %s", file_path, self.repo_path)
            return None

        repo.index.add([str(rel)])
        commit = repo.index.commit(message)
        return commit.hexsha

    def push(self) -> bool:
        """Push to remote. Returns True on success, False on failure."""
        repo = self.ensure_repo()

        if not repo.remotes:
            logger.warning("No git remote configured; skipping push")
            return False

        try:
            for remote in repo.remotes:
                remote.push()
            return True
        except Exception as exc:
            logger.error("git push failed: %s", exc)
            return False

    def file_history(
        self, file_path: Path, limit: int = 50
    ) -> List[Dict[str, str]]:
        """Return commit history for a single file."""
        repo = self.ensure_repo()
        file_path = Path(file_path).resolve()

        try:
            rel = str(file_path.relative_to(self.repo_path))
        except ValueError:
            return []

        history: List[Dict[str, str]] = []
        for commit in repo.iter_commits(paths=rel, max_count=limit):
            history.append(
                {
                    "hash": commit.hexsha,
                    "message": commit.message.strip(),
                    "date": commit.committed_datetime.isoformat(),
                }
            )
        return history

    def restore_file(self, file_path: Path, commit_hash: str) -> str:
        """Restore a file from a specific commit. Returns restored content."""
        repo = self.ensure_repo()
        file_path = Path(file_path).resolve()

        try:
            rel = str(file_path.relative_to(self.repo_path))
        except ValueError:
            raise ValueError(f"File {file_path} is outside repo {self.repo_path}")

        # Get the file content at that commit
        try:
            commit = repo.commit(commit_hash)
            content = commit.tree[rel].data_stream.read().decode("utf-8")
        except (KeyError, Exception) as exc:
            raise ValueError(
                f"Could not read file {rel} at commit {commit_hash}: {exc}"
            )

        # Write to disk
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return content
