"""
Slice 4B: Case 001 Prompt Grounding Test Skeleton (STRICT XFAIL)

Tests that the AuditEngine prompt properly uses retrieved regulation fragments,
includes source references, and does NOT treat preview as full text.
Uses fake retriever + fake LLM. No real Qwen or Embedding.
"""

import pytest
import yaml
from pathlib import Path

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


def _make_fake_retriever():
    """
    Return a mock VectorRetriever that returns controlled results.
    Will be replaced with actual fake when implementation exists.
    """
    raise NotImplementedError("Requires fake retriever implementation")


def _make_fake_llm():
    """
    Return a mock LLM client that returns controlled responses.
    Will be replaced with actual fake when implementation exists.
    """
    raise NotImplementedError("Requires fake LLM implementation")


# ── Tests ────────────────────────────────────────────────────────────


class TestPromptGrounding4B:
    """4B: Prompt grounding tests (strict xfail until implementation)."""

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4B: AuditEngine prompt must include material full text",
    )
    def test_prompt_contains_material_full_text(self):
        """
        The prompt sent to the LLM must include the full text of the
        uploaded materials (not just preview).
        """
        # ── When real implementation is done: ──
        # engine = AuditEngine(retriever=fake_retriever, llm=fake_llm)
        # prompt = engine.build_prompt(materials=[...], question=...)
        # assert "实验室服务器采购项目" in prompt
        # assert "850,000" in prompt
        # assert "星海科技有限公司" in prompt
        raise NotImplementedError(
            "Requires AuditEngine with full-text support"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4B: prompt must include retrieved regulation fragments",
    )
    def test_prompt_contains_regulation_fragments(self):
        """
        The prompt must include fragments from relevant regulations
        (采购管理办法.txt, 采购审批管理规定.txt) as returned by retriever.
        """
        # ── When real implementation is done: ──
        # fake_retriever = FakeVectorRetriever(regulations=[
        #     ("采购管理办法.txt", "第一条 采购项目金额达到人民币 500,000 元..."),
        #     ("采购审批管理规定.txt", "第一条 采购项目应当完成审批..."),
        # ])
        # prompt = engine.build_prompt(materials=[...], retriever=fake_retriever)
        # assert "500,000" in prompt
        # assert "完成审批" in prompt
        raise NotImplementedError(
            "Requires AuditEngine RAG prompt construction"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4B: prompt must include source_file and chunk_id references",
    )
    def test_prompt_includes_source_references(self):
        """
        The prompt must include source_file and chunk_id for each
        retrieved regulation fragment, enabling traceable citations.
        """
        # ── When real implementation is done: ──
        # prompt = engine.build_prompt(materials=[...], retriever=fake_retriever)
        # assert "采购管理办法.txt" in prompt
        # assert "chunk" in prompt.lower()
        raise NotImplementedError(
            "Requires AuditEngine with citation support"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4B: prompt must not treat preview as full text",
    )
    def test_prompt_does_not_use_preview_as_full_text(self):
        """
        The prompt must NOT contain truncated preview text as a
        substitute for the full material content. Full text must be used.
        """
        # ── When real implementation is done: ──
        # # If preview was used as full text, key details would be missing
        # prompt = engine.build_prompt(materials=[...], retriever=fake_retriever)
        # assert "850,000" in prompt  # would be excluded in preview length
        raise NotImplementedError(
            "Requires AuditEngine with full-text flow"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4B: prompt must not use irrelevant distractor as primary basis",
    )
    def test_prompt_does_not_use_irrelevant_distractor_as_primary(self):
        """
        The irrelevant distractor regulation (差旅费管理规定.txt) should
        NOT appear as a primary basis in the prompt.
        """
        # ── When real implementation is done: ──
        # fake_retriever = FakeVectorRetriever(regulations=[
        #     ("采购管理办法.txt", "..."),
        #     ("采购审批管理规定.txt", "..."),
        #     ("差旅费管理规定.txt", "..."),  # returned but low rank
        # ])
        # prompt = engine.build_prompt(materials=[...], retriever=fake_retriever)
        # # The distractor may appear in context but not as primary argument
        # distractor_pos = prompt.find("差旅费管理规定.txt")
        # # If it appears, it should be in supplementary context, not primary
        raise NotImplementedError(
            "Requires AuditEngine with ranking-aware prompt"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4B: prompt must retain disclaimer about regulation validity",
    )
    def test_prompt_has_manual_confirmation_disclaimer(self):
        """
        The prompt must include the disclaimer that regulation validity
        requires manual confirmation (制度有效性需人工确认).
        """
        # ── When real implementation is done: ──
        # prompt = engine.build_prompt(materials=[...], retriever=fake_retriever)
        # assert "制度有效性需人工确认" in prompt
        # assert "人工复核" in prompt
        raise NotImplementedError(
            "Requires AuditEngine with disclaimer in prompt"
        )
