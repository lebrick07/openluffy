from fastapi import FastAPI

app = FastAPI(title="lebrickbot")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/")
def root():
    return {"service": "lebrickbot", "status": "running", "version": "0.1.0"}

@app.get("/api/status")
def api_status():
    return {
        "service": "lebrickbot-backend",
        "status": "operational",
        "version": "0.1.0"
    }
