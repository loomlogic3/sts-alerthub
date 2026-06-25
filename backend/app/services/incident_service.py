from datetime import datetime, timezone

from backend.app.services.database import get_connection


def _calculate_duration(incident: dict) -> dict:
    started_at = incident.get("started_at")
    resolved_at = incident.get("resolved_at")

    incident["duration_seconds"] = None
    incident["duration_minutes"] = None

    if not started_at or not resolved_at:
        return incident

    try:
        started = datetime.fromisoformat(started_at)
        resolved = datetime.fromisoformat(resolved_at)
    except ValueError:
        return incident

    duration_seconds = int((resolved - started).total_seconds())

    incident["duration_seconds"] = duration_seconds
    incident["duration_minutes"] = round(duration_seconds / 60, 2)

    return incident


def open_incident(website_id: int, reason: str | None = None) -> dict:
    existing = get_open_incident(website_id)
    if existing:
        return existing

    started_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO incidents (website_id, started_at, status, reason)
            VALUES (?, ?, ?, ?)
            """,
            (website_id, started_at, "open", reason),
        )

        incident_id = cursor.lastrowid

    return {
        "id": incident_id,
        "website_id": website_id,
        "started_at": started_at,
        "resolved_at": None,
        "status": "open",
        "reason": reason,
        "duration_seconds": None,
        "duration_minutes": None,
    }


def resolve_open_incident(website_id: int) -> dict | None:
    incident = get_open_incident(website_id)
    if not incident:
        return None

    resolved_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE incidents
            SET resolved_at = ?, status = ?
            WHERE id = ?
            """,
            (resolved_at, "resolved", incident["id"]),
        )

    incident["resolved_at"] = resolved_at
    incident["status"] = "resolved"

    return _calculate_duration(incident)


def get_open_incident(website_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, website_id, started_at, resolved_at, status, reason
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

    return _calculate_duration(dict(row))


def list_incidents(
    website_id: int | None = None,
    limit: int = 100,
) -> list[dict]:
    query = """
        SELECT id, website_id, started_at, resolved_at, status, reason
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

    return [_calculate_duration(dict(row)) for row in rows]
