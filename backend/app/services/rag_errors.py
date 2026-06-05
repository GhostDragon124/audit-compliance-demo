"""Production RAG error types with controlled error semantics.

No RandomProvider fallback — RAG_MODE=required means real embedding or failure.
"""


class RagServiceError(Exception):
    """Base error for production RAG pipeline failures."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.status_code = status_code
        super().__init__(message)


class EmbeddingConnectionError(RagServiceError):
    """Failed to connect to the embedding service."""

    def __init__(self, message: str = "无法连接嵌入服务") -> None:
        super().__init__(message, status_code=503)


class EmbeddingTimeoutError(RagServiceError):
    """Embedding service request timed out."""

    def __init__(self, message: str = "嵌入服务超时") -> None:
        super().__init__(message, status_code=504)


class EmbeddingServiceError(RagServiceError):
    """Embedding service returned an error response."""

    def __init__(self, message: str = "嵌入服务返回错误") -> None:
        super().__init__(message, status_code=502)


class CollectionMetadataMismatchError(RagServiceError):
    """ChromaDB collection metadata does not match expected values."""

    def __init__(self, message: str = "ChromaDB collection metadata 不匹配，请重建索引") -> None:
        super().__init__(message, status_code=500)
