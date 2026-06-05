import hashlib
import math
import random
from typing import Any

import httpx


DEFAULT_EMBEDDING_MODEL = "/models"
DEFAULT_OPENAI_COMPATIBLE_BASE_URL = "http://127.0.0.1:8085/v1"
DEFAULT_EMBEDDING_DIM = 2560


class RandomProvider:
    def __init__(self, dim: int = DEFAULT_EMBEDDING_DIM) -> None:
        self.dim = dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], "big")
        rng = random.Random(seed)
        vector = [rng.uniform(-1.0, 1.0) for _ in range(self.dim)]
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAICompatibleProvider:
    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        base_url: str = DEFAULT_OPENAI_COMPATIBLE_BASE_URL,
        api_key: str = "",
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        payload: dict[str, Any] = {
            "model": self.model,
            "input": texts,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = httpx.post(
            url=f"{self.base_url}/embeddings",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()["data"]
        if all("index" in item for item in data):
            data = sorted(data, key=lambda item: item["index"])

        embeddings = [item["embedding"] for item in data]
        if len(embeddings) != len(texts):
            raise ValueError("Embedding response count does not match input count")
        return [[float(value) for value in embedding] for embedding in embeddings]


class EmbeddingClient:
    def __init__(
        self,
        provider: str = "openai_compatible",
        model: str = DEFAULT_EMBEDDING_MODEL,
        base_url: str = DEFAULT_OPENAI_COMPATIBLE_BASE_URL,
        api_key: str = "",
        dim: int = DEFAULT_EMBEDDING_DIM,
        timeout: float = 60.0,
        model_name: str | None = None,
        device: str | None = None,
    ) -> None:
        if model_name is not None:
            model = model_name
        self.provider_name = provider
        self.device = device

        if provider == "openai_compatible":
            self._provider = OpenAICompatibleProvider(
                model=model,
                base_url=base_url,
                api_key=api_key,
                timeout=timeout,
            )
        elif provider == "random":
            self._provider = RandomProvider(dim=dim)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._provider.embed_texts(texts)
