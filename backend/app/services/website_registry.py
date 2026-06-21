from datetime import datetime, timezone

from backend.app.services.database import get_connection


def create_website(
    name: str,
    url: str,
    location: str | None = None,
    real_world_usecase: str | None = None,
    payment_status: str = "trial",
) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO websites (
                name, url, location, real_world_usecase,
                payment_status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                url,
                location,
                real_world_usecase,
                payment_status,
                created_at,
            ),
        )

        website_id = cursor.lastrowid

    return {
        "id": website_id,
        "name": name,
        "url": url,
        "location": location,
        "real_world_usecase": real_world_usecase,
        "payment_status": payment_status,
        "is_active": True,
        "created_at": created_at,
        "last_checked_at": None,
        "last_status_code": None,
        "last_status": None,
    }


def list_websites() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id, name, url, location, real_world_usecase,
                payment_status, is_active, created_at,
                last_checked_at, last_status_code, last_status
            FROM websites
            ORDER BY id DESC
            """
        ).fetchall()

    websites = []
    for row in rows:
        website = dict(row)
        website["is_active"] = bool(website["is_active"])
        websites.append(website)

    return websites
