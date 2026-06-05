import pytest
from PIL import Image


def _png_bytes(size: tuple[int, int]) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    Image.new("RGB", size, "white").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_max_file_count_is_enforced(client, mock_settings) -> None:
    mock_settings.max_files_per_request = 1

    response = await client.post(
        "/api/analyze",
        data={"question": "文件数量限制"},
        files=[
            ("files", ("first.txt", b"first", "text/plain")),
            ("files", ("second.txt", b"second", "text/plain")),
        ],
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "单次最多上传 1 个文件"


@pytest.mark.asyncio
async def test_max_single_file_size_is_enforced(client, mock_settings) -> None:
    mock_settings.max_file_size_mb = 0

    response = await client.post(
        "/api/analyze",
        data={"question": "单文件大小限制"},
        files=[("files", ("large.txt", b"x", "text/plain"))],
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "单个文件最大 0 MB"


@pytest.mark.asyncio
async def test_max_total_upload_size_is_enforced(client, mock_settings) -> None:
    mock_settings.max_file_size_mb = 1
    mock_settings.max_total_upload_mb = 0

    response = await client.post(
        "/api/analyze",
        data={"question": "总大小限制"},
        files=[
            ("files", ("first.txt", b"x", "text/plain")),
            ("files", ("second.txt", b"y", "text/plain")),
        ],
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "单次上传总大小最大 0 MB"


@pytest.mark.asyncio
async def test_image_max_dimensions_are_enforced(client, mock_settings) -> None:
    mock_settings.image_max_pixels = 3

    response = await client.post(
        "/api/analyze",
        data={"question": "图片尺寸限制"},
        files=[("files", ("large.png", _png_bytes((2, 2)), "image/png"))],
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "图片尺寸过大"


@pytest.mark.asyncio
async def test_upload_cleanup_removes_files(client, monkeypatch, tmp_path) -> None:
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr("app.main.UPLOAD_DIR", upload_dir)

    response = await client.post(
        "/api/analyze",
        data={"question": "清理上传文件"},
        files=[("files", ("sample.txt", b"cleanup me", "text/plain"))],
    )

    assert response.status_code == 200
    assert list(upload_dir.glob("*_sample.txt")) == []
