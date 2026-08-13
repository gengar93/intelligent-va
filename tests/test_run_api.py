import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.reset_database import build_database
from scripts.run_api import run_api


class RunApiTests(unittest.TestCase):
    def test_resets_database_before_starting_server(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "orders.db"
            build_database(database_path)
            with sqlite3.connect(database_path) as connection:
                connection.execute("DELETE FROM invoices")

            observed_invoice_counts = []

            def fake_server_runner(*args, **kwargs):
                with sqlite3.connect(database_path) as connection:
                    observed_invoice_counts.append(
                        connection.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
                    )

            run_api(database_path, server_runner=fake_server_runner)

        self.assertEqual(observed_invoice_counts, [1])

    def test_starts_expected_local_reload_server(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            calls = []
            run_api(
                Path(temporary_directory) / "orders.db",
                server_runner=lambda *args, **kwargs: calls.append((args, kwargs)),
            )

        self.assertEqual(
            calls,
            [
                (
                    ("order_support.api:app",),
                    {
                        "host": "127.0.0.1",
                        "port": 8000,
                        "reload": True,
                    },
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
