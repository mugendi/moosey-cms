"""Load Moosey's built-in frontmatter field registry and project overrides."""
from __future__ import annotations
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)
BUILTIN_REGISTRY = Path(__file__).with_name("frontmatter_fields.yaml")
OVERRIDE_PATH = Path(".moosey") / "frontmatter_fields.yaml"

def _read_yaml(path: Path) -> dict[str, Any]:
    yaml = YAML(typ="safe")
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.load(stream) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Frontmatter registry must be a mapping: {path}")
    return data

def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result

def load_frontmatter_fields(content_dir: Path) -> dict[str, Any]:
    """Load built-ins and merge ``<content parent>/.moosey`` overrides."""
    registry = _read_yaml(BUILTIN_REGISTRY)
    override = Path(content_dir).resolve().parent / OVERRIDE_PATH
    if override.is_file():
        try:
            registry = _merge(registry, _read_yaml(override))
        except (OSError, ValueError) as exc:
            logger.warning("Ignoring invalid frontmatter field override %s: %s", override, exc)
    registry["override_path"] = str(override)
    return registry
