from datetime import datetime, timezone

from backend.app.services.database import get_connection


def record_uptime_check(
    website_id: int,
    status: str,
    status_code: int | None,
    response_time_ms: int | None = None,
) -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO uptime_checks (
                website_id,
                checked_at,
                status,
                status_code,
                response_time_ms
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                website_id,
                checked_at,
                status,
                status_code,
                response_time_ms,
            ),
        )

        check_id = cursor.lastrowid

    return {
        "id": check_id,
        "website_id": website_id,
        "checked_at": checked_at,
        "status": status,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
    }


def list_uptime_checks(
    website_id: int,
    limit: int = 100,
) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                website_id,
                checked_at,
                status,
                status_code,
                response_time_ms
            FROM uptime_checks
            WHERE website_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (website_id, limit),
        ).fetchall()

    return [dict(row) for row in rows]


def get_uptime_summary(website_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) as total_checks,
                SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_checks,
                SUM(CASE WHEN status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy_checks,
                AVG(response_time_ms) as average_response_time_ms,
                MIN(response_time_ms) as fastest_response_time_ms,
                MAX(response_time_ms) as slowest_response_time_ms
            FROM uptime_checks
            WHERE website_id = ?
            """,
            (website_id,),
        ).fetchone()

    total_checks = row["total_checks"] or 0
    healthy_checks = row["healthy_checks"] or 0
    unhealthy_checks = row["unhealthy_checks"] or 0

    average_response_time_ms = row["average_response_time_ms"]
    fastest_response_time_ms = row["fastest_response_time_ms"]
    slowest_response_time_ms = row["slowest_response_time_ms"]

    uptime_percentage = 0.0
    if total_checks > 0:
        uptime_percentage = round((healthy_checks / total_checks) * 100, 2)

    return {
        "website_id": website_id,
        "total_checks": total_checks,
        "healthy_checks": healthy_checks,
        "unhealthy_checks": unhealthy_checks,
        "uptime_percentage": uptime_percentage,
        "average_response_time_ms": round(average_response_time_ms, 2)
        if average_response_time_ms is not None
        else None,
        "fastest_response_time_ms": fastest_response_time_ms,
        "slowest_response_time_ms": slowest_response_time_ms,
    }
