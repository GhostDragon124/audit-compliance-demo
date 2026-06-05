from pathlib import Path

import pytest

from app.config import Settings
from app.services.document_parser import DocumentParser


class FakeOCRService:
    def __init__(self, text: str = "", error: Exception | None = None) -> None:
        self.text = text
        self.error = error
        self.calls: list[Path] = []

    def extract_text(self, image_path: Path) -> str:
        self.calls.append(image_path)
        if self.error:
            raise self.error
        return self.text


def test_ocr_success_returns_ocr_parsed(tmp_path: Path) -> None:
    image = tmp_path / "sample.png"
    image.write_bytes(b"fake")

    parsed = DocumentParser(ocr_service=FakeOCRService("OCR 文本")).parse(
        image,
        "sample.png",
    )

    assert parsed.status == "ocr_parsed"
    assert parsed.preview == "OCR 文本"
    assert parsed.error is None


def test_ocr_empty_text_returns_failed(tmp_path: Path) -> None:
    image = tmp_path / "sample.png"
    image.write_bytes(b"fake")

    parsed = DocumentParser(ocr_service=FakeOCRService(" ")).parse(
        image,
        "sample.png",
    )

    assert parsed.status == "failed"
    assert parsed.error == "No text detected in image"


def test_ocr_exception_does_not_crash_request(tmp_path: Path) -> None:
    image = tmp_path / "sample.png"
    image.write_bytes(b"fake")

    parsed = DocumentParser(ocr_service=FakeOCRService(error=RuntimeError("boom"))).parse(
        image,
        "sample.png",
    )

    assert parsed.status == "failed"
    assert parsed.preview == ""
    assert parsed.error == "boom"


@pytest.mark.asyncio
async def test_mixed_txt_and_failed_image_returns_partial_success(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.main.DocumentParser",
        lambda: DocumentParser(ocr_service=FakeOCRService(error=RuntimeError("OCR failed"))),
    )

    response = await client.post(
        "/api/analyze",
        data={"question": "混合 OCR"},
        files=[
            ("files", ("sample.png", b"fake", "image/png")),
            ("files", ("sample.txt", b"text ok", "text/plain")),
        ],
    )

    assert response.status_code == 200
    parsed = {item["filename"]: item for item in response.json()["parsed_files"]}
    assert parsed["sample.png"]["status"] == "failed"
    assert parsed["sample.txt"]["status"] == "parsed"


def test_disabled_ocr_provider_returns_controlled_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    image = tmp_path / "sample.png"
    image.write_bytes(b"fake")
    monkeypatch.setattr(
        "app.services.document_parser.get_settings",
        lambda: Settings(ocr_enable=False),
    )

    parsed = DocumentParser().parse(image, "sample.png")

    assert parsed.status == "failed"
    assert parsed.preview == ""
    assert parsed.error


def test_ocr_provider_not_reinitialized_for_every_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    created = []

    class CountingOCRService(FakeOCRService):
        def __init__(self, **kwargs) -> None:
            super().__init__("OCR 文本")
            self.kwargs = kwargs
            created.append(self)

    monkeypatch.setattr(
        "app.services.document_parser.OCRService",
        CountingOCRService,
    )
    parser = DocumentParser()
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"fake")
    second.write_bytes(b"fake")

    parser.parse(first, "first.png")
    parser.parse(second, "second.png")

    assert len(created) == 1
    assert len(created[0].calls) == 2
