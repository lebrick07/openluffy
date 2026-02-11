# Sample Python FastAPI Application
from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title=os.getenv("SERVICE_NAME", "API"))

class HealthResponse(BaseModel):
    status: str
    service: str

class MessageResponse(BaseModel):
    message: str

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {
        "status": "ok",
        "service": os.getenv("SERVICE_NAME", "api")
    }

@app.get("/api/hello", response_model=MessageResponse)
def hello():
    return {"message": "Hello from your OpenLuffy-powered application!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
