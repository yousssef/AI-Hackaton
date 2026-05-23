"""
FastAPI app entry point.
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import engine
from db.schema import create_tables
from api.routes import router
from pipeline import run_pipeline
from config import settings

app = FastAPI(
    title="Scale Without Borders — Verified Remote Jobs API",
    description="AI-powered remote job verification tool",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup():
    """Create DB tables and run an initial pipeline pass on startup."""
    create_tables(engine)
    print("[startup] DB tables ready")
    print("[startup] Running initial pipeline...")
    run_pipeline()


@app.get("/health")
def health():
    return {"status": "ok", "ingest_mode": settings.ingest_mode, "classifier_mode": settings.classifier_mode}
