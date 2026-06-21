import os
import requests


def send_notification(message: str) -> dict:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN")

    if not chat_id:
        raise ValueError("Missing TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=30,
    )

    return response.json()
