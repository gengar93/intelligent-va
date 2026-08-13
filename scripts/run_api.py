"""Reset the demo database once, then start the local API development server."""

from pathlib import Path

import uvicorn

from scripts.reset_database import DEFAULT_DATABASE_PATH, build_database


def run_api(
    database_path: Path = DEFAULT_DATABASE_PATH,
    *,
    server_runner=uvicorn.run,
):
    """Start the API only after rebuilding its local demo database."""
    database_path = Path(database_path).resolve()
    build_database(database_path)
    print(f"Reset database: {database_path}")
    server_runner(
        "order_support.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


def main():
    run_api()


if __name__ == "__main__":
    main()
