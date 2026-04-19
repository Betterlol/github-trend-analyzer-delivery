from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GitHub Trend Analyzer"
    github_token: str | None = None
    github_api_base: str = "https://api.github.com"
    github_request_timeout_sec: int = 20
    github_max_pages: int = 2
    github_per_page: int = Field(default=50, ge=1, le=100)
    database_url: str = "sqlite:///./data/trend_analyzer.db"
    llm_enabled: bool = True
    llm_api_key: str | None = Field(default=None, validation_alias=AliasChoices("LLM_API_KEY", "OPENAI_API_KEY"))
    llm_base_url: str = Field(default="https://api.openai.com/v1", validation_alias=AliasChoices("LLM_BASE_URL", "OPENAI_BASE_URL"))
    llm_model: str = Field(default="gpt-4o-mini", validation_alias=AliasChoices("LLM_MODEL", "OPENAI_MODEL"))
    llm_timeout_sec: int = Field(default=45, ge=5, le=180)
    llm_max_retries: int = Field(default=2, ge=0, le=5)


@lru_cache
def get_settings() -> Settings:
    return Settings()
