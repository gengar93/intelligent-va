import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from order_support.config import OpenRouterSettings, load_model_catalog


class ConfigTests(unittest.TestCase):
    def test_loads_openrouter_secrets_from_environment(self):
        environment = {
            "OPENROUTER_API_KEY": "test-key",
            "OPENROUTER_BASE_URL": "https://example.test/v1",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = OpenRouterSettings.from_env()

        self.assertEqual(settings.api_key, "test-key")
        self.assertEqual(settings.base_url, "https://example.test/v1")

    def test_rejects_missing_required_secrets(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("order_support.config.load_dotenv"):
                with self.assertRaisesRegex(ValueError, "OPENROUTER_API_KEY"):
                    OpenRouterSettings.from_env()

    def test_checked_in_catalog_contains_requested_nitro_models(self):
        catalog = load_model_catalog()

        self.assertEqual(catalog.default_model, "gpt-5-6-luna")
        self.assertEqual(
            {model.id: model.slug for model in catalog.models},
            {
                "gemini-3-7-flash": "google/gemini-3.7-flash:nitro",
                "glm-5-2": "z-ai/glm-5.2:nitro",
                "qwen-3-7-flash": "qwen/qwen3.7-flash:nitro",
                "gpt-5-6-luna": "openai/gpt-5.6-luna:nitro",
                "gpt-oss-120b": "openai/gpt-oss-120b:nitro",
            },
        )
        for model in catalog.models:
            self.assertEqual(model.resolve_route().id, "nitro")

    def test_loads_optional_provider_route_and_resolves_selection(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "models.toml"
            config_path.write_text(
                """
default_model = "demo"

[[models]]
id = "demo"
label = "Demo Model"
slug = "author/demo:nitro"
default_route = "auto"

[[models.routes]]
id = "auto"
label = "Nitro · Automatic"

[[models.routes]]
id = "fast-host"
label = "Fast Host"

[models.routes.provider]
only = ["fast-host"]
allow_fallbacks = false
""".strip(),
                encoding="utf-8",
            )

            catalog = load_model_catalog(config_path)
            model, route = catalog.resolve("demo", "fast-host")

        self.assertEqual(model.slug, "author/demo:nitro")
        self.assertEqual(
            route.provider,
            {"only": ["fast-host"], "allow_fallbacks": False},
        )

    def test_rejects_unknown_defaults_and_provider_fields(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "models.toml"
            config_path.write_text(
                """
default_model = "missing"

[[models]]
id = "demo"
label = "Demo Model"
slug = "author/demo:nitro"
default_route = "auto"

[[models.routes]]
id = "auto"
label = "Automatic"
""".strip(),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Default model"):
                load_model_catalog(config_path)

            config_path.write_text(
                config_path.read_text(encoding="utf-8")
                .replace('default_model = "missing"', 'default_model = "demo"')
                .replace('label = "Automatic"', 'label = "Automatic"\n\n[models.routes.provider]\nunknown = true'),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unsupported fields"):
                load_model_catalog(config_path)


if __name__ == "__main__":
    unittest.main()
