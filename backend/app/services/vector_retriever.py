from typing import Protocol

import chromadb

from app.schemas import RegulationChunk
from app.services.chroma_vector_store import get_or_create_regulation_collection


class EmbeddingTextClient(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


class VectorRetriever:
    def __init__(self, persist_dir, collection_name, embedding_client: EmbeddingTextClient) -> None:
        self.chroma_client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = get_or_create_regulation_collection(self.chroma_client, collection_name)
        self.embedding_client = embedding_client

    def retrieve(self, query: str, top_k: int = 5) -> list[RegulationChunk]:
        if top_k <= 0:
            return []

        query_embedding = self.embedding_client.embed_texts([query])[0]
        results = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)

        ids = results.get("ids", [[]])[0] or []
        documents = results.get("documents", [[]])[0] or []
        metadatas = results.get("metadatas", [[]])[0] or []
        distances = results.get("distances", [[]])[0] or []

        chunks: list[RegulationChunk] = []
        for index, chunk_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
            chunks.append(
                RegulationChunk(
                    chunk_id=str(chunk_id),
                    source_file=str(metadata.get("source_file", "")),
                    content=str(documents[index] if index < len(documents) and documents[index] else ""),
                    score=float(distances[index]) if index < len(distances) and distances[index] is not None else None,
                    metadata=dict(metadata),
                )
            )
        return chunks
