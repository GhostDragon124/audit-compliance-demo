from pathlib import Path

from app.services.document_parser import DocumentParser


def test_parse_txt_file(fixtures_dir: Path) -> None:
    parsed = DocumentParser().parse(fixtures_dir / "sample.txt", "sample.txt")

    assert parsed.filename == "sample.txt"
    assert parsed.status == "parsed"
    assert "采购审批" in parsed.preview
    assert parsed.error is None


def test_parse_md_file(fixtures_dir: Path) -> None:
    parsed = DocumentParser().parse(fixtures_dir / "sample.md", "sample.md")

    assert parsed.filename == "sample.md"
    assert parsed.status == "parsed"
    assert "审计测试材料" in parsed.preview
    assert parsed.error is None


def test_parse_csv_file(fixtures_dir: Path) -> None:
    parsed = DocumentParser().parse(fixtures_dir / "sample.csv", "sample.csv")

    assert parsed.filename == "sample.csv"
    assert parsed.status == "parsed"
    assert "项目, 金额, 审批状态" in parsed.preview
    assert "办公用品, 1200, 已审批" in parsed.preview
    assert parsed.error is None


def test_parse_pdf_file(fixtures_dir: Path) -> None:
    parsed = DocumentParser().parse(fixtures_dir / "sample.pdf", "sample.pdf")

    assert parsed.filename == "sample.pdf"
    assert parsed.status == "parsed"
    assert "[Page 1]" in parsed.preview
    assert "Audit PDF sample procurement control" in parsed.preview
    assert parsed.error is None


def test_parse_docx_file(fixtures_dir: Path) -> None:
    parsed = DocumentParser().parse(fixtures_dir / "sample.docx", "sample.docx")

    assert parsed.filename == "sample.docx"
    assert parsed.status == "parsed"
    assert "Audit DOCX sample procurement policy" in parsed.preview
    assert "| Control | Status |" in parsed.preview
    assert "| Approval | Complete |" in parsed.preview
    assert parsed.error is None


def test_parse_xlsx_file(fixtures_dir: Path) -> None:
    parsed = DocumentParser().parse(fixtures_dir / "sample.xlsx", "sample.xlsx")

    assert parsed.filename == "sample.xlsx"
    assert parsed.status == "parsed"
    assert "[Sheet: Procurement]" in parsed.preview
    assert "| Project | Amount | Status |" in parsed.preview
    assert "| Office supplies | 1200 | Approved |" in parsed.preview
    assert "[Sheet: Risks]" in parsed.preview
    assert "| Missing approval | High |" in parsed.preview
    assert parsed.error is None


def test_parse_unsupported_doc_and_xls(fixtures_dir: Path) -> None:
    parser = DocumentParser()

    parsed_doc = parser.parse(fixtures_dir / "unsupported.doc", "unsupported.doc")
    parsed_xls = parser.parse(fixtures_dir / "unsupported.xls", "unsupported.xls")

    assert parsed_doc.filename == "unsupported.doc"
    assert parsed_doc.status == "unsupported"
    assert parsed_doc.preview == ""
    assert parsed_doc.error
    assert "Unsupported file type" in parsed_doc.error
    assert parsed_xls.filename == "unsupported.xls"
    assert parsed_xls.status == "unsupported"
    assert parsed_xls.preview == ""
    assert parsed_xls.error
    assert "Unsupported file type" in parsed_xls.error


def test_parse_corrupted_pdf(tmp_path: Path) -> None:
    corrupted_pdf = tmp_path / "corrupted.pdf"
    corrupted_pdf.write_bytes(b"not a real pdf")

    parsed = DocumentParser().parse(corrupted_pdf, "corrupted.pdf")

    assert parsed.filename == "corrupted.pdf"
    assert parsed.status == "failed"
    assert parsed.preview == ""
    assert parsed.error


def test_parse_unsupported_file(fixtures_dir: Path) -> None:
    parsed = DocumentParser().parse(fixtures_dir / "unsupported.bin", "unsupported.bin")

    assert parsed.filename == "unsupported.bin"
    assert parsed.status == "unsupported"
    assert parsed.preview == ""
    assert parsed.error
    assert "Unsupported file type" in parsed.error


def test_parse_empty_file(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    parsed = DocumentParser().parse(empty_file, "empty.txt")

    assert parsed.filename == "empty.txt"
    assert parsed.status == "parsed"
    assert parsed.preview == ""
    assert parsed.error is None



class FakeOCRService:
    def __init__(self, text: str | None = None, error: Exception | None = None):
        self.text = text
        self.error = error

    def extract_text(self, image_path: Path) -> str:
        if self.error:
            raise self.error
        return self.text or ""


def test_parse_image_returns_ocr_parsed(fixtures_dir: Path, tmp_path: Path) -> None:
    image_file = tmp_path / "sample.png"
    image_file.write_bytes(b"fake-image")
    expected_text = (fixtures_dir / "sample_ocr.txt").read_text(encoding="utf-8").strip()

    parsed = DocumentParser(ocr_service=FakeOCRService(expected_text)).parse(image_file, "sample.png")

    assert parsed.filename == "sample.png"
    assert parsed.status == "ocr_parsed"
    assert parsed.preview == expected_text
    assert parsed.error is None


def test_parse_image_ocr_failure_returns_failed(tmp_path: Path) -> None:
    image_file = tmp_path / "sample.png"
    image_file.write_bytes(b"fake-image")

    parsed = DocumentParser(ocr_service=FakeOCRService(error=RuntimeError("OCR failed"))).parse(
        image_file,
        "sample.png",
    )

    assert parsed.filename == "sample.png"
    assert parsed.status == "failed"
    assert parsed.preview == ""
    assert parsed.error == "OCR failed"



def test_parse_image_no_text_returns_failed(tmp_path: Path) -> None:
    image_file = tmp_path / "sample.png"
    image_file.write_bytes(b"fake-image")

    parsed = DocumentParser(ocr_service=FakeOCRService("   ")).parse(image_file, "sample.png")

    assert parsed.filename == "sample.png"
    assert parsed.status == "failed"
    assert parsed.preview == ""
    assert parsed.error == "No text detected in image"
