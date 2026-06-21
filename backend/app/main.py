from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.services.telegram_service import send_notification

load_dotenv()


class AlertRequest(BaseModel):
    title: str
    message: str
    severity: str = "info"


app = FastAPI(
    title="STS AlertHub",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "service": "STS AlertHub",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "healthy": True,
    }


@app.post("/notify/test")
def notify_test():
    result = send_notification(
        "🚀 AlertHub test endpoint triggered successfully."
    )

    return result


@app.post("/alerts")
def create_alert(alert: AlertRequest):
    formatted_message = (
        f"🚨 STS AlertHub\n\n"
        f"Title: {alert.title}\n"
        f"Severity: {alert.severity}\n"
        f"Message: {alert.message}"
    )

    result = send_notification(formatted_message)

    return {
        "alert_sent": True,
        "title": alert.title,
        "severity": alert.severity,
        "telegram_result": result,
    }
