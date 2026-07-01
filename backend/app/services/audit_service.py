from datetime import datetime, timezone

from backend.app.services.database import get_connection


def initialize_audit_table() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_email TEXT,
                action TEXT NOT NULL,
                object_type TEXT,
                object_name TEXT,
                details TEXT,
                result TEXT NOT NULL DEFAULT 'success'
            )
            """
        )


def record_audit(
    user_email: str | None,
    action: str,
    object_type: str | None = None,
    object_name: str | None = None,
    details: str | None = None,
    result: str = "success",
) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO audit_logs (
                timestamp,
                user_email,
                action,
                object_type,
                object_name,
                details,
                result
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                user_email,
                action,
                object_type,
                object_name,
                details,
                result,
            ),
        )

        audit_id = cursor.lastrowid

    return {
        "id": audit_id,
        "timestamp": timestamp,
        "user_email": user_email,
        "action": action,
        "object_type": object_type,
        "object_name": object_name,
        "details": details,
        "result": result,
    }


def list_audit_logs(limit: int = 100) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                timestamp,
                user_email,
                action,
                object_type,
                object_name,
                details,
                result
            FROM audit_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]
