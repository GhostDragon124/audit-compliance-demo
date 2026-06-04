import pytest
from pathlib import Path

from app.config import Settings
from app.schemas import AnalyzeResponse, ParsedFileSummary
from app.services.audit_engine import AuditEngine
from app.services.llm_client import LLMClient


@pytest.mark.asyncio
async def test_analyze_returns_analyze_response(mock_settings: Settings, prompt_path: Path) -> None:
    engine = AuditEngine(llm_client=LLMClient(mock_settings), prompt_path=prompt_path)

    result = await engine.analyze(question="请分析审计风险。", parsed_files=[])

    assert isinstance(result, AnalyzeResponse)


@pytest.mark.asyncio
async def test_analyze_includes_parsed_files(mock_settings: Settings, prompt_path: Path) -> None:
    parsed_files = [
        ParsedFileSummary(
            filename="sample.txt",
            status="parsed",
            preview="测试材料内容",
        )
    ]
    engine = AuditEngine(llm_client=LLMClient(mock_settings), prompt_path=prompt_path)

    result = await engine.analyze(question="请分析审计风险。", parsed_files=parsed_files)

    assert result.parsed_files == parsed_files


@pytest.mark.asyncio
async def test_answer_text_not_empty(mock_settings: Settings, prompt_path: Path) -> None:
    engine = AuditEngine(llm_client=LLMClient(mock_settings), prompt_path=prompt_path)

    result = await engine.analyze(question="请分析审计风险。", parsed_files=[])

    assert result.answer_text
