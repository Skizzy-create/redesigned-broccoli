from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Smart Document Q&A API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    api_key: str = "dev-api-key"
    database_url: str = "postgresql+asyncpg://smartdoc:smartdoc@localhost:5432/smartdocqa"
    max_workers: int = 4
    max_pending_tasks: int = 1000
    max_upload_size_mb: int = 50
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    celery_task_always_eager: bool = False
    celery_task_store_eager_result: bool = True
    upload_dir: str = "data/uploads"
    index_dir: str = "data/indexes"
    top_k_retrieval: int = 20
    top_n_rerank: int = 5
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 64
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    llm_provider: str = "openai"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    max_context_tokens: int = 5000
    response_max_tokens: int = 800
    rag_max_cycles: int = 2
    rag_min_confidence: float = 0.55


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for dependency injection."""

    return Settings()
