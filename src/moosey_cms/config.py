"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import yaml

from .crypto import generate_key

CONFIG_FILENAME = ".moosey-cms.yaml"


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    reload_delay: float = 0.25


@dataclass
class AdminConfig:
    prefix: str = "admin/content"
    templates: str = "admin"


@dataclass
class SiteConfig:
    name: str = "My Site"
    admin: AdminConfig= field(default_factory=AdminConfig)


@dataclass
class CryptoConfig:
    key: str = ""


@dataclass
class CMSConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    site: SiteConfig = field(default_factory=SiteConfig)
    crypto: CryptoConfig = field(default_factory=CryptoConfig)

    # Advanced configs (optional)
    image_cdn: Optional[dict] = None
    image_processing: Optional[dict] = None
    sanitize: Optional[dict] = None


def load_config(config_path: Optional[Path] = None) -> CMSConfig:
    """Load config from .moosey-cms.yaml, return defaults if not found."""
    if config_path is None:
        config_path = Path(CONFIG_FILENAME)

    if not config_path.exists():
        return CMSConfig()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    # Parse nested configs
    server_data = data.get("server", {})
    site_data = data.get("site", {})
    crypto_data = data.get("crypto", {})

    return CMSConfig(
        server=ServerConfig(**server_data),
        site=SiteConfig(**site_data),
        crypto=CryptoConfig(**crypto_data),
        image_cdn=data.get("image_cdn"),
        image_processing=data.get("image_processing"),
        sanitize=data.get("sanitize"),
    )


def save_config(config: CMSConfig, config_path: Optional[Path] = None):
    """Save config to .moosey-cms.yaml (no comments)."""
    if config_path is None:
        config_path = Path(CONFIG_FILENAME)

    data = {
        "server": asdict(config.server),
        "site": asdict(config.site),
        "crypto": asdict(config.crypto),
    }

    # Add advanced configs only if set
    if config.image_cdn is not None:
        data["image_cdn"] = config.image_cdn
    if config.image_processing is not None:
        data["image_processing"] = config.image_processing
    if config.sanitize is not None:
        data["sanitize"] = config.sanitize

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
