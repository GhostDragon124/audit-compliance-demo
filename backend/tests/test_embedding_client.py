import pytest

from app.config import Settings
from app.services import embedding_client as embedding_module
from app.services.embedding_client import EmbeddingClient


def test_settings_default_embedding_provider_is_random() -> None:
    assert Settings().embedding_provider == "random"


def test_random_provider_returns_reproducible_384_dim_vectors() -> None:
    client = EmbeddingClient(provider="random")

    embeddings = client.embed_texts(["alpha", "beta", "alpha"])
    repeated_embeddings = EmbeddingClient(provider="random").embed_texts(["alpha", "beta"])

    assert len(embeddings) == 3
    assert all(len(embedding) == 384 for embedding in embeddings)
    assert embeddings[0] == embeddings[2]
    assert embeddings[:2] == repeated_embeddings
    assert embeddings[0] != embeddings[1]


def test_embed_empty_list_returns_empty() -> None:
    client = EmbeddingClient(provider="random")

    embeddings = client.embed_texts([])

    assert embeddings == []


def test_openai_compatible_provider_calls_embeddings_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "data": [
                    {"index": 1, "embedding": [3, 4.5]},
                    {"index": 0, "embedding": [1, 2]},
                ]
            }

    def fake_post(**kwargs):
        calls.append(kwargs)
        return FakeResponse()

    monkeypatch.setattr(embedding_module.httpx, "post", fake_post)
    client = EmbeddingClient(
        provider="openai_compatible",
        model="mock-embedding-model",
        base_url="http://localhost:8083/v1/",
        api_key="test-key",
    )

    embeddings = client.embed_texts(["alpha", "beta"])

    assert embeddings == [[1.0, 2.0], [3.0, 4.5]]
    assert calls == [
        {
            "url": "http://localhost:8083/v1/embeddings",
            "json": {"model": "mock-embedding-model", "input": ["alpha", "beta"]},
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer test-key",
            },
            "timeout": 60.0,
        }
    ]


def test_openai_compatible_response_count_mismatch_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"data": [{"index": 0, "embedding": [1, 2]}]}

    monkeypatch.setattr(embedding_module.httpx, "post", lambda **kwargs: FakeResponse())
    client = EmbeddingClient(provider="openai_compatible")

    with pytest.raises(ValueError, match="response count"):
        client.embed_texts(["alpha", "beta"])


def test_invalid_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        EmbeddingClient(provider="invalid-provider")
