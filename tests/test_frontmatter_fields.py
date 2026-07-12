from pathlib import Path

from moosey_cms.frontmatter import load_frontmatter_fields


def test_builtin_registry_contains_runtime_fields(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    registry = load_frontmatter_fields(content)
    fields = registry["fields"]

    for name in ("title", "template", "draft", "lock_params", "visible", "sitemap_exclude", "feed", "canonical_url"):
        assert name in fields
    assert fields["draft"]["default"] is False
    assert fields["tags"]["default"] == []
    assert fields["sitemap_priority"]["path"] == "sitemap.priority"
    assert fields["sitemap_priority"]["replace_scalar_parent"] is True


def test_project_registry_is_discovered_and_deep_merged(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    config = tmp_path / ".moosey"
    config.mkdir()
    (config / "frontmatter_fields.yaml").write_text(
        """fields:
  draft:
    default: true
  client:
    label: Client
    type: text
    default: ''
    group: Projects
"""
    )

    fields = load_frontmatter_fields(content)["fields"]
    assert fields["draft"]["default"] is True
    assert fields["draft"]["type"] == "boolean"
    assert fields["client"]["group"] == "Projects"


def test_registry_reports_automatic_override_path(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    registry = load_frontmatter_fields(content)
    assert Path(registry["override_path"]) == tmp_path / ".moosey" / "frontmatter_fields.yaml"
