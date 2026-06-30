import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

from backend.app.services.database import initialize_database
from backend.app.services.history_service import list_alerts, record_alert
from backend.app.services.password_service import hash_password, verify_password
from backend.app.services.rbac_service import get_role_permissions
from backend.app.services.user_service import create_user, get_user_by_email, list_users, update_user_password
from backend.app.services.incident_service import (
    get_incident_summary,
    list_incidents,
    open_incident,
    resolve_open_incident,
)
from backend.app.services.scheduler_service import start_scheduler
from backend.app.services.telegram_service import send_notification
from backend.app.services.uptime_service import (
    get_uptime_summary,
    list_uptime_checks,
    record_uptime_check,
)
from backend.app.services.website_monitor import check_website
from backend.app.services.website_registry import (
    create_website,
    delete_website,
    list_active_websites,
    list_websites,
    record_website_alert,
    update_website,
    update_website_status,
)

load_dotenv()
initialize_database()

VALID_PAYMENT_STATUSES = {"trial", "paid", "overdue", "cancelled"}


class AlertRequest(BaseModel):
    title: str
    message: str
    severity: str = "info"


class WebsiteCheckRequest(BaseModel):
    url: str
    alert_on_success: bool = False


class AdminCreateRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class PasswordChangeRequest(BaseModel):
    email: str
    current_password: str
    new_password: str


class WebsiteCreateRequest(BaseModel):
    name: str
    url: str
    location: str | None = None
    real_world_usecase: str | None = None
    payment_status: str = "trial"

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, value: str) -> str:
        if value not in VALID_PAYMENT_STATUSES:
            raise ValueError(
                "payment_status must be one of: trial, paid, overdue, cancelled"
            )
        return value


class WebsiteUpdateRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    location: str | None = None
    real_world_usecase: str | None = None
    payment_status: str | None = None
    is_active: bool | None = None

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_PAYMENT_STATUSES:
            raise ValueError(
                "payment_status must be one of: trial, paid, overdue, cancelled"
            )
        return value


app = FastAPI(
    title="STS AlertHub",
    version="0.4.0",
)


def _can_send_alert(website: dict, alert_type: str) -> bool:
    cooldown_seconds = int(os.getenv("ALERT_COOLDOWN_SECONDS", "900"))

    last_alert_type = website.get("last_alert_type")
    last_alert_at = website.get("last_alert_at")

    if last_alert_type != alert_type:
        return True

    if not last_alert_at:
        return True

    try:
        last_alert_time = datetime.fromisoformat(last_alert_at)
    except ValueError:
        return True

    age_seconds = (
        datetime.now(timezone.utc) - last_alert_time
    ).total_seconds()

    return age_seconds >= cooldown_seconds


def _summarize_failure_reason(result: dict) -> str:
    status_code = result.get("status_code")
    error = str(result.get("error", "")).lower()

    if status_code:
        return f"HTTP {status_code}"

    if "name or service not known" in error or "failed to resolve" in error:
        return "DNS resolution failed"

    if "timed out" in error or "timeout" in error:
        return "Connection timeout"

    if "connection refused" in error:
        return "Connection refused"

    if "ssl" in error or "certificate" in error:
        return "SSL/certificate error"

    return "Website unreachable"


def _send_state_change_alert(
    website: dict,
    alert_type: str,
) -> bool:
    if not _can_send_alert(website, alert_type):
        print(
            f"Alert suppressed by cooldown: "
            f"website_id={website['id']} alert_type={alert_type}",
            flush=True,
        )
        return False

    if alert_type == "down":
        send_notification(
            f"🚨 WEBSITE DOWN\n\n"
            f"Name: {website['name']}\n"
            f"URL: {website['url']}"
        )
    elif alert_type == "recovered":
        send_notification(
            f"✅ WEBSITE RECOVERED\n\n"
            f"Name: {website['name']}\n"
            f"URL: {website['url']}"
        )
    else:
        return False

    record_website_alert(
        website_id=website["id"],
        alert_type=alert_type,
    )

    return True


def run_monitor_job() -> dict:
    websites = list_active_websites()

    checked = 0
    healthy = 0
    unhealthy = 0
    alerts_sent = 0

    for website in websites:
        checked += 1
        result = check_website(website["url"])

        current_status = "healthy" if result.get("ok") else "unhealthy"
        previous_status = website.get("last_status")

        record_uptime_check(
            website_id=website["id"],
            status=current_status,
            status_code=result.get("status_code"),
            response_time_ms=result.get("response_time_ms"),
        )

        if current_status == "healthy":
            healthy += 1
        else:
            unhealthy += 1

        update_website_status(
            website_id=website["id"],
            last_status=current_status,
            last_status_code=result.get("status_code"),
        )

        if previous_status == "healthy" and current_status == "unhealthy":
            open_incident(
                website_id=website["id"],
                reason=_summarize_failure_reason(result),
            )

            if _send_state_change_alert(website, "down"):
                alerts_sent += 1

        elif previous_status == "unhealthy" and current_status == "healthy":
            resolve_open_incident(
                website_id=website["id"],
            )

            if _send_state_change_alert(website, "recovered"):
                alerts_sent += 1

    result = {
        "checked": checked,
        "healthy": healthy,
        "unhealthy": unhealthy,
        "alerts_sent": alerts_sent,
    }

    print(f"Monitor job completed: {result}", flush=True)
    return result


@app.on_event("startup")
def startup_event():
    start_scheduler(run_monitor_job)


@app.get("/")
def root():
    return {"service": "STS AlertHub", "status": "running"}


@app.get("/health")
def health():
    return {"healthy": True}


@app.get("/login")
def login_page():
    return FileResponse("backend/app/templates/login.html")


@app.get("/change-password")
def change_password_page():
    return FileResponse("backend/app/templates/change_password.html")


@app.post("/auth/create-admin")
def create_admin_user(request: AdminCreateRequest):
    existing_user = get_user_by_email(request.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists",
        )

    password_hash = hash_password(request.password)

    user = create_user(
        email=request.email,
        password_hash=password_hash,
        role="admin",
    )

    return {
        "user_created": True,
        "user": user,
    }


@app.get("/auth/users")
def get_auth_users():
    return {"users": list_users()}


@app.post("/auth/login")
def login(request: LoginRequest):
    user = get_user_by_email(request.email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        )

    password_matches = verify_password(
        password=request.password,
        stored_password_hash=user["password_hash"],
    )

    if not password_matches:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return {
        "login_success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "permissions": get_role_permissions(user["role"]),
            "is_active": user["is_active"],
        },
    }


@app.post("/auth/change-password")
def change_password(request: PasswordChangeRequest):
    user = get_user_by_email(request.email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    password_matches = verify_password(
        password=request.current_password,
        stored_password_hash=user["password_hash"],
    )

    if not password_matches:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    new_password_hash = hash_password(request.new_password)
    updated = update_user_password(
        email=request.email,
        password_hash=new_password_hash,
    )

    return {
        "password_changed": updated,
        "email": request.email,
    }


@app.get("/dashboard")
def dashboard_page():
    return FileResponse("backend/app/templates/dashboard.html")


@app.get("/websites/{website_id}/detail")
def website_detail_page(website_id: int):
    return FileResponse("backend/app/templates/website_detail.html")


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


@app.post("/monitors/run-all")
def run_all_monitors():
    return run_monitor_job()


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


@app.get("/dashboard/summary")
def get_dashboard_summary():
    websites = list_websites()
    incident_summary = get_incident_summary()
    latest_incidents = list_incidents(limit=5)

    total_websites = len(websites)
    active_websites = 0
    inactive_websites = 0
    healthy_websites = 0
    unhealthy_websites = 0
    unknown_websites = 0

    for website in websites:
        if website.get("is_active"):
            active_websites += 1
        else:
            inactive_websites += 1

        if website.get("last_status") == "healthy":
            healthy_websites += 1
        elif website.get("last_status") == "unhealthy":
            unhealthy_websites += 1
        else:
            unknown_websites += 1

    return {
        "service": "STS AlertHub",
        "total_websites": total_websites,
        "active_websites": active_websites,
        "inactive_websites": inactive_websites,
        "healthy_websites": healthy_websites,
        "unhealthy_websites": unhealthy_websites,
        "unknown_websites": unknown_websites,
        "incident_summary": incident_summary,
        "latest_incidents": latest_incidents,
    }


@app.get("/websites/{website_id}/uptime")
def get_website_uptime(website_id: int):
    return {
        "website_id": website_id,
        "uptime": list_uptime_checks(website_id),
    }


@app.get("/websites/{website_id}/uptime-summary")
def get_website_uptime_summary(website_id: int):
    return get_uptime_summary(website_id)


@app.get("/incidents")
def get_incidents():
    return {"incidents": list_incidents()}


@app.get("/incidents/summary")
def get_all_incidents_summary():
    return get_incident_summary()


@app.get("/websites/{website_id}/incidents")
def get_website_incidents(website_id: int):
    return {
        "website_id": website_id,
        "incidents": list_incidents(website_id=website_id),
    }


@app.get("/websites/{website_id}/incidents/summary")
def get_website_incidents_summary(website_id: int):
    return get_incident_summary(website_id=website_id)


@app.patch("/websites/{website_id}")
def patch_website(website_id: int, request: WebsiteUpdateRequest):
    updated = update_website(
        website_id,
        request.model_dump(exclude_none=True),
    )

    return {
        "website_updated": updated,
        "website_id": website_id,
    }


@app.delete("/websites/{website_id}")
def remove_website(website_id: int):
    deleted = delete_website(website_id)

    return {
        "website_deleted": deleted,
        "website_id": website_id,
    }
