"""Wait for PostgreSQL before starting a container process."""

from __future__ import annotations

import os
import sys
import time

import psycopg


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 1

    attempts = int(os.environ.get("DATABASE_WAIT_ATTEMPTS", "60"))
    for attempt in range(1, attempts + 1):
        try:
            with psycopg.connect(database_url, connect_timeout=3):
                print("PostgreSQL is reachable.")
                return 0
        except psycopg.OperationalError as exc:
            if attempt == attempts:
                print(
                    f"PostgreSQL was not reachable after {attempts} attempts: {exc}",
                    file=sys.stderr,
                )
                return 1
            print(f"Waiting for PostgreSQL ({attempt}/{attempts})…")
            time.sleep(1)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
