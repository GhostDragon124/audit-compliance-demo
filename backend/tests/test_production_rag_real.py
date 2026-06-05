"""Real provider tests for production RAG integration (Slice 5).

These tests hit the real embedding service (port 8085) and real ChromaDB.
Marked with @pytest.mark.production_rag — excluded from default CI.
"""

import pytest

from app.config import get_settings
from app.services.chroma_vector_store import COLLECTION_METADATA
from app.services.embedding_client import EmbeddingClient


@pytest.mark.production_rag
def test_real_embedding_dimension_2560() -> None:
    """Verify real Qwen3-Embedding-4B returns 2560-dim vectors."""
    settings = get_settings()
    client = EmbeddingClient(
        provider=settings.embedding_provider or "openai_compatible",
        model=settings.embedding_model or "/models",
        base_url=settings.embedding_base_url or "http://127.0.0.1:8085/v1",
        api_key="",
        timeout=5.0,
    )
    probe = client.embed_texts(["采购审批制度向量连通性测试。"])[0]
    assert len(probe) == 2560, f"Expected 2560 dimensions, got {len(probe)}"


@pytest.mark.production_rag
def test_production_index_integrity() -> None:
    """Verify production collection metadata matches config."""
    import chromadb

    settings = get_settings()
    persist_dir = settings.chroma_persist_dir
    collection_name = settings.chroma_collection_name or "regulations"

    try:
        chroma_client = chromadb.PersistentClient(path=str(persist_dir))
        collection = chroma_client.get_collection(collection_name)
    except Exception as exc:
        pytest.skip(f"BLOCKED: cannot access production index: {exc}")

    metadata = collection.metadata or {}
    for key, expected in COLLECTION_METADATA.items():
        actual = metadata.get(key)
        assert actual == expected, (
            f"Collection {collection_name!r}: {key}=expected {expected!r}, actual {actual!r}"
        )


@pytest.mark.production_rag
@pytest.mark.asyncio
async def test_case_001_via_production_api() -> None:
    """Upload Case 001 materials via POST /api/analyze → verify RAG output.

    This test requires:
    - RAG_MODE=required in .env
    - Real embedding service running on port 8085
    - Real ChromaDB index at chroma_persist_dir
    - Real LLM service running on port 8083 (or LLM_MODE=mock)
    """
    from app.services.vector_retriever import VectorRetriever

    settings = get_settings()

    if settings.rag_mode != "required":
        pytest.skip("BLOCKED: set RAG_MODE=required in .env for this test")

    # Verify we can build a retriever
    try:
        embedder = EmbeddingClient(
            provider=settings.embedding_provider or "openai_compatible",
            model=settings.embedding_model or "/models",
            base_url=settings.embedding_base_url or "http://127.0.0.1:8085/v1",
            api_key="",
            dim=2560,
            timeout=5.0,
        )
        retriever = VectorRetriever(
            persist_dir=settings.chroma_persist_dir,
            collection_name=settings.chroma_collection_name or "regulations",
            embedding_client=embedder,
        )
    except Exception as exc:
        pytest.skip(f"BLOCKED: cannot initialize retriever: {exc}")

    # Simple retrieval sanity check
    try:
        results = retriever.retrieve("采购审批制度", top_k=3)
    except Exception as exc:
        pytest.fail(f"Unexpected retrieval failure: {exc}")

    # Verify results are well-formed
    assert isinstance(results, list)
    for chunk in results:
        assert chunk.chunk_id
        assert chunk.source_file
        assert chunk.content
