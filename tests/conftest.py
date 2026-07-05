import pytest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from pathlib import Path


def make_context(request=None, site_data=None):
    return {"request": request, "site_data": site_data or {}}


def mock_request(static_dir="/fake/static", route_prefix="/__moosey/img/",
                 site_url="http://localhost:8000"):
    state = SimpleNamespace(
        moosey_static_dir=Path(static_dir),
        moosey_image_route_prefix=route_prefix,
        site_data={"site_url": site_url},
    )
    return SimpleNamespace(
        app=SimpleNamespace(state=state),
        base_url=site_url + "/",
    )


@pytest.fixture
def sample_dates():
    return {
        "normal": datetime(2026, 1, 13, 18, 0, 0),
        "midnight": datetime(2026, 6, 15, 0, 0, 0),
        "noon": datetime(2025, 12, 25, 12, 0, 0),
        "early": datetime(2026, 3, 5, 5, 30, 0),
        "ordinal_11": datetime(2026, 11, 11, 10, 0, 0),
        "ordinal_12": datetime(2026, 12, 12, 10, 0, 0),
        "ordinal_13": datetime(2026, 1, 13, 10, 0, 0),
        "ordinal_21": datetime(2026, 1, 21, 10, 0, 0),
        "ordinal_22": datetime(2026, 1, 22, 10, 0, 0),
        "ordinal_23": datetime(2026, 1, 23, 10, 0, 0),
        "ordinal_31": datetime(2026, 1, 31, 10, 0, 0),
        "date_only": date(2026, 7, 4),
    }


@pytest.fixture
def sample_html():
    return {
        "simple": "<p>Hello world</p>",
        "complex": '<div class="main"><h1 id="title">Title</h1><p>Body text</p></div>',
        "comment": "<!-- comment --><p>visible</p>",
        "minify": "<div>  \n  <p>text</p>  \n</div>",
        "headings": '<h1>Out</h1><h2 id="a">A</h2><h3 id="b">B</h3><h4>C</h4>',
    }


