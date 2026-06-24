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
            (name, url, location, real_world_usecase, payment_status, created_at),
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
        "last_alert_type": None,
        "last_alert_at": None,
    }


def _row_to_website(row) -> dict:
    website = dict(row)
    website["is_active"] = bool(website["is_active"])
    return website


def list_websites() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id, name, url, location, real_world_usecase,
                payment_status, is_active, created_at,
                last_checked_at, last_status_code, last_status,
                last_alert_type, last_alert_at
            FROM websites
            ORDER BY id DESC
            """
        ).fetchall()

    return [_row_to_website(row) for row in rows]


def list_active_websites() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id, name, url, location, real_world_usecase,
                payment_status, is_active, created_at,
                last_checked_at, last_status_code, last_status,
                last_alert_type, last_alert_at
            FROM websites
            WHERE is_active = 1
            ORDER BY id ASC
            """
        ).fetchall()

    return [_row_to_website(row) for row in rows]


def update_website_status(
    website_id: int,
    last_status: str,
    last_status_code: int | None,
) -> None:
    checked_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE websites
            SET
                last_checked_at = ?,
                last_status_code = ?,
                last_status = ?
            WHERE id = ?
            """,
            (checked_at, last_status_code, last_status, website_id),
        )


def record_website_alert(
    website_id: int,
    alert_type: str,
) -> None:
    alerted_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE websites
            SET
                last_alert_type = ?,
                last_alert_at = ?
            WHERE id = ?
            """,
            (alert_type, alerted_at, website_id),
        )


def update_website(website_id: int, updates: dict) -> bool:
    allowed_fields = {
        "name",
        "url",
        "location",
        "real_world_usecase",
        "payment_status",
        "is_active",
    }

    cleaned_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields and value is not None
    }

    if not cleaned_updates:
        return False

    if "is_active" in cleaned_updates:
        cleaned_updates["is_active"] = 1 if cleaned_updates["is_active"] else 0

    set_clause = ", ".join(f"{field} = ?" for field in cleaned_updates.keys())
    values = list(cleaned_updates.values())
    values.append(website_id)

    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            UPDATE websites
            SET {set_clause}
            WHERE id = ?
            """,
            values,
        )

        return cursor.rowcount > 0


def delete_website(website_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM websites
            WHERE id = ?
            """,
            (website_id,),
        )

        return cursor.rowcount > 0
