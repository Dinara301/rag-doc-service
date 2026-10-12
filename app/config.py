import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

CHAT_MODEL: str = "gpt-4o-mini"
EMBEDDING_MODEL: str = "text-embedding-3-small"

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_CHROMA_PATH: Path = PROJECT_ROOT / "data" / "chroma"


class Settings(BaseModel):
    openai_api_key: str = ""
    chat_model: str = CHAT_MODEL
    embedding_model: str = EMBEDDING_MODEL
    chroma_path: Path = DEFAULT_CHROMA_PATH
    chunk_size_tokens: int = 800
    chunk_overlap_tokens: int = 150
    max_file_bytes: int = 10 * 1024 * 1024
    allowed_extensions: frozenset[str] = Field(
        default_factory=lambda: frozenset({".pdf", ".md", ".markdown", ".txt"})
    )


def load_settings() -> Settings:
    load_dotenv()
    return Settings(openai_api_key=os.getenv("OPENAI_API_KEY", ""))
