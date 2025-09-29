# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .routers import  calculations, reports, ingestion
import uvicorn

app = FastAPI(
    title="AQUA-GUARD Data Processing Service",
    description="FastAPI service for heavy data processing tasks",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(calculations.router, prefix="/api/v1/calculations", tags=["calculations"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(ingestion.router, prefix="/api/v1/ingestion", tags=["ingestion"])

@app.get("/")
async def root():
    return {"message": "AQUA-GUARD Data Processing Service"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fastapi-data-processing"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
