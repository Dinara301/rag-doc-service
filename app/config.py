from pathlib import Path
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CHAT_MODEL: str = "gpt-4o-mini"
EMBEDDING_MODEL: str = "text-embedding-3-small"

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_CHROMA_PATH: Path = PROJECT_ROOT / "data" / "chroma"


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables and a local `.env` file.

    Field names map to upper-case variables (`openai_api_key` -> `OPENAI_API_KEY`).
    Explicit constructor arguments override the environment, which keeps tests hermetic.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: SecretStr = SecretStr("")
    chat_model: str = CHAT_MODEL
    embedding_model: str = EMBEDDING_MODEL
    chroma_path: Path = DEFAULT_CHROMA_PATH
    chunk_size_tokens: int = Field(default=800, gt=0)
    chunk_overlap_tokens: int = Field(default=150, ge=0)
    max_file_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_request_bytes: int = Field(default=50 * 1024 * 1024, gt=0)
    allowed_extensions: frozenset[str] = frozenset({".pdf", ".md", ".markdown", ".txt"})
    openai_timeout_seconds: float = Field(default=30.0, gt=0)
    openai_max_retries: int = Field(default=2, ge=0, le=10)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = True
    metrics_enabled: bool = True

    @model_validator(mode="after")
    def _request_limit_fits_one_file(self) -> Self:
        """Reject a request limit smaller than the per-file limit (one file could never fit)."""
        if self.max_request_bytes < self.max_file_bytes:
            raise ValueError("max_request_bytes must be >= max_file_bytes")
        return self

    @property
    def openai_configured(self) -> bool:
        """Whether a non-empty OpenAI API key is set."""
        return bool(self.openai_api_key.get_secret_value())
