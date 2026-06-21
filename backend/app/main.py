from dotenv import load_dotenv
from fastapi import FastAPI

from backend.app.services.telegram_service import send_notification

load_dotenv()

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
