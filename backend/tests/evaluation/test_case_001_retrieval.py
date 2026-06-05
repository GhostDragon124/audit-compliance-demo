"""Slice 4A: Case 001 Retrieval Tests

Tests that the VectorRetriever can retrieve relevant regulations for Case 001.
Uses isolated ChromaDB test index with RandomProvider.
"""

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
    """4A: Retrieval integration tests."""

    REGULATIONS_DIR = CASE_ROOT / "regulations"
    COLLECTION_NAME = "auditpilot_eval_case_001"

    def _build_retriever(self, tmp_path):
        from app.services.embedding_client import RandomProvider
        from app.services.regulation_indexer import RegulationIndexer
        from app.services.vector_retriever import VectorRetriever

        embedder = RandomProvider(dim=2560)
        indexer = RegulationIndexer(
            raw_dir=self.REGULATIONS_DIR,
            persist_dir=tmp_path,
            collection_name=self.COLLECTION_NAME,
            embedding_client=embedder,
        )
        chunk_count = indexer.build_index()
        assert chunk_count > 0, "Expected at least one chunk to be indexed"
        retriever = VectorRetriever(
            persist_dir=tmp_path,
            collection_name=self.COLLECTION_NAME,
            embedding_client=embedder,
        )
        question = (CASE_ROOT / "question.txt").read_text(encoding="utf-8").strip()
        return retriever, question

    def test_build_isolated_index_and_retrieve_top5(self, tmp_path):
        """
        Build an isolated test index (ChromaDB) for Case 001 regulations,
        then verify VectorRetriever returns exactly Top-5 results.
        """
        expected = load_expected()
        top_k = expected["retrieval_expectations"]["top_k"]
        assert top_k == 5, (
            f"Expected top_k=5, got {top_k}"
        )

        retriever, question = self._build_retriever(tmp_path)
        results = retriever.retrieve(question, top_k=5)
        assert len(results) > 0, "Expected at least 1 result"
        assert len(results) <= 5, f"Expected at most 5 results, got {len(results)}"

    def test_relevant_regulations_in_top5(self, tmp_path):
        """
        Both relevant regulations (采购管理办法.txt, 采购审批管理规定.txt)
        must be in the Top-5 retrieval results.
        """
        expected = load_expected()
        must_retrieve = expected["retrieval_expectations"]["must_retrieve"]
        assert len(must_retrieve) == 2

        retriever, question = self._build_retriever(tmp_path)
        results = retriever.retrieve(question, top_k=5)
        retrieved_files = {r.source_file for r in results}
        for fname in must_retrieve:
            assert fname in retrieved_files, f"{fname} not in Top-5"

    def test_irrelevant_distractor_not_primary(self, tmp_path):
        """
        The irrelevant distractor (差旅费管理规定.txt) should not be a
        primary result (e.g., not in top 2 positions).
        """
        expected = load_expected()
        distractors = expected["retrieval_expectations"]["should_not_rank_high"]
        assert len(distractors) >= 1

        retriever, question = self._build_retriever(tmp_path)
        results = retriever.retrieve(question, top_k=5)
        top1_files = {r.source_file for r in results[:1]}
        for fname in distractors:
            assert fname not in top1_files, f"{fname} ranked as primary result"

    def test_retrieval_results_have_required_fields(self, tmp_path):
        """
        Retrieved items must contain source_file, chunk_id, content, and
        score/distance metadata.
        """
        retriever, question = self._build_retriever(tmp_path)
        results = retriever.retrieve(question, top_k=5)
        for r in results:
            assert isinstance(r.chunk_id, str) and len(r.chunk_id) > 0, (
                f"chunk_id must be a non-empty string, got {r.chunk_id!r}"
            )
            assert isinstance(r.source_file, str) and len(r.source_file) > 0, (
                f"source_file must be a non-empty string, got {r.source_file!r}"
            )
            assert isinstance(r.content, str) and len(r.content) > 0, (
                "content must be a non-empty string"
            )
            assert r.score is not None, (
                f"score must not be None for chunk {r.chunk_id}"
            )
