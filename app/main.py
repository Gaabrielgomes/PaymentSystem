from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.routers import payments
from app.core.log_config import setup_logging

logger = setup_logging("api")

app = FastAPI(title="Payment System")
app.include_router(payments.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)