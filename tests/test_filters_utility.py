from unittest.mock import patch, Mock
from pathlib import Path

from moosey_cms.filters import (
    default_if_none, yesno, pluralize,
    absolute_url, cache_bust, inline,
)


class TestDefaultIfNone:
    def test_none_returns_default(self):
        assert default_if_none(None) == ""

    def test_none_custom_default(self):
        assert default_if_none(None, default="N/A") == "N/A"

    def test_value_returned(self):
        assert default_if_none("hello") == "hello"

    def test_falsy_not_none(self):
        assert default_if_none(0) == 0
        assert default_if_none(False) is False
        assert default_if_none("") == ""


class TestYesno:
    def test_true(self):
        assert yesno(True) == "Yes"

    def test_false(self):
        assert yesno(False) == "No"

    def test_custom_strings(self):
        assert yesno(True, yes="Yep", no="Nope") == "Yep"
        assert yesno(False, yes="Yep", no="Nope") == "Nope"

    def test_truthy_values(self):
        assert yesno(1) == "Yes"
        assert yesno("non-empty") == "Yes"


class TestPluralize:
    def test_singular(self):
        assert pluralize("review", 1) == "review"

    def test_plural_adds_s(self):
        assert pluralize("review", 2) == "reviews"

    def test_custom_plural(self):
        assert pluralize("child", 2, plural="children") == "children"


class TestAbsoluteUrl:
    def test_relative_with_base_url(self):
        context = {"site_data": {"web": {"site_url": "https://example.com"}}}
        assert absolute_url(context, "/page") == "https://example.com/page"

    def test_absolute_unchanged(self):
        context = {}
        url = "https://other.com/page"
        assert absolute_url(context, url) == url

    def test_hash_only_unchanged(self):
        context = {}
        assert absolute_url(context, "#section") == "#section"

    def test_empty_returns_empty(self):
        assert absolute_url({}, "") == ""

    def test_none_returns_empty(self):
        assert absolute_url({}, None) == ""

    def test_with_request_base(self):
        req = Mock(base_url="http://localhost:8000/")
        context = {"request": req}
        assert absolute_url(context, "/page") == "http://localhost:8000/page"

    def test_explicit_base_url_overrides(self):
        context = {"site_data": {"site_url": "https://example.com"}}
        result = absolute_url(context, "/page", base_url="https://override.com")
        assert result == "https://override.com/page"


class TestCacheBust:
    def test_no_request_returns_url(self):
        context = {}
        assert cache_bust(context, "/static/style.css") == "/static/style.css"

    def test_no_static_dir_returns_url(self):
        req = Mock(app=Mock(state=Mock(moosey_static_dir=None)))
        context = {"request": req}
        assert cache_bust(context, "/static/style.css") == "/static/style.css"

    def test_file_not_found_returns_url(self, tmp_path):
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        req = Mock(app=Mock(state=Mock(moosey_static_dir=static_dir)))
        context = {"request": req}
        assert cache_bust(context, "/static/nonexistent.css") == "/static/nonexistent.css"

    def test_mtime_mode(self, tmp_path):
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        css = static_dir / "style.css"
        css.write_text("body {}")
        req = Mock(app=Mock(state=Mock(moosey_static_dir=static_dir)))
        context = {"request": req}
        result = cache_bust(context, "/static/style.css")
        assert "/static/style.css?v=" in result

    def test_sha8_mode(self, tmp_path):
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        css = static_dir / "style.css"
        css.write_text("body {}")
        req = Mock(app=Mock(state=Mock(moosey_static_dir=static_dir)))
        context = {"request": req}
        result = cache_bust(context, "/static/style.css", mode="sha8")
        assert "/static/style.css?v=" in result

    def test_empty_url_returns_empty(self):
        assert cache_bust({}, "") == ""


class TestInline:
    def test_no_request_returns_empty(self):
        assert inline({}, "/static/file.txt") == ""

    def test_no_static_dir_returns_empty(self):
        req = Mock(app=Mock(state=Mock(moosey_static_dir=None)))
        context = {"request": req}
        assert inline(context, "/static/file.txt") == ""

    def test_file_not_found_returns_empty(self, tmp_path):
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        req = Mock(app=Mock(state=Mock(moosey_static_dir=static_dir)))
        context = {"request": req}
        assert inline(context, "/static/nonexistent.txt") == ""

    def test_text_file_contents(self, tmp_path):
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        txt = static_dir / "hello.txt"
        txt.write_text("Hello World")
        req = Mock(app=Mock(state=Mock(moosey_static_dir=static_dir)))
        context = {"request": req}
        assert inline(context, "/static/hello.txt") == "Hello World"

    def test_data_uri_encode(self, tmp_path):
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        svg = static_dir / "icon.svg"
        svg.write_text("<svg></svg>")
        req = Mock(app=Mock(state=Mock(moosey_static_dir=static_dir)))
        context = {"request": req}
        result = inline(context, "/static/icon.svg", encode="data-uri")
        assert result.startswith("data:")
        assert "base64" in result

    def test_empty_path_returns_empty(self):
        assert inline({}, "") == ""
