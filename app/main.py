from fastapi import FastAPI
from app.api.v1.api import api_router

app = FastAPI(title="Horizon API - Skeleton", version="0.1.0")

# Include the main API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Horizon API Template is Running"}
