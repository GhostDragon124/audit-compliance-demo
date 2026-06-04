from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_base_url: str = "http://your-qwen-api-server/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen3"

    ocr_provider: str = "paddleocr"
    ocr_device: str = "cpu"
    ocr_lang: str = "ch"
    ocr_enable: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
