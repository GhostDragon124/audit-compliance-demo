from pathlib import Path

import httpx
import pytest

from app.config import Settings
from app.services import regulation_indexer as indexer_module
from app.services.chroma_vector_store import COLLECTION_METADATA, ChromaCollectionMetadataError
from app.services.embedding_client import EmbeddingClient
from app.services.regulation_indexer import RegulationIndexer
from chromadb.errors import NotFoundError


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.text_batches: list[list[str]] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.text_batches.append(texts)
        return [[float(index), 0.0, 1.0] for index, _ in enumerate(texts)]


class FakeCollection:
    def __init__(self, metadata: dict[str, object] | None = None) -> None:
        self.metadata = metadata or {}
        self.add_calls: list[dict[str, object]] = []

    def add(self, *, ids, documents, embeddings, metadatas) -> None:
        self.add_calls.append(
            {
                "ids": ids,
                "documents": documents,
                "embeddings": embeddings,
                "metadatas": metadatas,
            }
        )


class FakePersistentClient:
    collection = FakeCollection()
    existing_collection: FakeCollection | None = None
    init_paths: list[str] = []
    collection_names: list[str] = []
    collection_metadata: list[dict[str, object] | None] = []

    def __init__(self, path: str) -> None:
        self.init_paths.append(path)

    def get_collection(self, name: str) -> FakeCollection:
        if self.existing_collection is None:
            raise NotFoundError(f"Collection [{name}] does not exist")
        self.collection_names.append(name)
        return self.existing_collection

    def create_collection(self, name: str, metadata: dict[str, object] | None = None) -> FakeCollection:
        self.collection_names.append(name)
        self.collection_metadata.append(metadata)
        type(self).collection.metadata = dict(metadata or {})
        return type(self).collection


@pytest.fixture
def fake_chroma(monkeypatch: pytest.MonkeyPatch) -> FakeCollection:
    FakePersistentClient.collection = FakeCollection()
    FakePersistentClient.existing_collection = None
    FakePersistentClient.init_paths = []
    FakePersistentClient.collection_names = []
    FakePersistentClient.collection_metadata = []
    monkeypatch.setattr(indexer_module.chromadb, "PersistentClient", FakePersistentClient)
    return FakePersistentClient.collection


@pytest.fixture
def indexer_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    settings = Settings(chunk_size=1000, chunk_overlap=200)
    monkeypatch.setattr(indexer_module, "get_settings", lambda: settings)
    return settings


def make_indexer(raw_dir: Path, persist_dir: Path, embedding_client: FakeEmbeddingClient) -> RegulationIndexer:
    return RegulationIndexer(
        raw_dir=raw_dir,
        persist_dir=persist_dir,
        collection_name="test_regulations",
        embedding_client=embedding_client,
    )


def test_build_index_returns_chunk_count(
    tmp_path: Path,
    fake_chroma: FakeCollection,
    indexer_settings: Settings,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "policy_2024.txt").write_text(
        "第一段采购审批制度。\n\n" "第二段供应商准入制度。\n\n" "第三段付款复核制度。",
        encoding="utf-8",
    )
    embedding_client = FakeEmbeddingClient()

    count = make_indexer(raw_dir, tmp_path / "chroma", embedding_client).build_index()

    assert count == 1
    assert len(fake_chroma.add_calls) == 1
    assert fake_chroma.add_calls[0]["documents"] == embedding_client.text_batches[0]
    assert FakePersistentClient.init_paths == [str(tmp_path / "chroma")]
    assert FakePersistentClient.collection_names == ["test_regulations"]


def test_collection_metadata_is_written(
    tmp_path: Path,
    fake_chroma: FakeCollection,
    indexer_settings: Settings,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    make_indexer(raw_dir, tmp_path / "chroma", FakeEmbeddingClient())

    assert FakePersistentClient.collection_metadata == [COLLECTION_METADATA]
    assert fake_chroma.metadata == COLLECTION_METADATA


def test_collection_metadata_mismatch_requires_rebuild(
    tmp_path: Path,
    fake_chroma: FakeCollection,
    indexer_settings: Settings,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    FakePersistentClient.existing_collection = FakeCollection({**COLLECTION_METADATA, "embedding_dimension": 384})

    with pytest.raises(ChromaCollectionMetadataError, match="rebuild the index"):
        make_indexer(raw_dir, tmp_path / "chroma", FakeEmbeddingClient())


def test_chunk_metadata_has_source_file(
    tmp_path: Path,
    fake_chroma: FakeCollection,
    indexer_settings: Settings,
) -> None:
    raw_dir = tmp_path / "raw"
    nested_dir = raw_dir / "regulations"
    nested_dir.mkdir(parents=True)
    (nested_dir / "finance_2023.txt").write_text("财务报销制度。", encoding="utf-8")

    count = make_indexer(raw_dir, tmp_path / "chroma", FakeEmbeddingClient()).build_index()

    assert count == 1
    metadata = fake_chroma.add_calls[0]["metadatas"][0]
    assert metadata == {
        "source_file": "regulations/finance_2023.txt",
        "chunk_index": 0,
        "year_hint": "2023",
    }


def test_empty_dir_returns_zero(
    tmp_path: Path,
    fake_chroma: FakeCollection,
    indexer_settings: Settings,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    count = make_indexer(raw_dir, tmp_path / "chroma", FakeEmbeddingClient()).build_index()

    assert count == 0
    assert fake_chroma.add_calls == []


def test_unsupported_skipped(
    tmp_path: Path,
    fake_chroma: FakeCollection,
    indexer_settings: Settings,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "unsupported.bin").write_bytes(b"not indexed")

    count = make_indexer(raw_dir, tmp_path / "chroma", FakeEmbeddingClient()).build_index()

    assert count == 0
    assert fake_chroma.add_calls == []


def test_doc_conversion(
    tmp_path: Path,
    fake_chroma: FakeCollection,
    indexer_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    doc_path = raw_dir / "legacy_2019.doc"
    doc_path.write_bytes(b"legacy doc")
    calls = []

    def fake_run(command, *, check, timeout) -> None:
        calls.append({"command": command, "check": check, "timeout": timeout})
        outdir = Path(command[command.index("--outdir") + 1])
        (outdir / "legacy_2019.txt").write_text("旧版制度正文。", encoding="utf-8")

    monkeypatch.setattr(indexer_module.subprocess, "run", fake_run)

    count = make_indexer(raw_dir, tmp_path / "chroma", FakeEmbeddingClient()).build_index()

    assert count == 1
    assert calls == [
        {
            "command": [
                "libreoffice",
                "--headless",
                "--convert-to",
                "txt:Text",
                "--outdir",
                calls[0]["command"][5],
                str(doc_path),
            ],
            "check": True,
            "timeout": 120,
        }
    ]
    assert fake_chroma.add_calls[0]["documents"] == ["旧版制度正文。"]
    assert fake_chroma.add_calls[0]["metadatas"][0]["year_hint"] == "2019"


@pytest.mark.local_embedding
def test_build_index_with_real_embedding_client_writes_2560_vectors(tmp_path: Path) -> None:
    settings = Settings()
    if settings.embedding_provider != "openai_compatible":
        pytest.skip("BLOCKED: set EMBEDDING_PROVIDER=openai_compatible for real embedding validation.")

    embedding_client = EmbeddingClient(
        provider="openai_compatible",
        model=settings.embedding_model,
        base_url=settings.embedding_base_url,
        timeout=2.0,
    )
    try:
        probe = embedding_client.embed_texts(["采购审批制度向量连通性测试。"])[0]
    except httpx.TransportError as exc:
        pytest.skip(f"BLOCKED: embedding endpoint {settings.embedding_base_url} is not reachable: {exc}")

    assert len(probe) == 2560

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "policy_2026.txt").write_text("采购审批制度正文。", encoding="utf-8")

    indexer = RegulationIndexer(
        raw_dir=raw_dir,
        persist_dir=tmp_path / "chroma",
        collection_name="real_embedding_regulations",
        embedding_client=embedding_client,
    )

    assert indexer.build_index() == 1
    stored = indexer.collection.get(include=["embeddings"])
    assert len(stored["embeddings"][0]) == 2560

