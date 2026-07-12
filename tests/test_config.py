"""
Tests for moosey_cms.config module.
"""

import pytest
from pathlib import Path
import yaml

from moosey_cms.config import (
    CMSConfig,
    ServerConfig,
    SiteConfig,
    CryptoConfig,
    load_config,
    save_config,
)


def test_default_config():
    """Test that default config has expected values."""
    config = CMSConfig()

    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8000
    assert config.server.reload_delay == 0.25
    assert config.site.name == "My Site"
    assert config.site.admin_prefix == "admin"
    assert config.crypto.key == ""
    assert config.image_cdn is None
    assert config.image_processing is None
    assert config.sanitize is None


def test_custom_config():
    """Test creating config with custom values."""
    config = CMSConfig(
        server=ServerConfig(host="127.0.0.1", port=3000),
        site=SiteConfig(name="Custom Site"),
        crypto=CryptoConfig(key="test-key-123"),
    )

    assert config.server.host == "127.0.0.1"
    assert config.server.port == 3000
    assert config.site.name == "Custom Site"
    assert config.crypto.key == "test-key-123"


def test_save_and_load_config(tmp_path):
    """Test saving and loading config from file."""
    config_path = tmp_path / ".moosey-cms.yaml"

    config = CMSConfig(
        server=ServerConfig(host="192.168.1.1", port=9000),
        site=SiteConfig(name="Test Site"),
        crypto=CryptoConfig(key="my-secret-key"),
    )

    save_config(config, config_path)
    assert config_path.exists()

    loaded = load_config(config_path)

    assert loaded.server.host == "192.168.1.1"
    assert loaded.server.port == 9000
    assert loaded.site.name == "Test Site"
    assert loaded.crypto.key == "my-secret-key"


def test_load_config_nonexistent():
    """Test loading config when file doesn't exist returns defaults."""
    config = load_config(Path("/nonexistent/.moosey-cms.yaml"))

    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8000
    assert config.crypto.key == ""


def test_save_config_with_advanced(tmp_path):
    """Test saving config with advanced settings."""
    config_path = tmp_path / ".moosey-cms.yaml"

    config = CMSConfig(
        crypto=CryptoConfig(key="test-key"),
        image_cdn={"provider": "cloudflare", "base_url": "https://cdn.example.com"},
        sanitize={"allowed_tags": ["p", "a"]},
    )

    save_config(config, config_path)

    with open(config_path) as f:
        data = yaml.safe_load(f)

    assert "image_cdn" in data
    assert data["image_cdn"]["provider"] == "cloudflare"
    assert "sanitize" in data
    assert "image_processing" not in data  # None values not saved


def test_load_config_with_advanced(tmp_path):
    """Test loading config with advanced settings."""
    config_path = tmp_path / ".moosey-cms.yaml"

    data = {
        "server": {"host": "0.0.0.0", "port": 8000, "reload_delay": 0.25},
        "site": {"name": "My Site", "admin_prefix": "admin"},
        "crypto": {"key": "test-key"},
        "image_cdn": {"provider": "imgix", "base_url": "https://img.example.com"},
    }

    with open(config_path, "w") as f:
        yaml.dump(data, f)

    loaded = load_config(config_path)

    assert loaded.image_cdn is not None
    assert loaded.image_cdn["provider"] == "imgix"
    assert loaded.sanitize is None
