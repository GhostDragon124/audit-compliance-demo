from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_mode: str = "mock"
    llm_base_url: str = "http://127.0.0.1:8083/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen3.6-35b-a3b-fp8"
    llm_timeout: float = 120.0
    llm_max_prompt_chars: int = 24000
    llm_truncation_prompt_template: str = (
        "\n\n[分析范围提示]\n"
        "以下材料已被截断：原始 {original_chars} 字符，本次分析使用前 {used_chars} 字符。\n"
    )

    ocr_provider: str = "paddleocr"
    ocr_device: str = "cpu"
    ocr_lang: str = "ch"
    ocr_enable: bool = True

    embedding_provider: str = "openai_compatible"
    embedding_model: str = "/models"
    embedding_base_url: str = "http://127.0.0.1:8085/v1"
    chroma_persist_dir: str = "../data/indexes/chroma/regulations"
    chroma_collection_name: str = "regulations"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    rag_mode: str = "disabled"  # "disabled" | "required"
    rag_top_k: int = 5

    max_file_size_mb: int = 50
    max_total_upload_mb: int = 100
    max_files_per_request: int = 10
    pdf_max_pages: int = 100
    image_max_pixels: int = 50_000_000
    upload_cleanup: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
