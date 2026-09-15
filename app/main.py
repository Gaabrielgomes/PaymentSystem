from fastapi import FastAPI
from app.routers import payments

app = FastAPI(title="Payment System")

app.include_router(payments.router)

@app.get("/health")
def health():
    return {"status": "ok"}