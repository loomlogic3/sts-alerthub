import sqlite3
from pathlib import Path

DB_PATH = Path("data/alerthub.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row["name"] == column_name for row in rows)


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS websites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                location TEXT,
                real_world_usecase TEXT,
                payment_status TEXT DEFAULT 'trial',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_checked_at TEXT,
                last_status_code INTEGER,
                last_status TEXT
            )
            """
        )

        if not _column_exists(connection, "websites", "last_alert_type"):
            connection.execute(
                "ALTER TABLE websites ADD COLUMN last_alert_type TEXT"
            )

        if not _column_exists(connection, "websites", "last_alert_at"):
            connection.execute(
                "ALTER TABLE websites ADD COLUMN last_alert_at TEXT"
            )
