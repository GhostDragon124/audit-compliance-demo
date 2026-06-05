from pathlib import Path

import httpx
import pytest

from app.config import Settings
from app.main import app
from app.services.document_parser import DocumentParser


def test_zero_byte_txt_returns_controlled_result(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_bytes(b"")

    parsed = DocumentParser().parse(source, "empty.txt")

    assert parsed.status == "parsed"
    assert parsed.preview == ""
    assert parsed.error is None


@pytest.mark.asyncio
async def test_empty_document_does_not_crash_request(client, tmp_path: Path) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "空文件"},
        files=[("files", ("empty.txt", b"", "text/plain"))],
    )

    assert response.status_code == 200
    assert response.json()["parsed_files"][0]["status"] == "parsed"


def test_corrupt_pdf_does_not_crash_request(tmp_path: Path) -> None:
    source = tmp_path / "corrupt.pdf"
    source.write_bytes(b"not a pdf")

    parsed = DocumentParser().parse(source, "corrupt.pdf")

    assert parsed.status == "failed"
    assert parsed.preview == ""
    assert parsed.error


def test_corrupt_docx_does_not_crash_request(tmp_path: Path) -> None:
    source = tmp_path / "corrupt.docx"
    source.write_bytes(b"not a docx")

    parsed = DocumentParser().parse(source, "corrupt.docx")

    assert parsed.status == "failed"
    assert parsed.preview == ""
    assert parsed.error


def test_corrupt_xlsx_does_not_crash_request(tmp_path: Path) -> None:
    source = tmp_path / "corrupt.xlsx"
    source.write_bytes(b"not an xlsx")

    parsed = DocumentParser().parse(source, "corrupt.xlsx")

    assert parsed.status == "failed"
    assert parsed.preview == ""
    assert parsed.error


@pytest.mark.asyncio
async def test_unsupported_file_does_not_crash_request(client) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "不支持的文件"},
        files=[("files", ("sample.exe", b"binary", "application/octet-stream"))],
    )

    assert response.status_code == 200
    parsed = response.json()["parsed_files"][0]
    assert parsed["status"] == "unsupported"
    assert parsed["error"]


@pytest.mark.asyncio
async def test_mixed_batch_allows_partial_success(client) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "混合上传"},
        files=[
            ("files", ("good.txt", b"valid text", "text/plain")),
            ("files", ("bad.pdf", b"not a pdf", "application/pdf")),
            ("files", ("unsupported.bin", b"binary", "application/octet-stream")),
        ],
    )

    assert response.status_code == 200
    parsed = {item["filename"]: item for item in response.json()["parsed_files"]}
    assert parsed["good.txt"]["status"] == "parsed"
    assert parsed["bad.pdf"]["status"] == "failed"
    assert parsed["unsupported.bin"]["status"] == "unsupported"


@pytest.mark.asyncio
async def test_filename_path_traversal_is_sanitized(client) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "路径穿越"},
        files=[("files", ("../../secret.txt", b"safe", "text/plain"))],
    )

    assert response.status_code == 200
    assert response.json()["parsed_files"][0]["filename"] == "secret.txt"


@pytest.mark.asyncio
async def test_duplicate_filenames_do_not_overwrite_each_other(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr("app.main.UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: Settings(llm_api_key="", upload_cleanup=False),
    )
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        response = await test_client.post(
            "/api/analyze",
            data={"question": "同名文件"},
            files=[
                ("files", ("same.txt", b"first content", "text/plain")),
                ("files", ("same.txt", b"second content", "text/plain")),
            ],
        )

    assert response.status_code == 200
    previews = [item["preview"] for item in response.json()["parsed_files"]]
    assert previews == ["first content", "second content"]
    assert len(list(upload_dir.glob("*_same.txt"))) == 2
