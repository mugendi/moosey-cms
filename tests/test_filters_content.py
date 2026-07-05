from moosey_cms.filters import embed, headings, toc_from_html, gravatar


class TestEmbed:
    def test_youtube(self):
        result = embed("https://youtu.be/dQw4w9WgXcQ")
        assert "youtube.com/embed/dQw4w9WgXcQ" in result
        assert "<iframe" in result

    def test_youtube_full_url(self):
        result = embed("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert "youtube.com/embed/dQw4w9WgXcQ" in result

    def test_vimeo(self):
        result = embed("https://vimeo.com/12345678")
        assert "player.vimeo.com/video/12345678" in result

    def test_twitter(self):
        result = embed("https://twitter.com/user/status/123456789")
        assert "twitter-tweet" in result

    def test_gist(self):
        result = embed("https://gist.github.com/user/abc123")
        assert "gist.github.com" in result

    def test_codepen(self):
        result = embed("https://codepen.io/user/pen/abc123")
        assert "codepen.io" in result

    def test_unknown_url_fallback(self):
        result = embed("https://example.com/page")
        assert '<a href="https://example.com/page"' in result

    def test_empty_returns_empty(self):
        assert embed("") == ""

    def test_none_returns_empty(self):
        assert embed(None) == ""


class TestHeadings:
    def test_extracts_headings(self, sample_html):
        result = headings(sample_html["headings"])
        assert ("a", "A", 2) in result
        assert ("b", "B", 3) in result
        assert len(result) == 3

    def test_empty_returns_empty_list(self):
        assert headings("") == []

    def test_none_returns_empty_list(self):
        assert headings(None) == []

    def test_custom_levels(self, sample_html):
        result = headings(sample_html["headings"], min_level=3, max_level=3)
        assert len(result) == 1
        assert result[0][2] == 3


class TestTocFromHtml:
    def test_generates_nav(self, sample_html):
        result = toc_from_html(sample_html["headings"])
        assert "<nav" in result
        assert "<ul>" in result
        assert "A" in result
        assert "B" in result
        assert "C" not in result

    def test_empty_returns_empty(self):
        assert toc_from_html("") == ""

    def test_none_returns_empty(self):
        assert toc_from_html(None) == ""

    def test_custom_class(self, sample_html):
        result = toc_from_html(sample_html["headings"], klass="custom-toc")
        assert 'class="custom-toc"' in result


class TestGravatar:
    def test_basic(self):
        result = gravatar("test@example.com")
        assert "gravatar.com/avatar/" in result
        assert "s=80" in result
        assert "d=404" in result
        assert "r=g" in result

    def test_custom_size(self):
        result = gravatar("test@example.com", size=200)
        assert "s=200" in result

    def test_email_normalized(self):
        result1 = gravatar("Test@Example.com")
        result2 = gravatar("test@example.com")
        assert result1 == result2

    def test_empty_returns_empty(self):
        assert gravatar("") == ""

    def test_none_returns_empty(self):
        assert gravatar(None) == ""
