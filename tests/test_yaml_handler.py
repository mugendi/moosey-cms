"""
Tests for moosey_cms.yaml_handler — YAML frontmatter round-trip preservation.

Verifies that ruamel.yaml-based handling preserves comments, formatting,
and correctly serializes all YAML types (nested dicts, lists, bools, etc).
"""

import pytest

from moosey_cms.yaml_handler import (
    build_markdown,
    dump_frontmatter,
    parse_frontmatter,
    split_frontmatter,
)


# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    def test_empty_string(self):
        result = parse_frontmatter("")
        assert dict(result) == {}

    def test_blank_string(self):
        result = parse_frontmatter("   \n  ")
        assert dict(result) == {}

    def test_simple_kv(self):
        raw = "title: Hello\norder: 5"
        result = parse_frontmatter(raw)
        assert result["title"] == "Hello"
        assert result["order"] == 5

    def test_list(self):
        raw = "tags:\n  - python\n  - fastapi"
        result = parse_frontmatter(raw)
        assert result["tags"] == ["python", "fastapi"]

    def test_nested_dict(self):
        raw = "date:\n  published: 2024-01-01\n  updated: 2024-06-01"
        result = parse_frontmatter(raw)
        # ruamel.yaml parses ISO dates as date objects
        published = result["date"]["published"]
        assert str(published) == "2024-01-01"
        updated = result["date"]["updated"]
        assert str(updated) == "2024-06-01"

    def test_bool(self):
        raw = "draft: true"
        result = parse_frontmatter(raw)
        assert result["draft"] is True

    def test_multiline_string(self):
        raw = "description: |\n  Line one\n  Line two"
        result = parse_frontmatter(raw)
        assert "Line one" in result["description"]

    def test_comments_preserved(self):
        raw = "# Post metadata\ntitle: Hello\n# Sort order\norder: 5"
        result = parse_frontmatter(raw)
        assert result["title"] == "Hello"
        assert result["order"] == 5
        # Verify comment is attached (ruamel preserves via .ca)
        assert hasattr(result, "ca")


# ---------------------------------------------------------------------------
# dump_frontmatter
# ---------------------------------------------------------------------------

class TestDumpFrontmatter:
    def test_empty_dict(self):
        result = dump_frontmatter({})
        assert result == ""

    def test_simple_kv(self):
        result = dump_frontmatter({"title": "Hello"})
        assert "title: Hello" in result

    def test_list(self):
        result = dump_frontmatter({"tags": ["a", "b"]})
        assert "- a" in result
        assert "- b" in result

    def test_nested_dict(self):
        result = dump_frontmatter({"date": {"published": "2024-01-01"}})
        # Must NOT be Python repr
        assert "published: '2024-01-01'" in result or "published: 2024-01-01" in result
        assert "{" not in result  # no Python dict repr

    def test_bool(self):
        result = dump_frontmatter({"draft": True})
        assert "true" in result

    def test_bool_false(self):
        result = dump_frontmatter({"draft": False})
        assert "false" in result

    def test_number(self):
        result = dump_frontmatter({"order": 5, "weight": 2.5})
        assert "order: 5" in result
        assert "weight: 2.5" in result


# ---------------------------------------------------------------------------
# build_markdown
# ---------------------------------------------------------------------------

class TestBuildMarkdown:
    def test_with_meta_and_body(self):
        result = build_markdown({"title": "Hi"}, "Body content.")
        assert result.startswith("---\n")
        assert "title: Hi" in result
        assert result.endswith("Body content.\n")

    def test_empty_meta(self):
        result = build_markdown({}, "Body only.")
        assert result.startswith("\n") or result.startswith("Body")
        assert "---" not in result

    def test_nested_dict_serialized_correctly(self):
        meta = {
            "date": {"published": "2024-01-01", "updated": "2024-06-01"},
        }
        result = build_markdown(meta, "Body.")
        # Must NOT contain Python dict repr
        assert "published:" in result
        assert "{" not in result.split("---")[1]  # no Python repr in frontmatter

    def test_comments_preserved_with_original(self):
        original_fm = "# Post title\ntitle: Original\n# Sort order\norder: 1"
        meta = {"title": "Updated", "order": 5}
        result = build_markdown(meta, "Body.", original_fm=original_fm)
        # Comments should be preserved
        assert "# Post title" in result
        assert "# Sort order" in result
        # Values should be updated
        assert "title: Updated" in result
        assert "order: 5" in result

    def test_new_key_added_without_comment(self):
        original_fm = "title: Hello"
        meta = {"title": "Hello", "new_key": "value"}
        result = build_markdown(meta, "Body.", original_fm=original_fm)
        assert "new_key: value" in result

    def test_removed_key_drops_comment(self):
        """When merge source doesn't include a key, the original value is preserved."""
        original_fm = "# Sort order\norder: 1\ntitle: Hello"
        meta = {"title": "Hello"}  # order not sent
        result = build_markdown(meta, "Body.", original_fm=original_fm)
        assert "title: Hello" in result
        # order is preserved from original (not dropped)
        assert "order: 1" in result

    def test_no_original_fresh_serialization(self):
        meta = {"title": "Fresh", "tags": ["a", "b"], "draft": False}
        result = build_markdown(meta, "Content.", original_fm=None)
        assert "title: Fresh" in result
        assert "- a" in result
        assert "draft: false" in result

    def test_empty_body(self):
        result = build_markdown({"title": "Hi"}, "")
        assert "title: Hi" in result

    def test_body_multiline(self):
        result = build_markdown({"title": "Hi"}, "Line 1\n\nLine 2\n")
        assert "Line 1" in result
        assert "Line 2" in result


# ---------------------------------------------------------------------------
# split_frontmatter
# ---------------------------------------------------------------------------

class TestSplitFrontmatter:
    def test_no_frontmatter(self):
        fm, body = split_frontmatter("Just body text.")
        assert fm == ""
        assert body == "Just body text."

    def test_with_frontmatter(self):
        raw = "---\ntitle: Hi\norder: 1\n---\n\nBody here."
        fm, body = split_frontmatter(raw)
        assert "title: Hi" in fm
        assert "Body here." in body

    def test_empty_frontmatter(self):
        raw = "---\n---\n\nBody here."
        fm, body = split_frontmatter(raw)
        assert fm == ""
        assert "Body here." in body

    def test_long_dashes(self):
        raw = "----\ntitle: Hi\n----\n\nBody."
        fm, body = split_frontmatter(raw)
        assert "title: Hi" in fm
        assert "Body." in body


# ---------------------------------------------------------------------------
# Round-trip: full file → parse → build → parse
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_full_roundtrip_preserves_data(self):
        original = "---\ntitle: Test Post\ntags:\n  - python\n  - fastapi\norder: 5\ndraft: false\n---\n\nHello world.\n"
        fm, body = split_frontmatter(original)
        meta = dict(parse_frontmatter(fm))
        rebuilt = build_markdown(meta, body)
        fm2, body2 = split_frontmatter(rebuilt)
        meta2 = dict(parse_frontmatter(fm2))
        assert meta2["title"] == "Test Post"
        assert meta2["tags"] == ["python", "fastapi"]
        assert meta2["order"] == 5
        assert meta2["draft"] is False

    def test_roundtrip_with_comments(self):
        original = (
            "# Post metadata\n"
            "title: Test Post\n"
            "# Sort order\n"
            "order: 5\n"
        )
        fm, body = split_frontmatter("---\n" + original + "\n---\n\nBody.\n")
        meta = dict(parse_frontmatter(fm))
        rebuilt = build_markdown(meta, body, original_fm=fm)
        assert "# Post metadata" in rebuilt
        assert "# Sort order" in rebuilt
        assert "title: Test Post" in rebuilt
        assert "order: 5" in rebuilt

    def test_roundtrip_nested_dict(self):
        original_fm = "date:\n  published: 2024-01-01\n  updated: 2024-06-01"
        meta = dict(parse_frontmatter(original_fm))
        result = build_markdown(meta, "Body.", original_fm=original_fm)
        fm, _ = split_frontmatter(result)
        parsed = dict(parse_frontmatter(fm))
        assert str(parsed["date"]["published"]) == "2024-01-01"
        assert str(parsed["date"]["updated"]) == "2024-06-01"
