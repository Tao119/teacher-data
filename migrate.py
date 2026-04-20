"""Safe column migrations for SQLite — adds columns if they don't already exist."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "storage" / "db.sqlite"

MIGRATIONS = [
    ("records", "cost_usd", "REAL NOT NULL DEFAULT 0.0"),
    ("records", "cer", "REAL NOT NULL DEFAULT 0.0"),
    ("records", "confidence", "REAL NOT NULL DEFAULT 0.0"),
]


def run():
    if not DB_PATH.exists():
        print("No DB found, skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for table, column, definition in MIGRATIONS:
        existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"  + {table}.{column}")
        else:
            print(f"  . {table}.{column} (already exists)")

    conn.commit()
    conn.close()
    print("Migration done.")


if __name__ == "__main__":
    run()
