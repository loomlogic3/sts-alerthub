import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ALERT_HISTORY_FILE = Path("data/alerts.json")


def _load_alerts() -> list[dict]:
    if not ALERT_HISTORY_FILE.exists():
        return []

    with ALERT_HISTORY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_alerts(alerts: list[dict]) -> None:
    ALERT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with ALERT_HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(alerts, file, indent=2)


def record_alert(title: str, message: str, severity: str, delivery_status: str) -> dict:
    alerts = _load_alerts()

    alert_record = {
        "id": str(uuid4()),
        "title": title,
        "message": message,
        "severity": severity,
        "delivery_status": delivery_status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    alerts.append(alert_record)
    _save_alerts(alerts)

    return alert_record


def list_alerts() -> list[dict]:
    return _load_alerts()
