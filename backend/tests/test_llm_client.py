import pytest

from app.config import Settings
from app.services.llm_client import LLMClient


@pytest.mark.asyncio
async def test_mock_response_when_no_api_key() -> None:
    client = LLMClient(Settings(llm_api_key=""))

    response = await client.chat_completion("测试 prompt")

    assert "mock 初步审核意见" in response


@pytest.mark.asyncio
async def test_mock_response_is_string() -> None:
    client = LLMClient(Settings(llm_api_key=""))

    response = await client.chat_completion("测试 prompt")

    assert isinstance(response, str)
