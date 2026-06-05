"""Tests for production RAG integration (Slice 5).

These tests use mock HTTP for the embedding service and mock ChromaDB.
They run as part of default CI (no special marker).
"""

from pathlib import Path

import httpx
import pytest
from chromadb.errors import NotFoundError

from app.config import Settings
from app.schemas import AnalyzeResponse, ParsedFileSummary, RegulationChunk
from app.services.audit_engine import AuditEngine
from app.services.chroma_vector_store import (
    COLLECTION_METADATA,
    ChromaCollectionMetadataError,
    _validate_collection_metadata,
)
from app.services.llm_client import LLMClient
from app.services.rag_errors import (
    CollectionMetadataMismatchError,
    EmbeddingConnectionError,
    EmbeddingServiceError,
    EmbeddingTimeoutError,
    RagServiceError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeRetriever:
    """A mock retriever that returns controlled results."""

    def __init__(self, results: list[RegulationChunk] | None = None):
        self.results = results or []
        self.last_query: str | None = None
        self.last_top_k: int | None = None

    def retrieve(self, query: str, top_k: int = 5) -> list[RegulationChunk]:
        self.last_query = query
        self.last_top_k = top_k
        return self.results


class FailingRetriever:
    """A retriever that raises various errors for testing."""

    def __init__(self, error: Exception):
        self._error = error

    def retrieve(self, query: str, top_k: int = 5) -> list[RegulationChunk]:
        raise self._error


def make_engine(
    prompt_path: Path,
    settings: Settings | None = None,
) -> AuditEngine:
    if settings is None:
        settings = Settings(llm_api_key="")
    llm_client = LLMClient(settings)
    return AuditEngine(llm_client=llm_client, prompt_path=prompt_path, settings=settings)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRagDisabled:
    """When RAG_MODE=disabled, analyze() does NOT call retriever."""

    @pytest.mark.asyncio
    async def test_rag_disabled_skips_retrieval(self, prompt_path: Path) -> None:
        """RAG disabled — retriever is never called."""
        engine = make_engine(prompt_path)
        # Even with a retriever passed, rag_mode="disabled" means no retrieval
        fake = FakeRetriever([RegulationChunk(chunk_id="x", source_file="y", content="z")])
        result = await engine.analyze(
            question="test",
            parsed_files=[],
            retriever=fake,
        )
        assert fake.last_query is None  # retriever was NOT called
        assert result.retrieved_regulations == []

    @pytest.mark.asyncio
    async def test_rag_disabled_no_retriever_still_works(self, prompt_path: Path) -> None:
        """RAG disabled without retriever — works exactly like before."""
        engine = make_engine(prompt_path)
        result = await engine.analyze(question="test", parsed_files=[])
        assert isinstance(result, AnalyzeResponse)
        assert result.answer_text
        assert result.retrieved_regulations == []


class TestRagRequired:
    """When RAG_MODE=required, analyze() calls retriever and returns results."""

    @pytest.mark.asyncio
    async def test_rag_required_calls_retriever(self, prompt_path: Path) -> None:
        """RAG required — retriever.retrieve() is called with query."""
        settings = Settings(llm_api_key="", rag_mode="required")
        engine = make_engine(prompt_path, settings)
        fake = FakeRetriever([
            RegulationChunk(chunk_id="c1", source_file="reg.txt", content="制度内容"),
        ])

        result = await engine.analyze(
            question="请分析风险",
            parsed_files=[],
            retriever=fake,
        )

        assert fake.last_query is not None
        assert "请分析风险" in fake.last_query
        assert fake.last_top_k == 5
        assert len(result.retrieved_regulations) == 1
        assert result.retrieved_regulations[0].source_file == "reg.txt"

    @pytest.mark.asyncio
    async def test_rag_required_no_retriever_falls_back(self, prompt_path: Path) -> None:
        """RAG required but no retriever passed — falls back to no retrieval (graceful)."""
        settings = Settings(llm_api_key="", rag_mode="required")
        engine = make_engine(prompt_path, settings)
        result = await engine.analyze(question="test", parsed_files=[])
        assert result.retrieved_regulations == []

    @pytest.mark.asyncio
    async def test_no_related_regulations_empty_result(self, prompt_path: Path) -> None:
        """Empty result is NOT treated as provider failure — empty list is valid."""
        settings = Settings(llm_api_key="", rag_mode="required")
        engine = make_engine(prompt_path, settings)
        fake = FakeRetriever([])  # No results found

        result = await engine.analyze(
            question="test",
            parsed_files=[],
            retriever=fake,
        )

        assert isinstance(result, AnalyzeResponse)
        assert result.retrieved_regulations == []  # Empty, not an error


class TestRagErrors:
    """Controlled error semantics — no RandomProvider fallback."""

    @pytest.mark.asyncio
    async def test_rag_required_connection_failure(self, prompt_path: Path) -> None:
        """httpx.ConnectError → EmbeddingConnectionError (503)."""
        settings = Settings(llm_api_key="", rag_mode="required")
        engine = make_engine(prompt_path, settings)
        retriever = FailingRetriever(httpx.ConnectError("Connection refused"))

        with pytest.raises(EmbeddingConnectionError) as exc_info:
            await engine.analyze(question="test", parsed_files=[], retriever=retriever)

        assert exc_info.value.status_code == 503
        assert "无法连接嵌入服务" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rag_required_timeout_failure(self, prompt_path: Path) -> None:
        """httpx.TimeoutException → EmbeddingTimeoutError (504)."""
        settings = Settings(llm_api_key="", rag_mode="required")
        engine = make_engine(prompt_path, settings)
        retriever = FailingRetriever(httpx.TimeoutException("Timed out"))

        with pytest.raises(EmbeddingTimeoutError) as exc_info:
            await engine.analyze(question="test", parsed_files=[], retriever=retriever)

        assert exc_info.value.status_code == 504
        assert "嵌入服务超时" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rag_required_http_error(self, prompt_path: Path) -> None:
        """httpx.HTTPStatusError → EmbeddingServiceError (502)."""
        settings = Settings(llm_api_key="", rag_mode="required")
        engine = make_engine(prompt_path, settings)
        response = httpx.Response(status_code=502, request=httpx.Request("POST", "http://test/"))
        retriever = FailingRetriever(httpx.HTTPStatusError("Bad gateway", request=response.request, response=response))

        with pytest.raises(EmbeddingServiceError) as exc_info:
            await engine.analyze(question="test", parsed_files=[], retriever=retriever)

        assert exc_info.value.status_code == 502
        assert "嵌入服务返回错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rag_chroma_collection_not_found(self, prompt_path: Path) -> None:
        """Chroma NotFoundError → CollectionMetadataMismatchError (500)."""
        settings = Settings(llm_api_key="", rag_mode="required")
        engine = make_engine(prompt_path, settings)
        retriever = FailingRetriever(NotFoundError("Collection not found"))

        with pytest.raises(CollectionMetadataMismatchError) as exc_info:
            await engine.analyze(question="test", parsed_files=[], retriever=retriever)

        assert exc_info.value.status_code == 500
        assert "ChromaDB collection not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rag_generic_error_wrapped(self, prompt_path: Path) -> None:
        """Unknown retriever error → RagServiceError (500)."""
        settings = Settings(llm_api_key="", rag_mode="required")
        engine = make_engine(prompt_path, settings)
        retriever = FailingRetriever(RuntimeError("Unexpected error"))

        with pytest.raises(RagServiceError) as exc_info:
            await engine.analyze(question="test", parsed_files=[], retriever=retriever)

        assert exc_info.value.status_code == 500
        assert "检索服务错误" in str(exc_info.value)


class TestBuildRetrievalQuery:
    """_build_retrieval_query constructs query from question + file content."""

    @pytest.mark.asyncio
    async def test_question_only(self, prompt_path: Path) -> None:
        engine = make_engine(prompt_path)
        query = engine._build_retrieval_query("请分析风险", [])
        assert query == "请分析风险"

    @pytest.mark.asyncio
    async def test_with_file_content(self, prompt_path: Path) -> None:
        engine = make_engine(prompt_path)
        files = [
            ParsedFileSummary(filename="doc1.txt", status="parsed", preview="合同内容略", error=None),
        ]
        query = engine._build_retrieval_query("请分析风险", files)
        assert "请分析风险" in query
        assert "合同内容略" in query

    @pytest.mark.asyncio
    async def test_max_chars_enforced(self, prompt_path: Path) -> None:
        engine = make_engine(prompt_path)
        long_text = "A" * 3000
        files = [ParsedFileSummary(filename="long.txt", status="parsed", preview=long_text, error=None)]
        query = engine._build_retrieval_query("Q", files, max_chars=100)
        assert len(query) == 100


class TestCollectionMetadata:
    """Collection metadata validation."""

    def test_collection_metadata_has_collection_role(self) -> None:
        assert "collection_role" in COLLECTION_METADATA
        assert COLLECTION_METADATA["collection_role"] == "production_regulations"

    def test_production_metadata_mismatch_is_rejected(self) -> None:
        """Mismatched metadata raises ChromaCollectionMetadataError."""
        bad_metadata = {**COLLECTION_METADATA, "embedding_dimension": 384}
        with pytest.raises(ChromaCollectionMetadataError, match="rebuild the index"):
            _validate_collection_metadata("regulations", bad_metadata)

    def test_correct_metadata_passes(self) -> None:
        """Matching metadata passes validation."""
        # Should not raise
        _validate_collection_metadata("regulations", dict(COLLECTION_METADATA))

    def test_production_collection_is_not_case001_collection(self) -> None:
        """Production collection has collection_role=production_regulations,
        which distinguishes it from any Case 001 test collection."""
        assert COLLECTION_METADATA["collection_role"] == "production_regulations"
        assert COLLECTION_METADATA["embedding_model"] == "Qwen3-Embedding-4B"
        assert COLLECTION_METADATA["embedding_dimension"] == 2560


class TestApiAnalyze:
    """Integration tests via HTTP client."""

    @pytest.mark.asyncio
    async def test_api_analyze_returns_retrieved_regulations(
        self,
        client: httpx.AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """POST /api/analyze with RAG_MODE=required returns regulations in response."""
        # Patch settings to enable RAG
        rag_settings = Settings(
            llm_api_key="",
            rag_mode="required",
        )
        monkeypatch.setattr("app.main.get_settings", lambda: rag_settings)

        # Patch VectorRetriever to use our fake
        fake = FakeRetriever([
            RegulationChunk(chunk_id="c1", source_file="policy.txt", content="制度内容"),
        ])
        monkeypatch.setattr("app.main.VectorRetriever", lambda persist_dir, collection_name, embedding_client: fake)

        response = await client.post(
            "/api/analyze",
            data={"question": "请分析风险"},
            files=[],
        )

        assert response.status_code == 200
        data = response.json()
        assert "retrieved_regulations" in data
        assert len(data["retrieved_regulations"]) == 1
        assert data["retrieved_regulations"][0]["source_file"] == "policy.txt"

    @pytest.mark.asyncio
    async def test_api_analyze_rag_disabled_no_regulations(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        """POST /api/analyze with default RAG_MODE=disabled returns empty regulations."""
        response = await client.post(
            "/api/analyze",
            data={"question": "请分析风险"},
            files=[],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["retrieved_regulations"] == []
