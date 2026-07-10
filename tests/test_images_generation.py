import pytest

pytest.importorskip("PIL")
from PIL import Image

from moosey_cms import images


def _write_test_image(path, size=(80, 120)):
    img = Image.new("RGB", size, "#f8fafc")
    img.save(path)


def test_aspect_crop_with_height_only_resizes(tmp_path):
    source = tmp_path / "portrait.jpg"
    target = tmp_path / "out.png"
    _write_test_image(source)

    images.generate(
        source,
        target,
        {
            "ar": "square",
            "fit": "cover",
            "focus": "center",
            "fmt": "png",
            "h": 32,
            "meta": "none",
        },
    )

    with Image.open(target) as img:
        assert img.size == (32, 32)


def test_face_focus_falls_back_when_no_face_detected(tmp_path, monkeypatch):
    source = tmp_path / "portrait.jpg"
    target = tmp_path / "out.png"
    img = Image.new("RGB", (80, 120), "#ef4444")
    for y in range(80, 120):
        for x in range(80):
            img.putpixel((x, y), (37, 99, 235))
    img.save(source)
    monkeypatch.setattr(images, "face_box_path", lambda img: None)

    images.generate(
        source,
        target,
        {
            "ar": "square",
            "fit": "cover",
            "focus": "face",
            "fmt": "png",
            "h": 40,
            "meta": "none",
        },
    )

    with Image.open(target) as img:
        assert img.size == (40, 40)
        r, g, b = img.getpixel((20, 5))[:3]
        assert r > 200 and g < 120 and b < 120


def test_tiny_face_box_is_not_plausible():
    assert not images._plausible_face_box((595, 1280, 91, 91), 1204, 1600)
    assert images._plausible_face_box((226, 175, 241, 241), 719, 1050)
