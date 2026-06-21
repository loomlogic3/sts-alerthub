from fastapi import FastAPI

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