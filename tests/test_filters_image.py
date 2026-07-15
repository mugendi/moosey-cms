import warnings
from unittest.mock import patch, Mock
from pathlib import Path

from moosey_cms.filters import (
    img_attrs, lazy_image,
    image_dimensions, dominant_color,
    image_cdn, image_cdn_ctx,
    image, image_url, responsive_image,
)


class TestImgAttrs:
    def test_basic(self):
        result = img_attrs("/img/test.jpg")
        assert 'src="/img/test.jpg"' in result
        assert 'loading="lazy"' in result
        assert 'decoding="async"' in result

    def test_with_dimensions(self):
        result = img_attrs("/img/test.jpg", width=800, height=600)
        assert 'width="800"' in result
        assert 'height="600"' in result

    def test_empty_returns_empty(self):
        assert img_attrs("") == ""

    def test_none_returns_empty(self):
        assert img_attrs(None) == ""


class TestLazyImage:
    def test_adds_lazy_attrs(self):
        result = lazy_image('<img src="test.jpg">')
        assert 'loading="lazy"' in result
        assert 'decoding="async"' in result

    def test_does_not_duplicate(self):
        result = lazy_image('<img src="test.jpg" loading="eager">')
        assert result.count('loading=') == 1
        assert result == '<img src="test.jpg" loading="eager" decoding="async" referrerpolicy="no-referrer">'

    def test_bare_src_uses_img_attrs(self):
        result = lazy_image("test.jpg")
        assert 'src="test.jpg"' in result

    def test_empty_returns_empty(self):
        assert lazy_image("") == ""

    def test_none_returns_empty(self):
        assert lazy_image(None) == ""


class TestImageDimensions:
    def test_delegates_and_returns(self):
        with patch("moosey_cms.filters._image_dimensions_impl", return_value='width="800" height="600"') as mock:
            result = image_dimensions("/img/test.jpg")
            mock.assert_called_once_with("/img/test.jpg")
            assert result == 'width="800" height="600"'


class TestDominantColor:
    def test_delegates_and_returns(self):
        with patch("moosey_cms.filters._dominant_color_impl", return_value="#ff0000") as mock:
            req = Mock(app=Mock(state=Mock(moosey_static_dir=Path("/static"))))
            context = {"request": req}
            result = dominant_color(context, "/img/test.jpg")
            mock.assert_called_once_with("/img/test.jpg", default="#0b172a", static_dir=Path("/static"))
            assert result == "#ff0000"

    def test_delegates_with_default(self):
        with patch("moosey_cms.filters._dominant_color_impl", return_value="#0b172a") as mock:
            req = Mock(app=Mock(state=Mock(moosey_static_dir=Path("/static"))))
            context = {"request": req}
            result = dominant_color(context, "/img/test.jpg", default="#000000")
            mock.assert_called_once_with("/img/test.jpg", default="#000000", static_dir=Path("/static"))
            assert result == "#0b172a"

    def test_no_request_returns_default_via_impl(self):
        with patch("moosey_cms.filters._dominant_color_impl", return_value="#0b172a") as mock:
            context = {"request": None}
            result = dominant_color(context, "/img/test.jpg")
            mock.assert_called_once_with("/img/test.jpg", default="#0b172a", static_dir=None)
            assert result == "#0b172a"


class TestImageCdn:
    def test_delegates(self):
        with patch("moosey_cms.filters._image_cdn_impl", return_value="https://cdn.example.com/test.jpg?w=800") as mock:
            result = image_cdn("/test.jpg", w=800)
            mock.assert_called_once_with("/test.jpg", w=800)
            assert result == "https://cdn.example.com/test.jpg?w=800"


class TestImageCdnCtx:
    def test_delegates_with_site_data(self):
        with patch("moosey_cms.filters._image_cdn_impl", return_value="https://cdn.example.com/test.jpg") as mock:
            context = {"site_data": {"image_cdn": {"provider": "cloudflare", "base_url": "https://im.example.com"}}}
            result = image_cdn_ctx(context, "/test.jpg", w=800)
            mock.assert_called_once_with("/test.jpg", provider="cloudflare", base_url="https://im.example.com", w=800)
            assert result == "https://cdn.example.com/test.jpg"

    def test_no_site_data_uses_defaults(self):
        with patch("moosey_cms.filters._image_cdn_impl", return_value="/test.jpg") as mock:
            result = image_cdn_ctx({}, "/test.jpg")
            mock.assert_called_once_with("/test.jpg", provider="cloudflare", base_url=None)
            assert result == "/test.jpg"


class TestImage:
    def test_no_widths_returns_url(self):
        with patch("moosey_cms.filters._image_url_filter", return_value="/__moosey/img/test.jpg?w=800") as mock:
            mock_normalize = Mock(return_value="/test.jpg")
            mock_config = Mock()
            mock_config.crypto.key = "test-key"
            state = Mock(
                moosey_image_route_prefix="/__moosey/img/",
                normalize_static_path=mock_normalize,
                config=mock_config,
            )
            req = Mock(app=Mock(state=state))
            context = {"request": req}
            result = image(context, "/test.jpg", w=800)
            mock.assert_called_once_with("/test.jpg", crypto_key="test-key", _route_prefix="/__moosey/img/", w=800)
            assert result == "/__moosey/img/test.jpg?w=800"

    def test_with_widths_returns_tag(self):
        with patch("moosey_cms.filters._responsive_image_html", return_value='<img src="...">') as mock:
            mock_normalize = Mock(return_value="/test.jpg")
            state = Mock(
                moosey_image_route_prefix="/__moosey/img/",
                normalize_static_path=mock_normalize,
            )
            req = Mock(app=Mock(state=state))
            context = {"request": req}
            result = image(context, "/test.jpg", widths=(400, 800))
            mock.assert_called_once_with(
                "/test.jpg", _route_prefix="/__moosey/img/",
                widths=(400, 800), sizes="100vw",
                loading="lazy", decoding="async",
            )
            assert result == '<img src="...">'

    def test_no_request_uses_default_route(self):
        with patch("moosey_cms.filters._image_url_filter", return_value="/__moosey/img/test.jpg") as mock:
            result = image({}, "/test.jpg")
            mock.assert_called_once_with("/test.jpg", crypto_key="", _route_prefix="/__moosey/img/")
            assert result == "/__moosey/img/test.jpg"


class TestImageUrlDeprecated:
    def test_deprecation_warning(self):
        with patch("moosey_cms.filters.image") as mock_image:
            mock_image.return_value = "/__moosey/img/test.jpg"
            req = Mock(app=Mock(state=Mock(moosey_image_route_prefix="/__moosey/img/")))
            context = {"request": req}
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = image_url(context, "/test.jpg", w=800)
                assert len(w) == 1
                assert issubclass(w[0].category, DeprecationWarning)
                assert "image_url" in str(w[0].message)
            mock_image.assert_called_once_with(context, "/test.jpg", w=800)
            assert result == "/__moosey/img/test.jpg"

    def test_empty_src_returns_empty(self):
        assert image_url({}, "") == ""


class TestResponsiveImageDeprecated:
    def test_deprecation_warning(self):
        with patch("moosey_cms.filters.image") as mock_image:
            mock_image.return_value = '<img src="...">'
            req = Mock(app=Mock(state=Mock(moosey_image_route_prefix="/__moosey/img/")))
            context = {"request": req}
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = responsive_image(context, "/test.jpg")
                assert len(w) == 1
                assert issubclass(w[0].category, DeprecationWarning)
                assert "responsive_image" in str(w[0].message)
            mock_image.assert_called_once_with(
                context, "/test.jpg",
                widths=(400, 800, 1200, 1600),
                sizes="100vw", loading="lazy", decoding="async",
            )
            assert result == '<img src="...">'
