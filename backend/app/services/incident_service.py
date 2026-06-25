from datetime import datetime, timezone

from backend.app.services.database import get_connection


def open_incident(
    website_id: int,
    reason: str | None = None,
) -> dict:
    existing = get_open_incident(website_id)
    if existing:
        return existing

    started_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO incidents (
                website_id,
                started_at,
                status,
                reason
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                website_id,
                started_at,
                "open",
                reason,
            ),
        )

        incident_id = cursor.lastrowid

    return {
        "id": incident_id,
        "website_id": website_id,
        "started_at": started_at,
        "resolved_at": None,
        "status": "open",
        "reason": reason,
    }


def resolve_open_incident(
    website_id: int,
) -> dict | None:
    incident = get_open_incident(website_id)
    if not incident:
        return None

    resolved_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE incidents
            SET
                resolved_at = ?,
                status = ?
            WHERE id = ?
            """,
            (
                resolved_at,
                "resolved",
                incident["id"],
            ),
        )

    incident["resolved_at"] = resolved_at
    incident["status"] = "resolved"

    return incident


def get_open_incident(
    website_id: int,
) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                website_id,
                started_at,
                resolved_at,
                status,
                reason
            FROM incidents
            WHERE website_id = ?
              AND status = 'open'
            ORDER BY id DESC
            LIMIT 1
            """,
            (website_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def list_incidents(
    website_id: int | None = None,
    limit: int = 100,
) -> list[dict]:
    query = """
        SELECT
            id,
            website_id,
            started_at,
            resolved_at,
            status,
            reason
        FROM incidents
    """
    params: list = []

    if website_id is not None:
        query += " WHERE website_id = ?"
        params.append(website_id)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]
