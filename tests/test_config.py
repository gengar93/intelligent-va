import os
import unittest
from unittest.mock import patch

from order_support.config import OpenRouterSettings


class ConfigTests(unittest.TestCase):
    def test_loads_openrouter_settings_from_environment(self):
        environment = {
            "OPENROUTER_API_KEY": "test-key",
            "OPENROUTER_MODEL": "test/model",
            "OPENROUTER_BASE_URL": "https://example.test/v1",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = OpenRouterSettings.from_env()

        self.assertEqual(settings.api_key, "test-key")
        self.assertEqual(settings.model, "test/model")
        self.assertEqual(settings.base_url, "https://example.test/v1")

    def test_rejects_missing_required_settings(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("order_support.config.load_dotenv"):
                with self.assertRaisesRegex(ValueError, "OPENROUTER_API_KEY"):
                    OpenRouterSettings.from_env()


if __name__ == "__main__":
    unittest.main()
