"""
PetroSafe Energia - Configurações centralizadas
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_root_user: str = "petrosafe"
    minio_root_password: str = "petrosafe123"
    minio_secure: bool = False

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "petrosafe"
    postgres_user: str = "petrosafe"
    postgres_password: str = "petrosafe123"

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
