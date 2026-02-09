from fastapi import FastAPI

app = FastAPI(title="openbrick-playground")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/")
def root():
    return {"service": "openbrick-playground", "status": "running"}
