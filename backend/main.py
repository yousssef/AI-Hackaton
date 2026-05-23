"""
FastAPI app entry point.
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

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

_scheduler = BackgroundScheduler(daemon=True)


@app.on_event("startup")
async def startup():
    """Create DB tables, run initial pipeline, then schedule refresh every 6 hours."""
    create_tables(engine)
    print("[startup] DB tables ready")
    print("[startup] Running initial pipeline...")
    run_pipeline()

    _scheduler.add_job(run_pipeline, "interval",
                       hours=6, id="pipeline_refresh")
    _scheduler.start()
    print("[startup] Scheduler started — pipeline refreshes every 6 hours")


@app.on_event("shutdown")
async def shutdown():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


@app.get("/health")
def health():
    job = _scheduler.get_job("pipeline_refresh")
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    return {
        "status": "ok",
        "ingest_mode": settings.ingest_mode,
        "classifier_mode": settings.classifier_mode,
        "next_scheduled_refresh": next_run,
    }
