"""Tests for the moosey-cms CLI."""

import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from moosey_cms.cli import (
    cmd_admin,
    cmd_config,
    cmd_init,
    get_bundled_templates_dir,
    get_example_dir,
)
from moosey_cms.config import load_config


BUNDLED = get_bundled_templates_dir()
EXAMPLE = get_example_dir()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Args:
    """Minimal namespace for simulating argparse args."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# get_bundled_templates_dir / get_example_dir
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_bundled_templates_dir_exists(self):
        assert BUNDLED.is_dir()

    def test_bundled_templates_contains_expected_files(self):
        names = [f.name for f in BUNDLED.iterdir() if f.is_file()]
        assert "base.html" in names
        assert "editor.html" in names
        assert "dashboard.html" in names
        assert "list.html" in names
        assert "admin.js" in names

    def test_example_dir_exists(self):
        assert EXAMPLE.is_dir()

    def test_example_dir_contains_main(self):
        assert (EXAMPLE / "main.py").is_file()

    def test_example_dir_contains_content(self):
        assert (EXAMPLE / "content").is_dir()

    def test_example_dir_contains_templates(self):
        assert (EXAMPLE / "templates").is_dir()


# ---------------------------------------------------------------------------
# cmd_init
# ---------------------------------------------------------------------------

class TestCmdInit:
    @patch("questionary.text")
    def test_copies_example_to_target(self, mock_text, tmp_path):
        # Mock questionary prompts with correct values
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "My Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        assert dst.is_dir()
        assert (dst / "main.py").is_file()
        assert (dst / "content").is_dir()
        assert (dst / "templates").is_dir()
        assert (dst / ".moosey-cms.yaml").is_file()

    @patch("questionary.text")
    def test_patches_main_py_mode(self, mock_text, tmp_path):
        # Mock questionary prompts with correct values
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "My Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        main_py = dst / "main.py"
        content = main_py.read_text()
        assert "uvicorn.run" in content

    @patch("questionary.text")
    def test_copies_advanced_dir(self, mock_text, tmp_path):
        # Mock questionary prompts with correct values
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "My Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        assert (dst / "advanced").is_dir()

    @patch("questionary.text")
    def test_copies_assets_dir(self, mock_text, tmp_path):
        # Mock questionary prompts with correct values
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "My Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        assert (dst / "assets").is_dir()

    @patch("questionary.text")
    def test_idempotent_with_force(self, mock_text, tmp_path):
        # Mock questionary prompts with correct values
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "My Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ] * 2  # Duplicate for second call

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))
        cmd_init(_Args(path=str(dst), force=True))  # should not fail

        assert dst.is_dir()
        assert (dst / "main.py").is_file()

    @patch("questionary.text")
    def test_fails_without_force_on_nonempty_dir(self, mock_text, tmp_path):
        # Mock questionary prompts with correct values
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "My Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        dst = tmp_path / "my-site"
        dst.mkdir()
        (dst / "existing.txt").write_text("hi")

        with pytest.raises(SystemExit):
            cmd_init(_Args(path=str(dst), force=False))

    @patch("questionary.text")
    def test_skips_pycache(self, mock_text, tmp_path):
        # Mock questionary prompts with correct values
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "My Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        caches = list(dst.rglob("__pycache__"))
        assert caches == []


# ---------------------------------------------------------------------------
# cmd_config
# ---------------------------------------------------------------------------

class TestCmdConfig:
    @patch("questionary.text")
    def test_creates_config_file(self, mock_text, tmp_path, monkeypatch):
        # Mock questionary prompts
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "Test Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "127.0.0.1"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "3000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.5"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=False, generate_key=False))

        config_path = tmp_path / ".moosey-cms.yaml"
        assert config_path.exists()

        # Verify content
        from moosey_cms.config import load_config
        config = load_config(config_path)
        assert config.site.name == "Test Site"
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 3000
        assert config.crypto.key != ""  # Key was generated

    @patch("questionary.confirm")
    @patch("questionary.text")
    def test_preserves_existing_key(self, mock_text, mock_confirm, tmp_path, monkeypatch):
        # Create existing config
        from moosey_cms.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, save_config
        existing_config = CMSConfig(
            server=ServerConfig(host="0.0.0.0", port=8000),
            site=SiteConfig(name="Existing Site"),
            crypto=CryptoConfig(key="existing-key-123"),
        )
        save_config(existing_config, tmp_path / ".moosey-cms.yaml")

        # Mock confirm to allow overwrite
        mock_confirm.return_value.ask.return_value = True

        # Mock questionary prompts
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "Updated Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=False, generate_key=False))

        # Verify key was preserved
        config = load_config(tmp_path / ".moosey-cms.yaml")
        assert config.crypto.key == "existing-key-123"
        assert config.site.name == "Updated Site"

    @patch("questionary.text")
    def test_generate_key_flag(self, mock_text, tmp_path, monkeypatch):
        # Create existing config with a key
        from moosey_cms.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, save_config
        existing_config = CMSConfig(
            crypto=CryptoConfig(key="old-key-123"),
        )
        save_config(existing_config, tmp_path / ".moosey-cms.yaml")

        # Mock questionary prompts
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "My Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=True, generate_key=True))

        # Verify key was regenerated
        config = load_config(tmp_path / ".moosey-cms.yaml")
        assert config.crypto.key != "old-key-123"

    @patch("questionary.confirm")
    @patch("questionary.text")
    def test_force_overwrites(self, mock_text, mock_confirm, tmp_path, monkeypatch):
        # Create existing config
        from moosey_cms.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, save_config
        existing_config = CMSConfig(
            crypto=CryptoConfig(key="existing-key"),
        )
        save_config(existing_config, tmp_path / ".moosey-cms.yaml")

        # Mock questionary prompts (no confirm needed with --force)
        mock_text.side_effect = [
            type("MockQuestion", (), {"ask": lambda self: "New Site"})(),  # site_name
            type("MockQuestion", (), {"ask": lambda self: "0.0.0.0"})(),  # host
            type("MockQuestion", (), {"ask": lambda self: "8000"})(),  # port
            type("MockQuestion", (), {"ask": lambda self: "0.25"})(),  # reload_delay
            type("MockQuestion", (), {"ask": lambda self: "admin"})(),  # admin_prefix
        ]

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=True, generate_key=False))

        # Verify config was updated
        config = load_config(tmp_path / ".moosey-cms.yaml")
        assert config.site.name == "New Site"

    @patch("questionary.confirm")
    @patch("questionary.text")
    def test_aborts_on_no_confirm(self, mock_text, mock_confirm, tmp_path, monkeypatch):
        # Create existing config
        from moosey_cms.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, save_config
        existing_config = CMSConfig(
            site=SiteConfig(name="Original Site"),
            crypto=CryptoConfig(key="existing-key"),
        )
        save_config(existing_config, tmp_path / ".moosey-cms.yaml")

        # Mock confirm to deny overwrite
        mock_confirm.return_value.ask.return_value = False

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=False, generate_key=False))

        # Verify config was NOT updated
        config = load_config(tmp_path / ".moosey-cms.yaml")
        assert config.site.name == "Original Site"


# ---------------------------------------------------------------------------
# cmd_admin
# ---------------------------------------------------------------------------

class TestCmdAdmin:
    def test_creates_admin_directory(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        cmd_admin(_Args(templates=str(templates_dir)))

        assert (templates_dir / "admin").is_dir()

    def test_copies_all_bundled_files(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        cmd_admin(_Args(templates=str(templates_dir)))

        admin_dir = templates_dir / "admin"
        expected = [f.name for f in BUNDLED.iterdir() if f.is_file()]
        copied = [f.name for f in admin_dir.iterdir() if f.is_file()]

        assert sorted(copied) == sorted(expected)

    def test_creates_templates_dir_if_missing(self, tmp_path):
        templates_dir = tmp_path / "does-not-exist"

        cmd_admin(_Args(templates=str(templates_dir)))

        assert (templates_dir / "admin").is_dir()

    def test_idempotent(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        cmd_admin(_Args(templates=str(templates_dir)))
        cmd_admin(_Args(templates=str(templates_dir)))  # should not fail

        assert (templates_dir / "admin").is_dir()

    def test_copied_files_are_readable(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        cmd_admin(_Args(templates=str(templates_dir)))

        for f in (templates_dir / "admin").iterdir():
            if f.is_file():
                content = f.read_text(encoding="utf-8")
                assert len(content) > 0


# ---------------------------------------------------------------------------
# Subprocess integration tests
# ---------------------------------------------------------------------------

class TestCLISubprocess:
    @pytest.mark.skip(reason="Interactive prompts cannot be tested in subprocess")
    def test_init_command_runs(self, tmp_path):
        dst = tmp_path / "scaffolded"
        result = subprocess.run(
            [sys.executable, "-m", "moosey_cms.cli", "init", str(dst)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert dst.is_dir()

    def test_admin_command_runs(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        result = subprocess.run(
            [sys.executable, "-m", "moosey_cms.cli", "admin", "--templates", str(templates_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (templates_dir / "admin").is_dir()

    def test_no_command_fails(self):
        result = subprocess.run(
            [sys.executable, "-m", "moosey_cms.cli"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_dev_fails_without_main_py(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "moosey_cms.cli", "dev"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode != 0
        assert "main.py not found" in result.stderr

    def test_prod_fails_without_main_py(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "moosey_cms.cli", "prod"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode != 0
        assert "main.py not found" in result.stderr
