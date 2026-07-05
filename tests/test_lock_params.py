from pathlib import Path
import tempfile

from moosey_cms.helpers import build_lock_params_url, check_lock_params, get_directory_navigation


def _make_md_file(folder, name, frontmatter):
    """Write a markdown file with YAML frontmatter."""
    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, dict):
            lines.append(f"{k}:")
            for sk, sv in v.items():
                if isinstance(sv, bool):
                    lines.append(f"  {sk}: {'true' if sv else 'false'}")
                else:
                    lines.append(f"  {sk}: {sv}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append("# Content")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text("\n".join(lines))


class TestBuildLockParamsUrl:
    def test_basic(self):
        result = build_lock_params_url("/blog/title", {"id": "12345678", "rand_val": "allow-access"})
        assert result == "/blog/title?id=12345678&rand_val=allow-access"

    def test_special_params_excluded(self):
        result = build_lock_params_url("/blog/title", {
            "_sitemap_list_": True,
            "_fileset_list_": True,
            "id": "42",
        })
        assert "id=42" in result
        assert "_sitemap_list_" not in result
        assert "_fileset_list_" not in result

    def test_no_params(self):
        assert build_lock_params_url("/page", {}) == "/page"

    def test_only_special_params(self):
        result = build_lock_params_url("/page", {"_sitemap_list_": True})
        assert result == "/page"

    def test_values_stringified(self):
        result = build_lock_params_url("/page", {"id": 42, "active": True})
        assert "id=42" in result
        assert "active=True" in result


class TestCheckLockParams:
    def test_exact_match(self):
        assert check_lock_params({"id": "42"}, {"id": "42"})

    def test_missing_param(self):
        assert not check_lock_params({"id": "42"}, {})

    def test_wrong_value(self):
        assert not check_lock_params({"id": "42"}, {"id": "99"})

    def test_extra_query_params_allowed(self):
        assert check_lock_params({"id": "42"}, {"id": "42", "extra": "foo"})

    def test_empty_lock_params_always_true(self):
        assert check_lock_params({}, {"anything": "goes"})
        assert check_lock_params({}, {})

    def test_only_special_params_always_true(self):
        assert check_lock_params({"_sitemap_list_": True}, {})
        assert check_lock_params(
            {"_sitemap_list_": True, "_fileset_list_": True}, {}
        )

    def test_special_params_ignored_in_check(self):
        assert check_lock_params(
            {"_sitemap_list_": True, "id": "x"}, {"id": "x"}
        )

    def test_none_query_params(self):
        assert not check_lock_params({"id": "42"}, {})

    def test_values_compared_as_strings(self):
        assert check_lock_params({"id": 42}, {"id": "42"})


class TestNavExcludesWithoutFilesetList:
    def _make_page(self, tmp_path, lock_params):
        folder = tmp_path / "content"
        _make_md_file(folder, "page.md", {
            "title": "Test Page",
            "visible": True,
            **({"lock_params": lock_params} if lock_params is not None else {}),
        })
        return folder

    def test_no_lock_params_shows(self, tmp_path):
        folder = self._make_page(tmp_path, None)
        items = get_directory_navigation(folder, "/page", folder, "production")
        assert len(items) == 1

    def test_empty_lock_params_shows(self, tmp_path):
        folder = self._make_page(tmp_path, {})
        items = get_directory_navigation(folder, "/page", folder, "production")
        assert len(items) == 1

    def test_only_special_lock_params_shows(self, tmp_path):
        folder = self._make_page(tmp_path, {"_fileset_list_": True})
        items = get_directory_navigation(folder, "/page", folder, "production")
        assert len(items) == 1

    def test_fileset_list_true_shows(self, tmp_path):
        folder = self._make_page(tmp_path, {"_fileset_list_": True, "id": "42"})
        items = get_directory_navigation(folder, "/page", folder, "production")
        assert len(items) == 1
        assert "id=42" in items[0]["url"]

    def test_fileset_list_false_hides(self, tmp_path):
        folder = self._make_page(tmp_path, {"_fileset_list_": False, "id": "42"})
        items = get_directory_navigation(folder, "/page", folder, "production")
        assert len(items) == 0

    def test_no_fileset_list_hides(self, tmp_path):
        folder = self._make_page(tmp_path, {"id": "42"})
        items = get_directory_navigation(folder, "/page", folder, "production")
        assert len(items) == 0
