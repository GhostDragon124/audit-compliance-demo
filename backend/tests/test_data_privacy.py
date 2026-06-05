from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.asyncio
async def test_api_response_does_not_return_saved_file_path(client) -> None:
    response = await client.post(
        "/api/analyze",
        data={"question": "路径隐私"},
        files=[("files", ("sample.txt", b"safe text", "text/plain"))],
    )

    assert response.status_code == 200
    body = response.text
    assert "uploads" not in body
    assert "/tmp/" not in body


@pytest.mark.asyncio
async def test_api_response_does_not_return_full_document_text(client) -> None:
    hidden_tail = "TAIL_CONTENT_MUST_NOT_BE_RETURNED"
    content = ("A" * 1200 + hidden_tail).encode()

    response = await client.post(
        "/api/analyze",
        data={"question": "全文隐私"},
        files=[("files", ("long.txt", content, "text/plain"))],
    )

    assert response.status_code == 200
    assert hidden_tail not in response.text


@pytest.mark.asyncio
async def test_logs_do_not_include_full_document_content(client, caplog) -> None:
    secret = "LOG_SECRET_MUST_NOT_APPEAR"

    response = await client.post(
        "/api/analyze",
        data={"question": "日志隐私"},
        files=[("files", ("secret.txt", secret.encode(), "text/plain"))],
    )

    assert response.status_code == 200
    assert secret not in caplog.text


def test_env_file_is_gitignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "backend/.env" in gitignore


def test_upload_files_are_gitignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "backend/uploads/*" in gitignore
    assert "!backend/uploads/.gitkeep" in gitignore
