from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from app.config import CHAT_MODEL, DEFAULT_CHROMA_PATH, Settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate each test from the developer's real environment and `.env` file."""
    for name in ("OPENAI_API_KEY", "CHAT_MODEL", "CHROMA_PATH", "MAX_FILE_BYTES"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


def test_defaults_without_env() -> None:
    """With no environment, defaults apply and OpenAI is reported as not configured."""
    settings = Settings()

    assert settings.chat_model == CHAT_MODEL
    assert settings.chroma_path == DEFAULT_CHROMA_PATH
    assert settings.openai_configured is False


def test_reads_environment_variables(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Upper-case env vars populate the matching fields and are parsed to their types."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    monkeypatch.setenv("MAX_FILE_BYTES", "2048")
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma-x"))

    settings = Settings()

    assert settings.openai_api_key.get_secret_value() == "sk-from-env"
    assert settings.openai_configured is True
    assert settings.max_file_bytes == 2048
    assert settings.chroma_path == tmp_path / "chroma-x"


def test_reads_dotenv_file(tmp_path: Path) -> None:
    """Values in a `.env` file in the working directory are loaded; unknown keys are ignored."""
    (tmp_path / ".env").write_text("OPENAI_API_KEY=sk-from-file\nUNRELATED=1\n")

    assert Settings().openai_api_key.get_secret_value() == "sk-from-file"


def test_constructor_argument_overrides_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit arguments win over the environment, which keeps tests hermetic."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")

    assert Settings(openai_api_key=SecretStr("")).openai_configured is False


def test_api_key_is_masked_in_repr() -> None:
    """The secret never appears in `repr` or `str`, so it cannot leak into logs."""
    settings = Settings(openai_api_key=SecretStr("sk-very-secret"))

    assert "sk-very-secret" not in repr(settings)
    assert "sk-very-secret" not in str(settings)


def test_invalid_values_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-numeric or non-positive limits fail fast at startup."""
    monkeypatch.setenv("MAX_FILE_BYTES", "not-a-number")
    with pytest.raises(ValidationError):
        Settings()

    with pytest.raises(ValidationError):
        Settings(max_file_bytes=0)
