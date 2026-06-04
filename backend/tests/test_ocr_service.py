from pathlib import Path

import pytest

from app.services.ocr_service import (
    DisabledProvider,
    OCRException,
    OCRProvider,
    OCRService,
    SUPPORTED_IMAGE_SUFFIXES,
)


class FakeProvider(OCRProvider):
    def __init__(self, text: str):
        self.text = text

    def extract(self, image_path: Path) -> str:
        return self.text


def test_ocr_extracts_text_from_image(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"fake-image")

    text = OCRService(provider=FakeProvider("采购审批 OCR 文本")).extract_text(image_path)

    assert text == "采购审批 OCR 文本"


def test_ocr_returns_empty_on_no_text(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.jpg"
    image_path.write_bytes(b"fake-image")

    text = OCRService(provider=FakeProvider("")).extract_text(image_path)

    assert text == ""


def test_ocr_disabled_provider(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"fake-image")

    with pytest.raises(OCRException, match="disabled"):
        OCRService(provider=DisabledProvider()).extract_text(image_path)


def test_ocr_image_suffix_detection() -> None:
    assert SUPPORTED_IMAGE_SUFFIXES == {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
    }
