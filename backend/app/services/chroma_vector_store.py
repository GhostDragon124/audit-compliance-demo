from typing import Any

from chromadb.errors import NotFoundError


COLLECTION_METADATA: dict[str, str | int] = {
    "embedding_model": "Qwen3-Embedding-4B",
    "embedding_dimension": 2560,
    "distance_metric": "cosine",
    "chunk_strategy_version": "1.0",
    "index_schema_version": "1.0",
    "collection_role": "production_regulations",
}


class ChromaCollectionMetadataError(ValueError):
    pass


def get_or_create_regulation_collection(chroma_client: Any, collection_name: str) -> Any:
    get_collection = getattr(chroma_client, "get_collection", None)
    if get_collection is None:
        collection = chroma_client.get_or_create_collection(
            collection_name,
            metadata=COLLECTION_METADATA,
        )
    else:
        try:
            collection = get_collection(collection_name)
        except NotFoundError:
            collection = chroma_client.create_collection(
                collection_name,
                metadata=COLLECTION_METADATA,
            )

    _validate_collection_metadata(collection_name, collection.metadata or {})
    return collection


def _validate_collection_metadata(collection_name: str, metadata: dict[str, Any]) -> None:
    mismatches = {
        key: {"expected": expected, "actual": metadata.get(key)}
        for key, expected in COLLECTION_METADATA.items()
        if metadata.get(key) != expected
    }
    if not mismatches:
        return

    details = ", ".join(
        f"{key}=expected {values['expected']!r}, actual {values['actual']!r}"
        for key, values in mismatches.items()
    )
    raise ChromaCollectionMetadataError(
        f"Chroma collection {collection_name!r} metadata mismatch; rebuild the index. {details}"
    )
