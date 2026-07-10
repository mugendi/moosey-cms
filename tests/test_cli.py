"""Tests for the moosey-cms CLI."""

import sys
import subprocess
from pathlib import Path

import pytest

from moosey_cms.cli import cmd_setup, get_bundled_templates_dir


BUNDLED = get_bundled_templates_dir()


class TestGetBundledTemplatesDir:
    """Tests for get_bundled_templates_dir()."""

    def test_returns_path(self):
        result = get_bundled_templates_dir()
        assert isinstance(result, Path)

    def test_directory_exists(self):
        assert BUNDLED.is_dir()

    def test_contains_expected_files(self):
        names = [f.name for f in BUNDLED.iterdir() if f.is_file()]
        assert "base.html" in names
        assert "editor.html" in names
        assert "dashboard.html" in names
        assert "list.html" in names
        assert "admin.js" in names


class TestCmdSetup:
    """Tests for the setup subcommand."""

    def test_creates_admin_directory(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        class Args:
            templates = str(templates_dir)

        cmd_setup(Args())

        admin_dir = templates_dir / "admin"
        assert admin_dir.is_dir()

    def test_copies_all_bundled_files(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        class Args:
            templates = str(templates_dir)

        cmd_setup(Args())

        admin_dir = templates_dir / "admin"
        expected = [f.name for f in BUNDLED.iterdir() if f.is_file()]
        copied = [f.name for f in admin_dir.iterdir() if f.is_file()]

        assert sorted(copied) == sorted(expected)

    def test_creates_templates_dir_if_missing(self, tmp_path):
        templates_dir = tmp_path / "does-not-exist"

        class Args:
            templates = str(templates_dir)

        cmd_setup(Args())

        assert (templates_dir / "admin").is_dir()

    def test_idempotent_running_twice(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        class Args:
            templates = str(templates_dir)

        cmd_setup(Args())
        cmd_setup(Args())  # second run should not fail

        admin_dir = templates_dir / "admin"
        assert admin_dir.is_dir()

    def test_copied_files_are_readable(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        class Args:
            templates = str(templates_dir)

        cmd_setup(Args())

        for f in (templates_dir / "admin").iterdir():
            if f.is_file():
                content = f.read_text(encoding="utf-8")
                assert len(content) > 0


class TestCLIMain:
    """Tests for the CLI entry point via subprocess."""

    def test_setup_command_runs(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "moosey_cms.cli", "setup", "--templates", str(templates_dir)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert (templates_dir / "admin").is_dir()

    def test_setup_default_templates_flag(self, tmp_path):
        """--templates defaults to ./templates when not given."""
        result = subprocess.run(
            [sys.executable, "-m", "moosey_cms.cli", "setup"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

        # Should create ./templates/admin in the cwd
        assert result.returncode == 0

    def test_no_command_fails(self):
        result = subprocess.run(
            [sys.executable, "-m", "moosey_cms.cli"],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
