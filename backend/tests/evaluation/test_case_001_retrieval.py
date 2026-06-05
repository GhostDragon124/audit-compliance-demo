"""
Slice 4A: Case 001 Retrieval Test Skeleton (STRICT XFAIL)

Tests that the VectorRetriever can retrieve relevant regulations for Case 001.
Real implementation requires VectorRetriever with isolated test index.
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


def load_manifest():
    import json

    path = CASE_ROOT / "manifest.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Tests ────────────────────────────────────────────────────────────


class TestRetrieval4A:
    """4A: Retrieval integration tests (strict xfail until implementation)."""

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4A: VectorRetriever not yet integrated with isolated test index",
    )
    def test_build_isolated_index_and_retrieve_top5(self):
        """
        Build an isolated test index (ChromaDB) for Case 001 regulations,
        then verify VectorRetriever returns exactly Top-5 results.
        """
        expected = load_expected()
        top_k = expected["retrieval_expectations"]["top_k"]
        assert top_k == 5, (
            f"Expected top_k=5, got {top_k}"
        )

        # ── When real implementation is done: ──
        # 1. Create temp ChromaDB collection for case 001 regulations
        # 2. Chunk and embed: 采购管理办法.txt, 采购审批管理规定.txt, 差旅费管理规定.txt
        # 3. Query with a question about procurement approval
        # 4. Assert exactly top_k results returned
        # 5. Assert each result has source_file, chunk_id, content, score/distance
        raise NotImplementedError(
            "Requires VectorRetriever with isolated ChromaDB test index"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4A: relevant regulations must appear in Top-5",
    )
    def test_relevant_regulations_in_top5(self):
        """
        Both relevant regulations (采购管理办法.txt, 采购审批管理规定.txt)
        must be in the Top-5 retrieval results.
        """
        expected = load_expected()
        must_retrieve = expected["retrieval_expectations"]["must_retrieve"]
        assert len(must_retrieve) == 2

        # ── When real implementation is done: ──
        # results = retriever.retrieve(question, top_k=5)
        # retrieved_files = {r.source_file for r in results}
        # for fname in must_retrieve:
        #     assert fname in retrieved_files, f"{fname} not in Top-5"
        raise NotImplementedError(
            "Requires VectorRetriever with indexed case regulations"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4A: irrelevant distractor should not rank high",
    )
    def test_irrelevant_distractor_not_primary(self):
        """
        The irrelevant distractor (差旅费管理规定.txt) should not be a
        primary result (e.g., not in top 2 positions).
        """
        expected = load_expected()
        distractors = expected["retrieval_expectations"]["should_not_rank_high"]
        assert len(distractors) >= 1

        # ── When real implementation is done: ──
        # results = retriever.retrieve(question, top_k=5)
        # top2_files = {r.source_file for r in results[:2]}
        # for fname in distractors:
        #     assert fname not in top2_files, f"{fname} ranked too high"
        raise NotImplementedError(
            "Requires VectorRetriever with indexed case regulations"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="SLICE-4A: result items must contain required fields",
    )
    def test_retrieval_results_have_required_fields(self):
        """
        Retrieved items must contain source_file, chunk_id, content, and
        score/distance metadata.
        """
        # ── When real implementation is done: ──
        # results = retriever.retrieve(question, top_k=5)
        # for r in results:
        #     assert hasattr(r, 'source_file')
        #     assert hasattr(r, 'chunk_id')
        #     assert hasattr(r, 'content')
        #     assert hasattr(r, 'score') or hasattr(r, 'distance')
        raise NotImplementedError(
            "Requires VectorRetriever with proper result schema"
        )
