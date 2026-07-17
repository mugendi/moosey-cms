"""Load Moosey's built-in frontmatter field registry and project overrides."""
from __future__ import annotations
import logging
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Callable
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)
BUILTIN_REGISTRY = Path(__file__).with_name("fields.yaml")
OVERRIDE_PATH = Path(".moosey") / "frontmatter_fields.yaml"
DEFAULT_FACTORIES: dict[str, Callable[[], Any]] = {
    "today": lambda: date.today().isoformat(),
}

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

def _set_metadata_path(
    metadata: dict[str, Any],
    path: str,
    value: Any,
    *,
    replace_scalar_parent: bool = False,
    scalar_parent_key: str | None = None,
) -> bool:
    parts = path.split(".")
    if not parts or any(not part for part in parts):
        return False

    current = metadata
    for part in parts[:-1]:
        parent = current.get(part)
        if parent is None:
            current[part] = {}
        elif not isinstance(parent, dict):
            if not replace_scalar_parent:
                return False
            current[part] = {}
            if scalar_parent_key:
                current[part][scalar_parent_key] = parent
        current = current[part]

    current[parts[-1]] = deepcopy(value)
    return True

def build_initial_frontmatter(registry: dict[str, Any]) -> dict[str, Any]:
    """Resolve safe defaults for fields included in newly created files."""
    metadata: dict[str, Any] = {}
    fields = registry.get("fields", {})
    if not isinstance(fields, dict):
        return metadata

    for name, field in fields.items():
        if not isinstance(field, dict) or not field.get("is_basic_field"):
            continue

        if "default" in field:
            value = deepcopy(field["default"])
        elif "default_factory" in field:
            factory_name = field["default_factory"]
            factory = DEFAULT_FACTORIES.get(factory_name)
            if factory is None:
                logger.warning(
                    "Skipping frontmatter field %s: unknown default factory %r",
                    name,
                    factory_name,
                )
                continue
            try:
                value = factory()
            except Exception as exc:
                logger.warning(
                    "Skipping frontmatter field %s: default factory %r failed: %s",
                    name,
                    factory_name,
                    exc,
                )
                continue
        else:
            continue

        path = field.get("path", name)
        if not isinstance(path, str) or not _set_metadata_path(
            metadata,
            path,
            value,
            replace_scalar_parent=field.get("replace_scalar_parent") is True,
            scalar_parent_key=field.get("scalar_parent_key"),
        ):
            logger.warning(
                "Skipping frontmatter field %s: invalid or incompatible path %r",
                name,
                path,
            )

    return metadata

def load_frontmatter_fields(
    content_dir: Path,
    current_dir: Path | None = None,
) -> dict[str, Any]:
    """Load built-ins and hierarchical overrides for a content directory.

    Overrides are merged from the project root down to ``current_dir`` so the
    closest ``.moosey/frontmatter_fields.yaml`` takes precedence.
    """
    registry = _read_yaml(BUILTIN_REGISTRY)
    content_root = Path(content_dir).resolve()
    project_root = content_root.parent
    scope = Path(current_dir).resolve() if current_dir is not None else content_root


    if scope != content_root and content_root not in scope.parents:
        raise ValueError(f"Frontmatter field scope must be inside {content_root}: {scope}")

    directories = [project_root]
    relative_parts = scope.relative_to(content_root).parts

    directories.extend(
        content_root.joinpath(*relative_parts[:index])
        for index in range(len(relative_parts) + 1)
    )

    overrides = [directory / OVERRIDE_PATH for directory in directories]

    overrides.reverse()

    loaded_overrides: list[Path] = []
    for override in overrides:
        if override.is_file():
            try:
                registry =  _read_yaml(override)
                loaded_overrides.append(override)
                break
            except (OSError, ValueError) as exc:
                logger.warning("Ignoring invalid frontmatter field override %s: %s", override, exc)

    fields = registry.get("fields")

    if isinstance(fields, dict):
        for position, field in enumerate(fields.values()):
            if isinstance(field, dict):
                field.setdefault("order", position)
    registry["override_path"] = str(
        loaded_overrides[-1] if loaded_overrides else project_root / OVERRIDE_PATH
    )
    registry["override_paths"] = [str(path) for path in loaded_overrides]
    return registry
