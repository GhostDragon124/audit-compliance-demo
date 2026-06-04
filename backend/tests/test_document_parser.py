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
