from pathlib import Path

import pytest

from app.config import Settings
from app.models import ParsedDocument
from app.schemas import ParsedFileSummary
from app.services.audit_engine import AuditEngine
from app.services.document_parser import DocumentParser


class CaptureLLMClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def chat_completion(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "captured"


def _prompt_engine(
    prompt_path: Path,
    settings: Settings | None = None,
) -> tuple[AuditEngine, CaptureLLMClient]:
    llm_client = CaptureLLMClient()
    return (
        AuditEngine(
            llm_client=llm_client,
            prompt_path=prompt_path,
            settings=settings or Settings(llm_api_key=""),
        ),
        llm_client,
    )


@pytest.mark.asyncio
async def test_audit_engine_receives_full_text_not_only_preview(
    tmp_path: Path,
    prompt_path: Path,
) -> None:
    sentinel = "FULL_TEXT_SENTINEL_AFTER_PREVIEW"
    source = tmp_path / "long.txt"
    source.write_text("A" * 1200 + sentinel, encoding="utf-8")
    parsed = DocumentParser().parse(source, "long.txt")
    engine, llm_client = _prompt_engine(prompt_path)

    await engine.analyze("请分析完整材料", [parsed])

    assert sentinel in llm_client.prompts[0]


@pytest.mark.asyncio
async def test_full_text_not_leaked_in_api(
    client,
    tmp_path: Path,
) -> None:
    secret = "SENSITIVE_FULL_TEXT_SHOULD_NOT_LEAK"
    source = tmp_path / "sensitive.txt"
    source.write_text("公开预览" + ("A" * 1200) + secret, encoding="utf-8")

    response = await client.post(
        "/api/analyze",
        data={"question": "请分析材料"},
        files=[("files", ("sensitive.txt", source.read_bytes(), "text/plain"))],
    )

    assert response.status_code == 200
    assert secret not in response.text
    assert "full_text" not in response.json()["parsed_files"][0]


@pytest.mark.asyncio
async def test_long_document_truncation_is_explicit(
    tmp_path: Path,
    prompt_path: Path,
) -> None:
    source = tmp_path / "long.txt"
    source.write_text("A" * 1500, encoding="utf-8")
    parsed = DocumentParser().parse(source, "long.txt")
    engine, llm_client = _prompt_engine(
        prompt_path,
        Settings(llm_api_key="", llm_max_prompt_chars=1000),
    )

    result = await engine.analyze("分析", [parsed])

    assert "以下材料已被截断" in llm_client.prompts[0]
    assert "原始 1500 字符" in llm_client.prompts[0]
    assert "使用前 1000 字符" in llm_client.prompts[0]
    assert result.answer_text.startswith("\n\n[分析范围提示]")


@pytest.mark.asyncio
async def test_token_budget_distribution(prompt_path: Path) -> None:
    engine, llm_client = _prompt_engine(
        prompt_path,
        Settings(llm_api_key="", llm_max_prompt_chars=1000),
    )
    parsed_files = [
        ParsedDocument(
            filename="small.txt",
            status="parsed",
            full_text="A" * 1000,
            preview="A" * 1000,
        ),
        ParsedDocument(
            filename="large.txt",
            status="parsed",
            full_text="B" * 3000,
            preview="B" * 1000,
        ),
    ]

    await engine.analyze("按比例分配", parsed_files)

    prompt = llm_client.prompts[0]
    assert "A" * 250 in prompt
    assert "A" * 251 not in prompt
    assert "B" * 750 in prompt
    assert "B" * 751 not in prompt


@pytest.mark.asyncio
async def test_multiple_parsed_documents_are_included_in_prompt(
    prompt_path: Path,
) -> None:
    engine, llm_client = _prompt_engine(prompt_path)
    parsed_files = [
        ParsedFileSummary(filename="a.txt", status="parsed", preview="材料 A"),
        ParsedFileSummary(filename="b.txt", status="parsed", preview="材料 B"),
    ]

    await engine.analyze("汇总", parsed_files)

    prompt = llm_client.prompts[0]
    assert "a.txt" in prompt
    assert "材料 A" in prompt
    assert "b.txt" in prompt
    assert "材料 B" in prompt


@pytest.mark.asyncio
async def test_failed_document_content_is_not_treated_as_valid(
    prompt_path: Path,
) -> None:
    engine, llm_client = _prompt_engine(prompt_path)
    parsed = ParsedFileSummary(
        filename="failed.txt",
        status="failed",
        preview="SHOULD_NOT_BE_VALID_CONTENT",
        error="parse failed",
    )

    await engine.analyze("分析", [parsed])

    assert "SHOULD_NOT_BE_VALID_CONTENT" not in llm_client.prompts[0]
