import asyncio

from moosey_cms import images


def test_filter_returns_original_without_pillow(monkeypatch):
    monkeypatch.setattr(images, "IMAGES_AVAILABLE", False)
    monkeypatch.setattr(images, "FACES_AVAILABLE", False)

    result = images.image_url_filter(
        "/static/photo.jpg", "test-key-no-pillow", w=400
    )

    assert result == "/static/photo.jpg"


def test_filter_returns_original_for_face_without_opencv(monkeypatch):
    monkeypatch.setattr(images, "IMAGES_AVAILABLE", True)
    monkeypatch.setattr(images, "FACES_AVAILABLE", False)

    result = images.image_url_filter(
        "/static/face.jpg", "test-key-no-opencv", w=400, focus="face"
    )

    assert result == "/static/face.jpg"


def test_filter_builds_url_when_capability_is_available(monkeypatch):
    monkeypatch.setattr(images, "IMAGES_AVAILABLE", True)
    monkeypatch.setattr(images, "FACES_AVAILABLE", True)

    result = images.image_url_filter(
        "/static/face-capable.jpg", "test-key-face-capable", w=400, focus="face"
    )

    assert result.startswith("/__moosey/img/")


def test_generate_task_is_noop_when_capability_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(images, "IMAGES_AVAILABLE", False)
    called = False

    def generate(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(images, "generate", generate)
    asyncio.run(
        images._generate_image(
            tmp_path / "source.jpg",
            tmp_path / "target.webp",
            {"w": 400},
        )
    )

    assert called is False
