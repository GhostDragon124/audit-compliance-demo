from pathlib import Path

import pytest

from app.services.document_parser import DocumentParser

fitz = pytest.importorskip("fitz")


class SequencedOCRService:
    def __init__(self, texts: list[str]) -> None:
        self.texts = texts
        self.calls: list[Path] = []

    def extract_text(self, image_path: Path) -> str:
        self.calls.append(image_path)
        index = len(self.calls) - 1
        if index < len(self.texts):
            return self.texts[index]
        return f"page {index + 1}"


def _write_pdf(path: Path, pages: list[str | None]) -> None:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_text_pdf_does_not_trigger_ocr(tmp_path: Path) -> None:
    source = tmp_path / "text.pdf"
    _write_pdf(source, ["Text PDF procurement control " * 4])
    ocr = SequencedOCRService(["SHOULD_NOT_APPEAR"])

    parsed = DocumentParser(ocr_service=ocr).parse(source, "text.pdf")

    assert parsed.status == "parsed"
    assert "Text PDF procurement control" in parsed.preview
    assert ocr.calls == []


def test_scanned_pdf_triggers_ocr_fallback(tmp_path: Path) -> None:
    source = tmp_path / "scanned.pdf"
    _write_pdf(source, [None])
    ocr = SequencedOCRService(["OCR fallback text"])

    parsed = DocumentParser(ocr_service=ocr).parse(source, "scanned.pdf")

    assert parsed.status == "parsed"
    assert "[Page 1]" in parsed.preview
    assert "OCR fallback text" in parsed.preview
    assert len(ocr.calls) == 1


def test_scanned_pdf_preserves_page_order(tmp_path: Path) -> None:
    source = tmp_path / "ordered.pdf"
    _write_pdf(source, [None, None, None])
    ocr = SequencedOCRService(["first page", "second page", "third page"])

    parsed = DocumentParser(ocr_service=ocr).parse(source, "ordered.pdf")

    assert parsed.status == "parsed"
    assert parsed.preview.index("[Page 1]") < parsed.preview.index("[Page 2]")
    assert parsed.preview.index("[Page 2]") < parsed.preview.index("[Page 3]")
    assert parsed.preview.index("first page") < parsed.preview.index("second page")
    assert parsed.preview.index("second page") < parsed.preview.index("third page")


def test_mixed_pdf_handles_text_and_scanned_pages(tmp_path: Path) -> None:
    source = tmp_path / "mixed.pdf"
    _write_pdf(source, ["Text page has enough content " * 5, None])
    ocr = SequencedOCRService(["scanned page text"])

    parsed = DocumentParser(ocr_service=ocr).parse(source, "mixed.pdf")

    assert "Text page has enough content" in parsed.preview
    assert "scanned page text" in parsed.preview
    assert len(ocr.calls) == 1


def test_large_pdf_respects_page_limit(tmp_path: Path) -> None:
    source = tmp_path / "large_scanned.pdf"
    _write_pdf(source, [None] * 52)
    ocr = SequencedOCRService([f"page {number}" for number in range(1, 53)])

    parsed = DocumentParser(ocr_service=ocr).parse(source, "large_scanned.pdf")

    assert parsed.status == "parsed"
    assert len(ocr.calls) == DocumentParser.pdf_ocr_max_pages
    assert "[Page 50]" in parsed.preview
    assert "[Page 51]" not in parsed.preview


def test_pdf_partial_processing_is_reported(tmp_path: Path) -> None:
    source = tmp_path / "large_scanned.pdf"
    _write_pdf(source, [None] * 52)

    parsed = DocumentParser(ocr_service=SequencedOCRService(["text"] * 52)).parse(
        source,
        "large_scanned.pdf",
    )

    assert "partial" in parsed.preview.lower() or "仅处理" in parsed.preview
