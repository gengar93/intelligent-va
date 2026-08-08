"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the chatbot."""

    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL", "openai/gpt-5.4-mini"
            ).strip(),
            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ).strip(),
        )

    def require_api_key(self) -> None:
        if not self.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is missing. Add it to the .env file and restart the app."
            )
