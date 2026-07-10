from unittest.mock import patch

from moosey_cms.filters import (
    strip_html, strip_comments, minify_html,
    sanitize, get_sanitize_config, markdown,
)


class TestStripHtml:
    def test_simple(self):
        assert strip_html("<p>Hello world</p>") == "Hello world"

    def test_complex(self, sample_html):
        result = strip_html(sample_html["complex"])
        assert "Title" in result
        assert "Body text" in result
        assert "<div>" not in result

    def test_comment_removed(self, sample_html):
        result = strip_html(sample_html["comment"])
        assert "visible" in result
        assert "comment" not in result

    def test_empty_returns_empty(self):
        assert strip_html("") == ""

    def test_none_returns_empty(self):
        assert strip_html(None) == ""


class TestStripComments:
    def test_comment_removed(self, sample_html):
        result = strip_comments(sample_html["comment"])
        assert "visible" in result
        assert "comment" not in result

    def test_disabled(self, sample_html):
        result = strip_comments(sample_html["comment"], enabled=False)
        assert "comment" in result

    def test_empty_returns_empty(self):
        assert strip_comments("") == ""

    def test_none_returns_none(self):
        assert strip_comments(None) is None

    def test_disabled_without_text(self):
        assert strip_comments("", enabled=False) == ""


class TestMinifyHtml:
    def test_basic(self, sample_html):
        result = minify_html(sample_html["minify"])
        assert "\n" not in result
        assert "  " not in result
        assert "<div><p>text</p></div>" in result

    def test_preserves_pre_and_code_whitespace(self):
        html = (
            "<div>\n"
            "  <pre>line 1\n    line 2\n\tline 3</pre>\n"
            "  <code>  x = 1\n  y = 2  </code>\n"
            "</div>"
        )

        result = minify_html(html)

        assert "line 1\n    line 2\n\tline 3" in result
        assert "  x = 1\n  y = 2  " in result
        assert result.startswith("<div><pre>")

    def test_preserves_textarea_whitespace(self):
        html = "<form>\n<textarea>hello\n  world\n</textarea>\n</form>"

        result = minify_html(html)

        assert "<textarea>hello\n  world\n</textarea>" in result

    def test_does_not_minify_inline_script_by_default(self):
        script = "const value = 'a    b';\nif (value) {\n  console.log(value);\n}"
        html = f"<div>\n<script>{script}</script>\n</div>"

        result = minify_html(html)

        assert f"<script>{script}</script>" in result

    def test_preserves_json_ld_script_content(self):
        json_ld = (
            '{\n'
            '  "@context": "https://schema.org",\n'
            '  "@type": "Organization"\n'
            '}'
        )
        html = f'<script type="application/ld+json">{json_ld}</script>'

        result = minify_html(html)

        assert json_ld in result

    def test_keeps_comments_for_strip_comments_filter(self):
        html = "<div>\n<!-- keep until strip_comments runs -->\n<p>text</p>\n</div>"

        result = minify_html(html)

        assert "<!-- keep until strip_comments runs -->" in result
        assert strip_comments(result) == "<div><p>text</p></div>"

    def test_returns_original_html_when_minifier_fails(self):
        html = "<div>\n  <p>text</p>\n</div>"

        with patch("moosey_cms.filters._html_minifier.minify",
                   side_effect=ValueError("bad html")):
            assert minify_html(html) == html

    def test_returns_original_html_when_minifier_unavailable(self):
        html = "<div>\n  <p>text</p>\n</div>"

        with patch("moosey_cms.filters._html_minifier", None):
            assert minify_html(html) == html

    def test_disabled(self):
        html = "<div>  text  </div>"
        assert minify_html(html, enabled=False) == html

    def test_empty_returns_empty(self):
        assert minify_html("") == ""

    def test_none_returns_none(self):
        assert minify_html(None) is None


class TestSanitize:
    def test_removes_script_tags(self):
        result = sanitize("<p>hello</p><script>alert(1)</script>")
        assert "hello" in result
        assert "<script>" not in result

    def test_allows_default_tags(self):
        result = sanitize("<p>hello <strong>world</strong></p>")
        assert "<p>" in result
        assert "<strong>" in result

    def test_strips_unknown_tags(self):
        result = sanitize("<p>hello</p><marquee>world</marquee>")
        assert "hello" in result
        assert "marquee" not in result

    def test_allows_img_with_attrs(self):
        result = sanitize('<img src="https://example.com/img.jpg" alt="test">')
        assert "<img" in result

    def test_strips_onclick(self):
        result = sanitize('<p onclick="alert(1)">hello</p>')
        assert "onclick" not in result

    def test_empty_returns_empty(self):
        assert sanitize("") == ""

    def test_custom_tags(self):
        result = sanitize("<custom>hello</custom>", tags=["custom"])
        assert "<custom>" in result

    def test_styles_without_bleach_css(self):
        result = sanitize('<p style="color:red">hello</p>', styles=["color"])
        assert "style" not in result


class TestGetSanitizeConfig:
    def test_default(self):
        cfg = get_sanitize_config({})
        assert cfg is not None
        assert cfg["auto"] is True
        assert "bleach_kwargs" in cfg

    def test_disabled(self):
        cfg = get_sanitize_config({"sanitize": False})
        assert cfg is None

    def test_custom_tags(self):
        cfg = get_sanitize_config({"sanitize": {"tags": ["p"]}})
        assert cfg["bleach_kwargs"]["tags"] == ["p"]

    def test_none_site_data(self):
        cfg = get_sanitize_config(None)
        assert cfg is not None


class TestMarkdown:
    def test_basic(self):
        result = markdown("**bold**")
        assert "<strong>bold</strong>" in result

    def test_inline_strips_paragraph(self):
        result = markdown("**bold**", inline=True)
        assert not result.startswith("<p>")
        assert "<strong>bold</strong>" in result

    def test_empty_returns_empty(self):
        assert markdown("") == ""

    def test_none_returns_empty(self):
        assert markdown(None) == ""
