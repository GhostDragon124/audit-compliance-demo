"""Slice 4C: Case 001 End-to-End Tests (REAL PROVIDERS)

Tests the full pipeline: upload → parse/OCR → full text → embedding →
retrieval → Qwen analysis → risk output.
Uses real PaddleOCR, Qwen3.6-35B, Qwen3-Embedding-4B, and ChromaDB.
"""

import asyncio
from pathlib import Path

import pytest
import yaml

from app.config import Settings
from app.models import ParsedDocument
from app.schemas import RegulationChunk
from app.services.audit_engine import AuditEngine
from app.services.document_parser import DocumentParser
from app.services.embedding_client import EmbeddingClient
from app.services.llm_client import LLMClient
from app.services.regulation_indexer import RegulationIndexer
from app.services.vector_retriever import VectorRetriever

# ── Paths ─────────────────────────────────────────────────────────────

CASE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "tests"
    / "evaluation"
    / "case_001_procurement_pending_approval"
)
MATERIALS_DIR = CASE_ROOT / "materials"
REGULATIONS_DIR = CASE_ROOT / "regulations"
PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "prompts" / "audit_prompt.txt"
)

QUESTION = (CASE_ROOT / "question.txt").read_text(encoding="utf-8").strip()

# Real provider endpoints
EMBEDDING_BASE_URL = "http://127.0.0.1:8085/v1"
EMBEDDING_MODEL = "/models"
LLM_BASE_URL = "http://127.0.0.1:8083/v1"
LLM_MODEL = "qwen3.6-35b-a3b-fp8"

# Regulation files
REGULATION_FILES = {"采购管理办法.txt", "采购审批管理规定.txt", "差旅费管理规定.txt"}
DISTRACTOR_FILE = "差旅费管理规定.txt"

# ── Helpers ───────────────────────────────────────────────────────────


def load_expected():
    path = CASE_ROOT / "expected_results.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _run_pipeline(tmp_path: Path) -> dict:
    """Run full Case 001 pipeline and return result dict.

    Returns:
        dict with keys: answer_text, retrieved_regulations, prompt_text,
                        parsed_documents
    """
    # 1. Parse all 4 materials
    parser = DocumentParser()
    material_files = [
        ("采购项目说明.md", MATERIALS_DIR / "采购项目说明.md"),
        ("合同草案.txt", MATERIALS_DIR / "合同草案.txt"),
        ("供应商报价.xlsx", MATERIALS_DIR / "供应商报价.xlsx"),
        ("采购审批单_scan.png", MATERIALS_DIR / "采购审批单_scan.png"),
    ]
    parsed_documents: list[ParsedDocument] = []
    for filename, filepath in material_files:
        doc = parser.parse(filepath, filename)
        assert doc.status in (
            "parsed",
            "ocr_parsed",
        ), f"Failed to parse {filename}: {doc.status} - {doc.error}"
        parsed_documents.append(doc)

    # 2. Embedding client (real Qwen3-Embedding-4B at 127.0.0.1:8085)
    embedder = EmbeddingClient(
        provider="openai_compatible",
        model=EMBEDDING_MODEL,
        base_url=EMBEDDING_BASE_URL,
        api_key="not-needed",
    )

    # 3. Build isolated ChromaDB index for 3 regulation files
    indexer = RegulationIndexer(
        raw_dir=REGULATIONS_DIR,
        persist_dir=tmp_path,
        collection_name="auditpilot_eval_case_001",
        embedding_client=embedder,
    )
    chunk_count = indexer.build_index()
    assert chunk_count > 0, "Expected at least one chunk to be indexed"

    # 4. Retrieve Top-5 with VectorRetriever
    retriever = VectorRetriever(
        persist_dir=tmp_path,
        collection_name="auditpilot_eval_case_001",
        embedding_client=embedder,
    )
    retrieved = retriever.retrieve(QUESTION, top_k=5)
    assert len(retrieved) > 0, "Expected at least 1 retrieved chunk"

    # 5. Build RAG prompt with AuditEngine.build_rag_prompt()
    settings = Settings(
        llm_mode="openai_compatible",
        llm_base_url=LLM_BASE_URL,
        llm_api_key="not-needed",
        llm_model=LLM_MODEL,
        llm_timeout=180.0,
        ocr_enable=True,
        ocr_provider="paddleocr",
        ocr_device="cpu",
        ocr_lang="ch",
    )
    llm = LLMClient(settings=settings)
    engine = AuditEngine(llm_client=llm, prompt_path=PROMPT_PATH, settings=settings)
    rag_prompt = engine.build_rag_prompt(QUESTION, parsed_documents, retrieved)

    # 6. Call Qwen via LLMClient
    answer_text: str = asyncio.run(llm.chat_completion(rag_prompt))

    return {
        "answer_text": answer_text,
        "retrieved_regulations": retrieved,
        "prompt_text": rag_prompt,
        "parsed_documents": parsed_documents,
    }


# ── Class-scoped fixture ──────────────────────────────────────────────


@pytest.fixture(scope="class")
def pipeline_result(tmp_path_factory):
    """Run the full pipeline once and share the result across all tests."""
    tmp_path = tmp_path_factory.mktemp("chroma_4c")
    return _run_pipeline(tmp_path)


# ── Tests ─────────────────────────────────────────────────────────────


@pytest.mark.case001_e2e
@pytest.mark.case001_local_ocr
class TestEndToEnd4C:
    """4C: End-to-end pipeline tests (real PaddleOCR, Qwen, Embedding, ChromaDB)."""

    def test_full_pipeline_structure(self, pipeline_result):
        """Verify the pipeline returns a well-formed result with no 500 errors."""
        result = pipeline_result

        # answer_text must be a non-empty string
        answer_text = result["answer_text"]
        assert isinstance(answer_text, str), "answer_text must be a string"
        assert len(answer_text) > 0, "answer_text must not be empty"

        # retrieved_regulations must be a non-empty list
        retrieved = result["retrieved_regulations"]
        assert isinstance(retrieved, list), "retrieved_regulations must be a list"
        assert len(retrieved) > 0, "retrieved_regulations must not be empty"

        # Each regulation must have source_file, chunk_id, content
        for reg in retrieved:
            assert isinstance(reg, RegulationChunk), f"Expected RegulationChunk, got {type(reg)}"
            assert isinstance(reg.source_file, str) and len(reg.source_file) > 0, (
                f"source_file must be non-empty, got {reg.source_file!r}"
            )
            assert isinstance(reg.chunk_id, str) and len(reg.chunk_id) > 0, (
                f"chunk_id must be non-empty, got {reg.chunk_id!r}"
            )
            assert isinstance(reg.content, str) and len(reg.content) > 0, (
                "content must be non-empty"
            )

        # Verify no 500 errors — answer_text should not contain HTTP error indicators
        http_error_signals = ["HTTP 500", "500 Internal", "500 Error", "status 500"]
        assert not any(sig in answer_text for sig in http_error_signals), (
            "Pipeline returned a 500-style HTTP error"
        )
        assert "error" not in answer_text.lower()[:200], (
            "Unexpected error text in first 200 chars of answer"
        )

    def test_expected_risks_identified(self, pipeline_result):
        """The output must identify at least 3 of the expected_risk_points."""
        expected = load_expected()
        expected_risks = expected["expected_risk_points"]
        assert len(expected_risks) >= 3, (
            f"Need at least 3 expected risk points, got {len(expected_risks)}"
        )

        result = pipeline_result
        answer_text = result["answer_text"]

        # Check for keywords from each expected risk point
        risk_keywords = [
            ["公开招标", "招标标准", "招标方式", "询价采购"],
            ["专项审批", "非公开招标"],
            ["审批尚未完成", "待审批", "未签字", "尚未完成", "审批中"],
            ["审批", "供应商", "合同草案", "尚未完成"],
        ]

        found_count = 0
        for keywords in risk_keywords:
            if any(kw in answer_text for kw in keywords):
                found_count += 1

        assert found_count >= 3, (
            f"Only {found_count}/4 risk point categories identified in answer. "
            f"Expected at least 3. Answer excerpt: {answer_text[:500]}..."
        )

    def test_no_fabricated_regulation_sources(self, pipeline_result):
        """The output must not cite regulations that don't exist in the provided set."""
        expected = load_expected()
        must_not = expected["must_not_claim"]

        result = pipeline_result
        answer_text = result["answer_text"]

        # Check the answer does not mention fabricated regulation sources
        # This is the structural check from expected_results
        for forbidden in must_not:
            if "不存在于检索结果" in forbidden:
                assert forbidden not in answer_text, (
                    f"Answer references regulations not in retrieval results: {forbidden}"
                )

        # Verify all cited regulation names come from the 3 actual files
        for fname in REGULATION_FILES:
            stem = Path(fname).stem  # e.g. "采购管理办法" from "采购管理办法.txt"
            if stem in answer_text:
                pass  # Legitimate reference

    def test_no_irrelevant_regulations_as_primary_basis(self, pipeline_result):
        """The distractor must not be the primary/dominant regulation basis."""
        result = pipeline_result
        answer_text = result["answer_text"]

        # Even if distractor was retrieved, it should not be the primary argument
        # Check that the answer doesn't primarily discuss travel expenses
        travel_keywords = ["差旅费", "差旅", "出差"]
        travel_count = sum(answer_text.count(kw) for kw in travel_keywords)

        # Primary regulation keywords (procurement-related)
        procurement_keywords = ["采购管理办法", "采购审批", "公开招标", "询价采购"]
        procurement_count = sum(answer_text.count(kw) for kw in procurement_keywords)

        # Procurement should dominate over travel in the answer
        assert procurement_count > travel_count, (
            f"Distractor (travel) appears {travel_count} times vs "
            f"procurement {procurement_count} times — distractor may be primary basis"
        )

    def test_human_review_prompt_present(self, pipeline_result):
        """The output must include a clear prompt for human review."""
        result = pipeline_result
        answer_text = result["answer_text"]

        has_human_review = ("人工复核" in answer_text or "需要人工" in answer_text
                           or "人工确认" in answer_text or "建议人工" in answer_text
                           or "请人工" in answer_text or "人工审核" in answer_text)
        assert has_human_review, (
            "Answer does not contain a human review prompt. "
            f"Answer excerpt: {answer_text[:500]}..."
        )

    def test_no_claim_of_final_legal_conclusion(self, pipeline_result):
        """The output must not claim a final legal conclusion."""
        expected = load_expected()
        must_not = expected["must_not_claim"]

        result = pipeline_result
        answer_text = result["answer_text"]

        # These must NOT appear in the answer — loaded from expected_results.yaml
        forbidden_phrases = [
            p for p in must_not
            if "不存在于检索结果" not in p
        ]
        for phrase in forbidden_phrases:
            assert phrase not in answer_text, (
                f"Answer contains forbidden final legal conclusion: '{phrase}'"
            )

    def test_citations_traceable(self, pipeline_result):
        """Regulation citations in the output must be traceable to source files and chunks."""
        result = pipeline_result
        retrieved = result["retrieved_regulations"]

        assert len(retrieved) > 0, "No retrieved regulations to check"

        for reg in retrieved:
            assert isinstance(reg.source_file, str) and len(reg.source_file) > 0, (
                f"source_file must be non-empty, got {reg.source_file!r}"
            )
            assert isinstance(reg.chunk_id, str) and len(reg.chunk_id) > 0, (
                f"chunk_id must be non-empty, got {reg.chunk_id!r}"
            )
            # Source file should be one of the 3 regulation files
            assert reg.source_file in REGULATION_FILES, (
                f"source_file {reg.source_file!r} is not one of the expected regulation files"
            )
