import sqlite3
from pathlib import Path

DB_PATH = Path("data/alerthub.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


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
