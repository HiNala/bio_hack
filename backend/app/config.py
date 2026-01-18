"""
Application Configuration

Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "ScienceRAG"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://sciencerag:sciencerag@localhost:5432/sciencerag"

    # OpenAI Configuration
    openai_api_key: str = ""
    
    # Embedding model: text-embedding-3-small is best value
    # - 1536 dimensions, excellent for semantic search
    # - Much cheaper than text-embedding-3-large
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Chat/completion model for query parsing and synthesis
    # gpt-4o-mini: Best value for most tasks, fast
    # gpt-4o: Use for complex synthesis if needed
    openai_chat_model: str = "gpt-4o-mini"

    # Anthropic (optional - for synthesis, uses OpenAI if not set)
    anthropic_api_key: str = ""
    synthesis_model: str = "claude-sonnet-4-20250514"

    # Literature APIs
    openalex_email: str = ""  # Optional, for polite pool
    semantic_scholar_api_key: str = ""  # Optional, for higher rate limits

    # RAG Configuration
    chunk_size: int = 500  # tokens
    chunk_overlap: int = 50  # tokens
    retrieval_top_k: int = 20
    context_top_n: int = 10

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
