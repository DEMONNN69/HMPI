# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .routers import data_processing, calculations, reports
import uvicorn

app = FastAPI(
    title="AQUA-GUARD Data Processing Service",
    description="FastAPI service for heavy data processing tasks",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_processing.router, prefix="/api/v1/data", tags=["data"])
app.include_router(calculations.router, prefix="/api/v1/calculations", tags=["calculations"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/")
async def root():
    return {"message": "AQUA-GUARD Data Processing Service"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fastapi-data-processing"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
