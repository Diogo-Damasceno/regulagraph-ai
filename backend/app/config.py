from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RegulaGraph AI"
    database_url: str = "sqlite:///./regulagraph.db"
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "regulagraph123"
    llm_provider: str = "heuristic"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    upload_dir: str = "uploads"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
