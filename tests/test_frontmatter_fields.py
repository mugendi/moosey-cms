from datetime import date
from pathlib import Path

from moosey_cms.frontmatter import build_initial_frontmatter, load_frontmatter_fields
from moosey_cms.frontmatter import fields as fields_module


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
    for name in ("published", "updated", "created"):
        assert fields[name]["path"] == f"date.{name}"
        assert fields[name]["replace_scalar_parent"] is True
        assert fields[name]["scalar_parent_key"] == "published"
    date_fields = ("date", "published", "updated", "created")
    assert [fields[name]["order"] for name in date_fields] == sorted(
        fields[name]["order"] for name in date_fields
    )


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
    assert fields["client"]["order"] > fields["canonical_url"]["order"]


def test_registry_reports_automatic_override_path(tmp_path):
    content = tmp_path / "content"
    content.mkdir()
    registry = load_frontmatter_fields(content)
    assert Path(registry["override_path"]) == tmp_path / ".moosey" / "frontmatter_fields.yaml"


def test_closest_content_registry_takes_precedence(tmp_path):
    content = tmp_path / "content"
    blog = content / "blog"
    blog.mkdir(parents=True)

    project_config = tmp_path / ".moosey"
    project_config.mkdir()
    (project_config / "frontmatter_fields.yaml").write_text(
        "fields:\n  author:\n    default: Project author\n  category:\n    type: text\n",
        encoding="utf-8",
    )
    content_config = content / ".moosey"
    content_config.mkdir()
    (content_config / "frontmatter_fields.yaml").write_text(
        "fields:\n  author:\n    default: Content author\n",
        encoding="utf-8",
    )
    blog_config = blog / ".moosey"
    blog_config.mkdir()
    (blog_config / "frontmatter_fields.yaml").write_text(
        "fields:\n  author:\n    default: Blog author\n  category:\n    type: select\n",
        encoding="utf-8",
    )

    registry = load_frontmatter_fields(content, blog)

    assert registry["fields"]["author"]["default"] == "Blog author"
    assert registry["fields"]["category"]["type"] == "select"
    assert registry["override_path"] == str(blog_config / "frontmatter_fields.yaml")
    assert registry["override_paths"] == [
        str(project_config / "frontmatter_fields.yaml"),
        str(content_config / "frontmatter_fields.yaml"),
        str(blog_config / "frontmatter_fields.yaml"),
    ]


def test_registry_scope_must_be_inside_content_root(tmp_path):
    content = tmp_path / "content"
    content.mkdir()

    try:
        load_frontmatter_fields(content, tmp_path / "elsewhere")
    except ValueError as exc:
        assert "must be inside" in str(exc)
    else:
        raise AssertionError("Expected an out-of-root scope to be rejected")


def test_initial_frontmatter_resolves_factories_and_dotted_paths():
    registry = {
        "fields": {
            "title": {"default": "New post", "is_basic_field": True},
            "published": {
                "path": "date.published",
                "default_factory": "today",
                "is_basic_field": True,
            },
            "advanced": {"default": "not included", "is_basic_field": False},
        }
    }

    metadata = build_initial_frontmatter(registry)

    assert metadata == {
        "title": "New post",
        "date": {"published": date.today().isoformat()},
    }


def test_initial_frontmatter_skips_unknown_and_failing_factories(
    monkeypatch, caplog
):
    def fail():
        raise RuntimeError("factory failed")

    monkeypatch.setitem(fields_module.DEFAULT_FACTORIES, "broken", fail)
    registry = {
        "fields": {
            "unknown": {
                "default_factory": "not_registered",
                "is_basic_field": True,
            },
            "broken": {
                "default_factory": "broken",
                "is_basic_field": True,
            },
            "valid": {"default": "kept", "is_basic_field": True},
        }
    }

    metadata = build_initial_frontmatter(registry)

    assert metadata == {"valid": "kept"}
    assert "unknown default factory" in caplog.text
    assert "factory failed" in caplog.text


def test_initial_frontmatter_skips_incompatible_dotted_path(caplog):
    registry = {
        "fields": {
            "date": {"default": "2026-01-01", "is_basic_field": True},
            "updated": {
                "path": "date.updated",
                "default_factory": "today",
                "is_basic_field": True,
            },
        }
    }

    metadata = build_initial_frontmatter(registry)

    assert metadata == {"date": "2026-01-01"}
    assert "incompatible path" in caplog.text
