from typing import Any

import httpx
import pytest

from app.config import Settings
from app.services.llm_client import (
    LLMClient,
    LLMConnectionError,
    LLMError,
    LLMServiceError,
    LLMTimeoutError,
)


class FakeResponse:
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        *,
        status_code: int = 200,
        json_error: Exception | None = None,
    ) -> None:
        self.data = data if data is not None else {
            "choices": [{"message": {"content": "真实模型返回"}}],
        }
        self.status_code = status_code
        self.json_error = json_error

    def json(self) -> dict[str, Any]:
        if self.json_error:
            raise self.json_error
        return self.data


class FakeAsyncClient:
    captured: dict[str, Any] = {}
    response: FakeResponse = FakeResponse()
    post_error: Exception | None = None

    def __init__(self, timeout: float) -> None:
        FakeAsyncClient.captured["timeout"] = timeout

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(self, url: str, json: dict[str, Any], headers: dict[str, str]):
        FakeAsyncClient.captured.update(
            {
                "url": url,
                "json": json,
                "headers": headers,
            }
        )
        if FakeAsyncClient.post_error:
            raise FakeAsyncClient.post_error
        return FakeAsyncClient.response


@pytest.fixture(autouse=True)
def reset_fake_client(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeAsyncClient.captured = {}
    FakeAsyncClient.response = FakeResponse()
    FakeAsyncClient.post_error = None
    monkeypatch.setattr("app.services.llm_client.httpx.AsyncClient", FakeAsyncClient)


@pytest.mark.asyncio
async def test_llm_mock_mode_does_not_call_http() -> None:
    response = await LLMClient(Settings(llm_mode="mock", llm_api_key="key")).chat_completion("prompt")

    assert "mock 初步审核意见" in response
    assert FakeAsyncClient.captured == {}


@pytest.mark.asyncio
async def test_openai_compatible_calls_http_without_api_key() -> None:
    response = await LLMClient(
        Settings(llm_mode="openai_compatible", llm_api_key="")
    ).chat_completion("prompt")

    assert response == "真实模型返回"
    assert FakeAsyncClient.captured["url"] == "http://127.0.0.1:8083/v1/chat/completions"
    assert FakeAsyncClient.captured["headers"] == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_unknown_llm_mode_raises_error() -> None:
    with pytest.raises(LLMError, match="Unknown LLM_MODE"):
        await LLMClient(Settings(llm_mode="invalid")).chat_completion("prompt")


@pytest.mark.asyncio
async def test_llm_timeout_raises_controlled_error() -> None:
    FakeAsyncClient.post_error = httpx.TimeoutException("timeout")

    with pytest.raises(LLMTimeoutError, match="网关超时"):
        await LLMClient(Settings(llm_mode="openai_compatible")).chat_completion("prompt")


@pytest.mark.asyncio
async def test_llm_connection_error_raises_controlled_error() -> None:
    FakeAsyncClient.post_error = httpx.ConnectError("closed")

    with pytest.raises(LLMConnectionError, match="无法连接模型服务"):
        await LLMClient(Settings(llm_mode="openai_compatible")).chat_completion("prompt")


@pytest.mark.asyncio
async def test_llm_http_500_raises_service_error() -> None:
    FakeAsyncClient.response = FakeResponse(status_code=500)

    with pytest.raises(LLMServiceError, match="模型服务异常") as exc_info:
        await LLMClient(Settings(llm_mode="openai_compatible")).chat_completion("prompt")

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_llm_http_429_raises_busy_error() -> None:
    FakeAsyncClient.response = FakeResponse(status_code=429)

    with pytest.raises(LLMServiceError, match="模型服务繁忙") as exc_info:
        await LLMClient(Settings(llm_mode="openai_compatible")).chat_completion("prompt")

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_llm_invalid_json_raises_service_error() -> None:
    FakeAsyncClient.response = FakeResponse(json_error=ValueError("invalid json"))

    with pytest.raises(LLMServiceError, match="模型返回格式异常") as exc_info:
        await LLMClient(Settings(llm_mode="openai_compatible")).chat_completion("prompt")

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_llm_missing_choices_raises_service_error() -> None:
    FakeAsyncClient.response = FakeResponse(data={"id": "missing choices"})

    with pytest.raises(LLMServiceError, match="模型返回缺少内容") as exc_info:
        await LLMClient(Settings(llm_mode="openai_compatible")).chat_completion("prompt")

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_llm_base_url_model_auth_and_timeout_come_from_settings() -> None:
    result = await LLMClient(
        Settings(
            llm_mode="openai_compatible",
            llm_base_url="http://localhost:9999/v1/",
            llm_api_key="test-key",
            llm_model="qwen-local",
            llm_timeout=12.5,
        )
    ).chat_completion("prompt")

    assert result == "真实模型返回"
    assert FakeAsyncClient.captured["url"] == "http://localhost:9999/v1/chat/completions"
    assert FakeAsyncClient.captured["json"]["model"] == "qwen-local"
    assert FakeAsyncClient.captured["headers"]["Authorization"] == "Bearer test-key"
    assert FakeAsyncClient.captured["timeout"] == 12.5
