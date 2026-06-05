from pathlib import Path

import pytest

from app.config import Settings
from app.services import regulation_indexer as indexer_module
from app.services.regulation_indexer import RegulationIndexer


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.text_batches: list[list[str]] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.text_batches.append(texts)
        return [[float(index), 0.0, 1.0] for index, _ in enumerate(texts)]


class FakeCollection:
    def __init__(self) -> None:
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
    init_paths: list[str] = []
    collection_names: list[str] = []

    def __init__(self, path: str) -> None:
        self.init_paths.append(path)

    def get_or_create_collection(self, name: str) -> FakeCollection:
        self.collection_names.append(name)
        return self.collection


@pytest.fixture
def fake_chroma(monkeypatch: pytest.MonkeyPatch) -> FakeCollection:
    FakePersistentClient.collection = FakeCollection()
    FakePersistentClient.init_paths = []
    FakePersistentClient.collection_names = []
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
