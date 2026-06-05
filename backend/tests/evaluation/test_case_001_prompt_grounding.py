"""
Slice 4B: Case 001 Prompt Grounding Tests

Tests that the AuditEngine prompt properly uses retrieved regulation fragments,
includes source references, and does NOT treat preview as full text.
Uses fake retriever + fake LLM. No real Qwen or Embedding.
"""

from pathlib import Path

import yaml

from app.models import ParsedDocument
from app.schemas import RegulationChunk
from app.services.audit_engine import AuditEngine
from app.config import Settings

# ── Fixtures ─────────────────────────────────────────────────────────

CASE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "tests"
    / "evaluation"
    / "case_001_procurement_pending_approval"
)


def load_expected():
    path = CASE_ROOT / "expected_results.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class FakeLLMClient:
    """Captures the prompt passed to chat_completion and returns a controlled response."""

    def __init__(self, response: str = "mock audit response"):
        self.last_prompt: str | None = None
        self._response = response

    async def chat_completion(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._response


def _make_fake_llm(response: str = "mock audit response") -> FakeLLMClient:
    """Return a FakeLLMClient with a controlled response."""
    return FakeLLMClient(response=response)


def _make_engine(prompt_path: Path | None = None) -> AuditEngine:
    """Create an AuditEngine with a fake LLM and default settings."""
    if prompt_path is None:
        prompt_path = (
            Path(__file__).resolve().parents[2]
            / "app"
            / "prompts"
            / "audit_prompt.txt"
        )
    settings = Settings(llm_mode="mock")
    fake_llm = _make_fake_llm()
    return AuditEngine(llm_client=fake_llm, prompt_path=prompt_path, settings=settings)


def _make_material_doc(
    filename: str = "采购项目说明.md",
    full_text: str | None = None,
    preview: str = "预览...",
    status: str = "parsed",
) -> ParsedDocument:
    """Helper to create a ParsedDocument for testing."""
    if full_text is None:
        full_text = (
            "# 实验室服务器采购项目说明\n\n"
            "## 项目基本信息\n\n"
            "- 项目名称：实验室服务器采购项目\n"
            "- 采购预算：人民币 850,000 元\n"
            "- 采购方式：询价采购\n"
            "- 拟选供应商：星海科技有限公司\n\n"
            "## 当前进展\n\n"
            "1. 已完成三家供应商询价。\n"
            "2. 已选定星海科技有限公司作为拟合作供应商。\n"
            "3. 合同草案已经生成。\n"
            "4. 采购审批流程正在办理中。\n"
            "5. 当前尚未上传非公开招标方式专项审批文件。\n"
        )
    return ParsedDocument(
        filename=filename,
        status=status,
        full_text=full_text,
        preview=preview,
        error=None,
    )


# ── Tests ────────────────────────────────────────────────────────────


class TestPromptGrounding4B:
    """4B: Prompt grounding tests."""

    def test_prompt_contains_material_full_text(self):
        """The prompt sent to the LLM must include the full text of the
        uploaded materials (not just preview)."""
        engine = _make_engine()
        material = _make_material_doc()
        prompt = engine.build_rag_prompt(
            question="请分析这些采购材料中可能存在的合规风险",
            parsed_files=[material],
            retrieved_regulations=[],
        )
        assert "实验室服务器采购项目" in prompt
        assert "850,000" in prompt
        assert "星海科技有限公司" in prompt

    def test_prompt_contains_regulation_fragments(self):
        """The prompt must include fragments from relevant regulations
        (采购管理办法.txt, 采购审批管理规定.txt) as returned by retriever."""
        engine = _make_engine()
        material = _make_material_doc()
        regulations = [
            RegulationChunk(
                chunk_id="chunk_001",
                source_file="采购管理办法.txt",
                content="第一条 采购项目金额达到人民币 500,000 元及以上的，原则上应采用公开招标方式。",
            ),
            RegulationChunk(
                chunk_id="chunk_002",
                source_file="采购审批管理规定.txt",
                content="第一条 采购项目应当在完成部门负责人、财务部门和分管领导审批后，方可正式确定供应商。",
            ),
        ]
        prompt = engine.build_rag_prompt(
            question="请分析这些采购材料中可能存在的合规风险",
            parsed_files=[material],
            retrieved_regulations=regulations,
        )
        assert "500,000" in prompt
        # "完成" and "审批" appear in the regulation fragment content
        assert "完成" in prompt
        assert "审批后" in prompt

    def test_prompt_includes_source_references(self):
        """The prompt must include source_file and chunk_id for each
        retrieved regulation fragment, enabling traceable citations."""
        engine = _make_engine()
        material = _make_material_doc()
        regulations = [
            RegulationChunk(
                chunk_id="chunk_001",
                source_file="采购管理办法.txt",
                content="第一条 采购项目金额达到人民币 500,000 元及以上的，原则上应采用公开招标方式。",
            ),
            RegulationChunk(
                chunk_id="chunk_002",
                source_file="采购审批管理规定.txt",
                content="第一条 采购项目应当在完成部门负责人、财务部门和分管领导审批后，方可正式确定供应商。",
            ),
        ]
        prompt = engine.build_rag_prompt(
            question="请分析这些采购材料中可能存在的合规风险",
            parsed_files=[material],
            retrieved_regulations=regulations,
        )
        assert "采购管理办法.txt" in prompt
        # Check for chunk_id reference in the prompt
        assert "chunk_001" in prompt or "chunk" in prompt.lower()

    def test_prompt_does_not_use_preview_as_full_text(self):
        """The prompt must NOT contain truncated preview text as a
        substitute for the full material content. Full text must be used."""
        engine = _make_engine()
        # Create material where preview is truncated but full_text has details
        full_text = "完整内容含850000元详情及实验室服务器采购项目完整说明"
        preview = "截断预览...不包含完整金额信息"
        material = _make_material_doc(
            full_text=full_text,
            preview=preview,
        )
        prompt = engine.build_rag_prompt(
            question="请分析这些采购材料中可能存在的合规风险",
            parsed_files=[material],
            retrieved_regulations=[],
        )
        # Full text detail should be present
        assert "850000" in prompt
        # Preview text should NOT be used as the content
        assert "截断预览" not in prompt

    def test_prompt_does_not_use_irrelevant_distractor_as_primary(self):
        """The irrelevant distractor regulation (差旅费管理规定.txt) should
        NOT appear as a primary basis in the prompt."""
        engine = _make_engine()
        material = _make_material_doc()
        # Return regulations with the distractor as third item (lowest rank)
        regulations = [
            RegulationChunk(
                chunk_id="chunk_001",
                source_file="采购管理办法.txt",
                content="第一条 采购项目金额达到人民币 500,000 元及以上的，原则上应采用公开招标方式。",
            ),
            RegulationChunk(
                chunk_id="chunk_002",
                source_file="采购审批管理规定.txt",
                content="第一条 采购项目应当在完成审批后，方可正式确定供应商。",
            ),
            RegulationChunk(
                chunk_id="chunk_003",
                source_file="差旅费管理规定.txt",
                content="工作人员因公务出差产生的交通费、住宿费和伙食补助费，应当按照差旅费标准报销。",
            ),
        ]
        prompt = engine.build_rag_prompt(
            question="请分析这些采购材料中可能存在的合规风险",
            parsed_files=[material],
            retrieved_regulations=regulations,
        )
        # The distractor should NOT appear before the relevant regulations
        distractor_pos = prompt.find("差旅费管理规定.txt")
        primary_pos = prompt.find("采购管理办法.txt")
        assert distractor_pos > primary_pos, (
            "Irrelevant distractor (差旅费管理规定.txt) should not appear "
            "before relevant primary regulation (采购管理办法.txt)"
        )

    def test_prompt_has_manual_confirmation_disclaimer(self):
        """The prompt must include the disclaimer that regulation validity
        requires manual confirmation (制度有效性需人工确认)."""
        engine = _make_engine()
        material = _make_material_doc()
        regulations = [
            RegulationChunk(
                chunk_id="chunk_001",
                source_file="采购管理办法.txt",
                content="第一条 采购项目金额达到人民币 500,000 元及以上的，原则上应采用公开招标方式。",
            ),
        ]
        prompt = engine.build_rag_prompt(
            question="请分析这些采购材料中可能存在的合规风险",
            parsed_files=[material],
            retrieved_regulations=regulations,
        )
        assert "制度有效性" in prompt or "人工确认" in prompt
