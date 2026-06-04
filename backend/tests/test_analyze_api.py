from pathlib import Path

import httpx
import pytest

from app.services.document_parser import DocumentParser


def _upload_file(path: Path, content_type: str = "text/plain") -> tuple[str, tuple[str, bytes, str]]:
    return ("files", (path.name, path.read_bytes(), content_type))


@pytest.mark.asyncio
async def test_analyze_with_txt_file(client: httpx.AsyncClient, fixtures_dir: Path) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "请识别这份材料中的审计风险。"},
        files=[_upload_file(fixtures_dir / "sample.txt")],
    )

    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"answer_text", "parsed_files", "retrieved_regulations"}
    assert isinstance(data["answer_text"], str)
    assert data["answer_text"]
    assert isinstance(data["parsed_files"], list)
    assert isinstance(data["retrieved_regulations"], list)
    assert data["parsed_files"][0]["filename"] == "sample.txt"
    assert data["parsed_files"][0]["status"] == "parsed"


@pytest.mark.asyncio
async def test_analyze_with_multiple_files(client: httpx.AsyncClient, fixtures_dir: Path) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "请汇总所有上传材料。"},
        files=[
            _upload_file(fixtures_dir / "sample.txt"),
            _upload_file(fixtures_dir / "sample.md", "text/markdown"),
            _upload_file(fixtures_dir / "sample.csv", "text/csv"),
        ],
    )

    assert response.status_code == 200
    parsed_files = response.json()["parsed_files"]
    assert {item["filename"] for item in parsed_files} == {
        "sample.txt",
        "sample.md",
        "sample.csv",
    }
    assert all(item["status"] == "parsed" for item in parsed_files)


@pytest.mark.asyncio
async def test_analyze_with_unsupported_file(client: httpx.AsyncClient, fixtures_dir: Path) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "请处理不支持的文件。"},
        files=[_upload_file(fixtures_dir / "unsupported.bin", "application/octet-stream")],
    )

    assert response.status_code == 200
    parsed_file = response.json()["parsed_files"][0]
    assert parsed_file["filename"] == "unsupported.bin"
    assert parsed_file["status"] == "unsupported"
    assert parsed_file["error"]


@pytest.mark.asyncio
async def test_analyze_without_files(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "没有上传文件时请给出初步判断。"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer_text"]
    assert data["parsed_files"] == []
    assert data["retrieved_regulations"] == []


@pytest.mark.asyncio
async def test_analyze_without_question(client: httpx.AsyncClient, fixtures_dir: Path) -> None:
    response = await client.post(
        "/api/analyze",
        files=[_upload_file(fixtures_dir / "sample.txt")],
    )

    assert response.status_code == 422



class FakeOCRService:
    def __init__(self, text: str | None = None, error: Exception | None = None):
        self.text = text
        self.error = error

    def extract_text(self, image_path: Path) -> str:
        if self.error:
            raise self.error
        return self.text or ""


def _image_file(tmp_path: Path, name: str = "sample.png") -> Path:
    image_path = tmp_path / name
    image_path.write_bytes(b"fake-image")
    return image_path


@pytest.mark.asyncio
async def test_analyze_with_image_file(
    client: httpx.AsyncClient,
    fixtures_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected_text = (fixtures_dir / "sample_ocr.txt").read_text(encoding="utf-8").strip()
    monkeypatch.setattr(
        "app.main.DocumentParser",
        lambda: DocumentParser(ocr_service=FakeOCRService(expected_text)),
    )

    response = await client.post(
        "/api/analyze",
        data={"question": "请识别图片中的审计风险。"},
        files=[_upload_file(_image_file(tmp_path), "image/png")],
    )

    assert response.status_code == 200
    parsed_file = response.json()["parsed_files"][0]
    assert parsed_file["filename"] == "sample.png"
    assert parsed_file["status"] == "ocr_parsed"
    assert parsed_file["preview"] == expected_text


@pytest.mark.asyncio
async def test_analyze_mixed_files(
    client: httpx.AsyncClient,
    fixtures_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "app.main.DocumentParser",
        lambda: DocumentParser(ocr_service=FakeOCRService(error=RuntimeError("OCR failed"))),
    )

    response = await client.post(
        "/api/analyze",
        data={"question": "请汇总图片和文本材料。"},
        files=[
            _upload_file(_image_file(tmp_path), "image/png"),
            _upload_file(fixtures_dir / "sample.txt"),
        ],
    )

    assert response.status_code == 200
    parsed_files = {item["filename"]: item for item in response.json()["parsed_files"]}
    assert parsed_files["sample.png"]["status"] == "failed"
    assert parsed_files["sample.png"]["error"] == "OCR failed"
    assert parsed_files["sample.txt"]["status"] == "parsed"
    assert "采购审批" in parsed_files["sample.txt"]["preview"]
