"""Create a fresh local SQLite database from the checked-in schema and seed data."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parents[1]
DEFAULT_DATABASE = ROOT / "data" / "order_support.db"


def reset_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_path.unlink(missing_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.executescript((ROOT / "database" / "schema.sql").read_text())
        connection.executescript((ROOT / "database" / "seed.sql").read_text())
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations found: {violations}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    reset_database(args.database.resolve())
    print(f"Reset database: {args.database.resolve()}")


if __name__ == "__main__":
    main()
