from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.services.database import initialize_database
from backend.app.services.history_service import list_alerts, record_alert
from backend.app.services.telegram_service import send_notification
from backend.app.services.website_monitor import check_website
from backend.app.services.website_registry import create_website, list_websites

load_dotenv()
initialize_database()


class AlertRequest(BaseModel):
    title: str
    message: str
    severity: str = "info"


class WebsiteCheckRequest(BaseModel):
    url: str
    alert_on_success: bool = False


class WebsiteCreateRequest(BaseModel):
    name: str
    url: str
    location: str | None = None
    real_world_usecase: str | None = None
    payment_status: str = "trial"


app = FastAPI(
    title="STS AlertHub",
    version="0.2.0",
)


@app.get("/")
def root():
    return {"service": "STS AlertHub", "status": "running"}


@app.get("/health")
def health():
    return {"healthy": True}


@app.post("/notify/test")
def notify_test():
    return send_notification("🚀 AlertHub test endpoint triggered successfully.")


@app.post("/alerts")
def create_alert(alert: AlertRequest):
    formatted_message = (
        f"🚨 STS AlertHub\n\n"
        f"Title: {alert.title}\n"
        f"Severity: {alert.severity}\n"
        f"Message: {alert.message}"
    )

    telegram_result = send_notification(formatted_message)
    delivery_status = "sent" if telegram_result.get("ok") else "failed"

    alert_record = record_alert(
        title=alert.title,
        message=alert.message,
        severity=alert.severity,
        delivery_status=delivery_status,
    )

    return {
        "alert_sent": delivery_status == "sent",
        "alert": alert_record,
        "telegram_result": telegram_result,
    }


@app.get("/alerts")
def get_alerts():
    return {"alerts": list_alerts()}


@app.post("/monitors/website/check")
def check_website_endpoint(request: WebsiteCheckRequest):
    result = check_website(request.url)

    if not result["ok"]:
        message = (
            f"🌐 Website Monitor Alert\n\n"
            f"URL: {request.url}\n"
            f"Status: DOWN or unhealthy\n"
            f"Details: {result}"
        )

        telegram_result = send_notification(message)

        record_alert(
            title="Website Monitor Alert",
            message=f"{request.url} is down or unhealthy.",
            severity="critical",
            delivery_status="sent" if telegram_result.get("ok") else "failed",
        )

        return {
            "website_check": result,
            "alert_sent": telegram_result.get("ok", False),
            "telegram_result": telegram_result,
        }

    if request.alert_on_success:
        telegram_result = send_notification(
            f"✅ Website Monitor Check\n\n"
            f"URL: {request.url}\n"
            f"Status: OK\n"
            f"Status Code: {result.get('status_code')}"
        )

        return {
            "website_check": result,
            "success_alert_sent": telegram_result.get("ok", False),
            "telegram_result": telegram_result,
        }

    return {"website_check": result, "alert_sent": False}


@app.post("/websites")
def add_website(request: WebsiteCreateRequest):
    website = create_website(
        name=request.name,
        url=request.url,
        location=request.location,
        real_world_usecase=request.real_world_usecase,
        payment_status=request.payment_status,
    )

    return {"website_created": True, "website": website}


@app.get("/websites")
def get_websites():
    return {"websites": list_websites()}


from backend.app.services.website_registry import (
    list_active_websites,
    update_website_status,
)


@app.post("/monitors/run-all")
def run_all_monitors():
    websites = list_active_websites()

    checked = 0
    healthy = 0
    unhealthy = 0
    alerts_sent = 0

    for website in websites:
        checked += 1

        result = check_website(website["url"])

        current_status = (
            "healthy"
            if result.get("ok")
            else "unhealthy"
        )

        previous_status = website.get("last_status")

        if current_status == "healthy":
            healthy += 1
        else:
            unhealthy += 1

        update_website_status(
            website_id=website["id"],
            last_status=current_status,
            last_status_code=result.get("status_code"),
        )

        if (
            previous_status == "healthy"
            and current_status == "unhealthy"
        ):
            send_notification(
                f"🚨 WEBSITE DOWN\n\n"
                f"Name: {website['name']}\n"
                f"URL: {website['url']}"
            )
            alerts_sent += 1

        elif (
            previous_status == "unhealthy"
            and current_status == "healthy"
        ):
            send_notification(
                f"✅ WEBSITE RECOVERED\n\n"
                f"Name: {website['name']}\n"
                f"URL: {website['url']}"
            )
            alerts_sent += 1

    return {
        "checked": checked,
        "healthy": healthy,
        "unhealthy": unhealthy,
        "alerts_sent": alerts_sent,
    }
