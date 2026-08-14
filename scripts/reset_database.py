"""Create a fresh local SQLite database from the schema and seed files."""

import argparse
import os
import sqlite3
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "order_support.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
SEED_PATH = PROJECT_ROOT / "database" / "seed.sql"


def build_database(database_path):
    """Atomically replace database_path with a freshly created seeded database."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{database_path.name}.",
        suffix=".tmp",
        dir=database_path.parent,
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        with sqlite3.connect(temporary_path) as connection:
            connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            connection.executescript(SEED_PATH.read_text(encoding="utf-8"))

            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError(f"Foreign-key violations found: {violations}")

        os.replace(temporary_path, database_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE_PATH)
    arguments = parser.parse_args()

    database_path = arguments.database.resolve()
    build_database(database_path)
    print(f"Created database: {database_path}")


if __name__ == "__main__":
    main()
