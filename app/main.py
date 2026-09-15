from fastapi import FastAPI

app = FastAPI(title="Payment System")

@app.get("/health")
def health():
    return {"status": "ok"}