import os
from pathlib import Path
import shutil
import time

import httpx
import pytest

from app.config import Settings
from app.services.embedding_client import EmbeddingClient
from app.services.llm_client import LLMClient
from app.services.ocr_service import OCRException, OCRService


@pytest.mark.local_ocr
def test_local_disabled_ocr_provider_reports_controlled_failure(tmp_path: Path) -> None:
    image = tmp_path / "blank.png"
    image.write_bytes(b"not an image")

    with pytest.raises(OCRException):
        OCRService(provider="disabled").extract_text(image)


@pytest.mark.local_ocr
def test_local_tesseract_provider_if_available(tmp_path: Path) -> None:
    if shutil.which("tesseract") is None:
        pytest.skip("BLOCKED: tesseract binary is not installed or not on PATH.")

    pillow = pytest.importorskip("PIL.Image")
    image_draw = pytest.importorskip("PIL.ImageDraw")
    image = pillow.new("RGB", (320, 120), "white")
    draw = image_draw.Draw(image)
    draw.text((20, 40), "Audit 123", fill="black")
    image_path = tmp_path / "tesseract_sample.png"
    image.save(image_path)

    start = time.perf_counter()
    text = OCRService(provider="tesseract", lang="eng").extract_text(image_path)
    elapsed = time.perf_counter() - start

    assert elapsed >= 0
    assert "Audit" in text or "123" in text


@pytest.mark.local_ocr
def test_local_paddleocr_provider_requires_explicit_init_permission(tmp_path: Path) -> None:
    if os.getenv("AUDITPILOT_ALLOW_PADDLEOCR_INIT") != "1":
        pytest.skip("BLOCKED: set AUDITPILOT_ALLOW_PADDLEOCR_INIT=1 after models exist locally.")

    pytest.importorskip("paddleocr")
    image = tmp_path / "blank.png"
    image.write_bytes(b"not an image")

    with pytest.raises(OCRException):
        OCRService(provider="paddleocr").extract_text(image)


@pytest.mark.local_qwen
@pytest.mark.asyncio
async def test_local_qwen_chat_completions_compatible() -> None:
    settings = Settings()
    if settings.llm_mode != "openai_compatible":
        pytest.skip("BLOCKED: set LLM_MODE=openai_compatible for local Qwen validation.")
    if "your-qwen-api-server" in settings.llm_base_url:
        pytest.skip("BLOCKED: LLM_BASE_URL still uses placeholder value.")

    start = time.perf_counter()
    answer = await LLMClient(settings).chat_completion("用中文回答：本地模型连通性测试。")
    elapsed = time.perf_counter() - start

    assert elapsed >= 0
    assert isinstance(answer, str)
    assert answer.strip()


@pytest.mark.local_qwen
@pytest.mark.asyncio
async def test_local_qwen_endpoint_reachable_without_printing_secret() -> None:
    settings = Settings()
    if settings.llm_mode != "openai_compatible":
        pytest.skip("BLOCKED: set LLM_MODE=openai_compatible for local Qwen validation.")

    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = "Bearer " + settings.llm_api_key
    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": "请回答：OK"}],
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
        response = await client.post(url, json=payload, headers=headers)

    assert response.status_code < 500


@pytest.mark.local_embedding
def test_local_embedding_endpoint_returns_qwen3_2560_vectors() -> None:
    settings = Settings()
    if settings.embedding_provider != "openai_compatible":
        pytest.skip("BLOCKED: set EMBEDDING_PROVIDER=openai_compatible for local embedding validation.")

    client = EmbeddingClient(
        provider="openai_compatible",
        model=settings.embedding_model,
        base_url=settings.embedding_base_url,
        timeout=2.0,
    )
    try:
        embeddings = client.embed_texts(["本地 embedding 端点验收。"])
    except httpx.TransportError as exc:
        pytest.skip(f"BLOCKED: embedding endpoint {settings.embedding_base_url} is not reachable: {exc}")

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 2560
    assert any(value != 0.0 for value in embeddings[0])

