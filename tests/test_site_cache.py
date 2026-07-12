from datetime import datetime, timezone

from moosey_cms import site


def test_sitemap_xml_is_cached(monkeypatch, tmp_path):
    calls = 0

    def content_index(**_kwargs):
        nonlocal calls
        calls += 1
        return [{
            "url": "/about",
            "metadata": {},
            "updated": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }]

    monkeypatch.setattr(site, "get_content_index", content_index)
    config = {"default_priority": "0.5"}

    first = site._build_sitemap_xml(tmp_path, "production", config, "https://example.com")
    second = site._build_sitemap_xml(tmp_path, "production", config, "https://example.com")

    assert first == second
    assert calls == 1
    assert b"https://example.com/about" in first


def test_feed_xml_is_cached(monkeypatch, tmp_path):
    calls = 0

    def content_index(**_kwargs):
        nonlocal calls
        calls += 1
        return [{
            "url": "/news/item",
            "title": "Item",
            "description": "Description",
            "metadata": {},
            "published": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }]

    monkeypatch.setattr(site, "get_content_index", content_index)
    config = {"limit": 10}
    args = (
        tmp_path,
        "production",
        config,
        "https://example.com",
        "Example",
        "Example description",
        None,
    )

    first = site._build_feed_xml(*args)
    second = site._build_feed_xml(*args)

    assert first == second
    assert calls == 1
    assert b"https://example.com/news/item" in first
