"""Environment configuration for the OpenRouter model client."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class OpenRouterSettings:
    api_key: str
    model: str
    base_url: str

    @classmethod
    def from_env(cls):
        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        model = os.getenv("OPENROUTER_MODEL", "").strip()
        base_url = os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ).strip()

        missing = [
            name
            for name, value in (
                ("OPENROUTER_API_KEY", api_key),
                ("OPENROUTER_MODEL", model),
                ("OPENROUTER_BASE_URL", base_url),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "Missing required OpenRouter configuration: " + ", ".join(missing)
            )

        return cls(api_key=api_key, model=model, base_url=base_url)
