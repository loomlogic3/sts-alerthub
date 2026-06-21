# STS AlertHub

Telegram monitoring and alert platform for websites, dashboards, inventory systems, and business operations.

## MVP Features

- FastAPI backend
- Health check endpoint
- Telegram notification engine
- Alert history
- Business monitoring use cases

## Local Development

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8002

## Endpoints

GET /
GET /health
