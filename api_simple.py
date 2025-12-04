from fastapi import FastAPI, Header, HTTPException, Depends, Response
from datetime import datetime
import os

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

API_KEY = os.getenv("API_KEY", "super-secret-key-change-me")

app = FastAPI(title="Digital Twin API", version="2.0.1")


async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


@app.get("/")
async def root():
    return {
        "name": "Digital Twin API",
        "version": "2.0.0",
        "status": "running",
        "auth": "X-API-Key required for /api/v1/*",
        "metrics": "/metrics (Prometheus)"
    }


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/twins", dependencies=[Depends(verify_api_key)])
async def list_twins():
    return {
        "twins": [
            {"id": "twin-001", "name": "Factory A", "status": "active"},
            {"id": "twin-002", "name": "Factory B", "status": "idle"}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_simple:app", host="0.0.0.0", port=8000, reload=False)
