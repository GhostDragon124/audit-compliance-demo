from app.schemas import RegulationChunk


class VectorRetriever:
    """Placeholder retriever. M0+ intentionally returns no regulation chunks."""

    def retrieve(self, query: str, top_k: int = 5) -> list[RegulationChunk]:
        # TODO: Retrieve regulation chunks from ChromaDB after the vector index is implemented.
        return []
