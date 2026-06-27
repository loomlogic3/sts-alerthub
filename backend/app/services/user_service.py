from datetime import datetime, timezone

from backend.app.services.database import get_connection


def create_user(
    email: str,
    password_hash: str,
    role: str = "admin",
) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (
                email,
                password_hash,
                role,
                is_active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                email,
                password_hash,
                role,
                1,
                created_at,
            ),
        )

        user_id = cursor.lastrowid

    return {
        "id": user_id,
        "email": email,
        "role": role,
        "is_active": True,
        "created_at": created_at,
    }


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                email,
                password_hash,
                role,
                is_active,
                created_at
            FROM users
            WHERE email = ?
            LIMIT 1
            """,
            (email,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def list_users() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                email,
                role,
                is_active,
                created_at
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]
