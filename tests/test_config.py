import pytest

from order_support.config import Settings


def test_reads_openrouter_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemini-3-flash-preview")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.example/api/v1")

    settings = Settings.from_env()

    assert settings.openrouter_api_key == "test-key"
    assert settings.openrouter_model == "google/gemini-3-flash-preview"
    assert settings.openrouter_base_url == "https://openrouter.example/api/v1"


def test_requires_openrouter_api_key() -> None:
    settings = Settings(
        openrouter_api_key="",
        openrouter_model="openai/gpt-5.4-mini",
        openrouter_base_url="https://openrouter.ai/api/v1",
    )

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        settings.require_api_key()
