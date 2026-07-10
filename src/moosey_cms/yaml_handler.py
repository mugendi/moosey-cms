"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT

YAML frontmatter handler using ruamel.yaml.

Preserves comments, formatting, and handles all YAML types correctly.
Unlike the hand-rolled serializer or PyYAML's SafeDumper, ruamel.yaml
maintains the original structure of the frontmatter block when round-tripping
through read → edit → write cycles.
"""

from io import StringIO
from typing import Any, Optional, Tuple

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


def _make_yaml() -> YAML:
    """Create a configured YAML instance for round-trip editing."""
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096  # prevent line wrapping
    y.default_flow_style = False
    return y


_yaml = _make_yaml()


def parse_frontmatter(raw_fm: str) -> CommentedMap:
    """Parse a raw YAML frontmatter string into a CommentedMap.

    Parameters
    ----------
    raw_fm:
        The raw YAML text (without the ``---`` delimiters).

    Returns
    -------
    CommentedMap
        Parsed YAML with comments preserved. Empty dict if *raw_fm* is blank.
    """
    raw_fm = raw_fm.strip()
    if not raw_fm:
        return CommentedMap()
    return _yaml.load(StringIO(raw_fm))


def dump_frontmatter(data: dict) -> str:
    """Serialize a dict (or CommentedMap) to a YAML string.

    Parameters
    ----------
    data:
        The frontmatter metadata dict.

    Returns
    -------
    str
        YAML text (no ``---`` delimiters). Empty string if *data* is empty.
    """
    if not data:
        return ""
    buf = StringIO()
    _yaml.dump(data, buf)
    return buf.getvalue().strip()


def build_markdown(meta: dict, body: str, original_fm: Optional[str] = None) -> str:
    """Serialize frontmatter + body into a Markdown file string.

    Parameters
    ----------
    meta:
        Frontmatter metadata dict (from the API request).
    body:
        Markdown body content.
    original_fm:
        If provided, the raw YAML frontmatter text from the original file.
        When set, *meta* is merged into the parsed original so that comments
        and formatting from the source file are preserved.

    Returns
    -------
    str
        Complete Markdown file content with ``---`` delimiters.
    """
    if meta:
        if original_fm is not None and original_fm.strip():
            # Merge updated values into the original CommentedMap
            existing = parse_frontmatter(original_fm)
            _merge_dict(existing, meta)
            fm_text = dump_frontmatter(existing)
        else:
            fm_text = dump_frontmatter(meta)
        frontmatter_block = f"---\n{fm_text}\n---"
    else:
        frontmatter_block = ""

    # Ensure body ends with a single newline
    body_clean = body.rstrip("\n") + "\n" if body else "\n"

    if frontmatter_block:
        return frontmatter_block + "\n\n" + body_clean
    return "\n" + body_clean


def split_frontmatter(raw: str) -> Tuple[str, str]:
    """Split a full Markdown file into frontmatter text and body.

    Parameters
    ----------
    raw:
        The full file content (with ``---`` delimiters).

    Returns
    -------
    tuple[str, str]
        ``(frontmatter_text, body_text)`` — both stripped of leading/trailing
        whitespace. *frontmatter_text* is the raw YAML between delimiters
        (without ``---``). *body_text* is everything after the closing delimiter.
    """
    raw = raw.strip()
    if not raw.startswith("---"):
        return ("", raw)

    # Find the closing ---
    lines = raw.split("\n", 1)
    if len(lines) < 2:
        return ("", "")

    rest = lines[1]
    # Handle both --- and ---- (3+ dashes)
    close_idx = rest.find("\n---")
    if close_idx == -1:
        # Try at start of string
        if rest.startswith("---"):
            return ("", rest[3:].strip())
        return ("", raw)

    fm_text = rest[:close_idx].strip()
    body_text = rest[close_idx + 4:].strip()  # skip \n---
    return (fm_text, body_text)


def _merge_dict(target: CommentedMap, source: dict) -> None:
    """Recursively merge *source* into *target* (in-place).

    - New keys from *source* are added to *target*.
    - Existing keys are updated (preserving the comment on the target key).
    - Keys in *target* but not in *source* are left untouched.
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], CommentedMap) and isinstance(value, dict):
            _merge_dict(target[key], value)
        else:
            target[key] = value
