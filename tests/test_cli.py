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
from moosey_cms.lib.config import load_config


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


def _mock_question(value):
    return type("MockQuestion", (), {"ask": lambda self: value})()


def _init_prompts(site="My Site", host="0.0.0.0", port="8000", reload_delay="0.25",
                   admin_prefix="admin/content", admin_templates="admin",
                   cache_backend="memory", cache_ttl="2592000"):
    """Return (text_side_effect, select_side_effect) for cmd_init prompts."""
    text_side_effect = [
        _mock_question(site),
        _mock_question(host),
        _mock_question(port),
        _mock_question(reload_delay),
        _mock_question(admin_prefix),
        _mock_question(admin_templates),
        _mock_question(cache_ttl),
    ]
    return text_side_effect, cache_backend


def _config_prompts(site="Test Site", host="127.0.0.1", port="3000", reload_delay="0.5",
                     admin_prefix="admin/content", admin_templates="admin",
                     cache_backend="memory", cache_ttl="2592000"):
    """Return (text_side_effect, select_side_effect) for cmd_config prompts."""
    text_side_effect = [
        _mock_question(site),
        _mock_question(host),
        _mock_question(port),
        _mock_question(reload_delay),
        _mock_question(admin_prefix),
        _mock_question(admin_templates),
        _mock_question(cache_ttl),
    ]
    return text_side_effect, cache_backend


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
    @patch("questionary.select")
    @patch("questionary.text")
    def test_copies_example_to_target(self, mock_text, mock_select, tmp_path):
        text_ef, sel_val = _init_prompts()
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        assert dst.is_dir()
        assert (dst / "main.py").is_file()
        assert (dst / "content").is_dir()
        assert (dst / "templates").is_dir()
        assert (dst / ".moosey-cms.yaml").is_file()

    @patch("questionary.select")
    @patch("questionary.text")
    def test_patches_main_py_mode(self, mock_text, mock_select, tmp_path):
        text_ef, sel_val = _init_prompts()
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        main_py = dst / "main.py"
        content = main_py.read_text()
        assert "uvicorn.run" in content

    @patch("questionary.select")
    @patch("questionary.text")
    def test_copies_advanced_dir(self, mock_text, mock_select, tmp_path):
        text_ef, sel_val = _init_prompts()
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        assert (dst / "advanced").is_dir()

    @patch("questionary.select")
    @patch("questionary.text")
    def test_copies_assets_dir(self, mock_text, mock_select, tmp_path):
        text_ef, sel_val = _init_prompts()
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        assert (dst / "assets").is_dir()

    @patch("questionary.select")
    @patch("questionary.text")
    def test_idempotent_with_force(self, mock_text, mock_select, tmp_path):
        text_ef, sel_val = _init_prompts()
        mock_text.side_effect = text_ef * 2
        mock_select.return_value.ask.return_value = sel_val

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))
        cmd_init(_Args(path=str(dst), force=True))

        assert dst.is_dir()
        assert (dst / "main.py").is_file()

    @patch("questionary.select")
    @patch("questionary.text")
    def test_fails_without_force_on_nonempty_dir(self, mock_text, mock_select, tmp_path):
        text_ef, sel_val = _init_prompts()
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        dst = tmp_path / "my-site"
        dst.mkdir()
        (dst / "existing.txt").write_text("hi")

        with pytest.raises(SystemExit):
            cmd_init(_Args(path=str(dst), force=False))

    @patch("questionary.select")
    @patch("questionary.text")
    def test_skips_pycache(self, mock_text, mock_select, tmp_path):
        text_ef, sel_val = _init_prompts()
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        dst = tmp_path / "my-site"
        cmd_init(_Args(path=str(dst), force=False))

        caches = list(dst.rglob("__pycache__"))
        assert caches == []


# ---------------------------------------------------------------------------
# cmd_config
# ---------------------------------------------------------------------------

class TestCmdConfig:
    @patch("questionary.select")
    @patch("questionary.text")
    def test_creates_config_file(self, mock_text, mock_select, tmp_path, monkeypatch):
        text_ef, sel_val = _config_prompts()
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=False, generate_key=False))

        config_path = tmp_path / ".moosey-cms.yaml"
        assert config_path.exists()

        from moosey_cms.lib.config import load_config
        config = load_config(config_path)
        assert config.site.name == "Test Site"
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 3000
        assert config.crypto.key != ""

    @patch("questionary.confirm")
    @patch("questionary.select")
    @patch("questionary.text")
    def test_preserves_existing_key(self, mock_text, mock_select, mock_confirm, tmp_path, monkeypatch):
        from moosey_cms.lib.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, save_config
        existing_config = CMSConfig(
            server=ServerConfig(host="0.0.0.0", port=8000),
            site=SiteConfig(name="Existing Site"),
            crypto=CryptoConfig(key="existing-key-123"),
        )
        save_config(existing_config, tmp_path / ".moosey-cms.yaml")

        mock_confirm.return_value.ask.return_value = True

        text_ef, sel_val = _config_prompts(site="Updated Site")
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=False, generate_key=False))

        config = load_config(tmp_path / ".moosey-cms.yaml")
        assert config.crypto.key == "existing-key-123"
        assert config.site.name == "Updated Site"

    @patch("questionary.select")
    @patch("questionary.text")
    def test_generate_key_flag(self, mock_text, mock_select, tmp_path, monkeypatch):
        from moosey_cms.lib.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, save_config
        existing_config = CMSConfig(
            crypto=CryptoConfig(key="old-key-123"),
        )
        save_config(existing_config, tmp_path / ".moosey-cms.yaml")

        text_ef, sel_val = _config_prompts()
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=True, generate_key=True))

        config = load_config(tmp_path / ".moosey-cms.yaml")
        assert config.crypto.key != "old-key-123"

    @patch("questionary.confirm")
    @patch("questionary.select")
    @patch("questionary.text")
    def test_force_overwrites(self, mock_text, mock_select, mock_confirm, tmp_path, monkeypatch):
        from moosey_cms.lib.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, save_config
        existing_config = CMSConfig(
            crypto=CryptoConfig(key="existing-key"),
        )
        save_config(existing_config, tmp_path / ".moosey-cms.yaml")

        text_ef, sel_val = _config_prompts(site="New Site")
        mock_text.side_effect = text_ef
        mock_select.return_value.ask.return_value = sel_val

        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=True, generate_key=False))

        config = load_config(tmp_path / ".moosey-cms.yaml")
        assert config.site.name == "New Site"

    @patch("questionary.confirm")
    def test_aborts_on_no_confirm(self, mock_confirm, tmp_path, monkeypatch):
        from moosey_cms.lib.config import CMSConfig, ServerConfig, SiteConfig, CryptoConfig, save_config
        existing_config = CMSConfig(
            site=SiteConfig(name="Original Site"),
            crypto=CryptoConfig(key="existing-key"),
        )
        save_config(existing_config, tmp_path / ".moosey-cms.yaml")

        mock_confirm.return_value.ask.return_value = False

        monkeypatch.chdir(tmp_path)

        cmd_config(_Args(force=False, generate_key=False))

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
        cmd_admin(_Args(templates=str(templates_dir)))

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
