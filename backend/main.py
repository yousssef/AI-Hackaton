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
    allow_origins=["*"],  # open for hackathon demo — tighten post-event
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

_scheduler = BackgroundScheduler(daemon=True)


def _safe_pipeline():
    """Run pipeline, catching all exceptions so a failure never kills the server."""
    try:
        run_pipeline()
    except Exception as e:
        print(f"[pipeline] ERROR during run: {e}")


@app.on_event("startup")
async def startup():
    """Create DB tables, kick off pipeline in background, schedule refresh every 6h."""
    create_tables(engine)
    print("[startup] DB tables ready")

    # Schedule the recurring refresh
    _scheduler.add_job(_safe_pipeline, "interval", hours=6, id="pipeline_refresh")
    _scheduler.start()
    print("[startup] Scheduler started — pipeline refreshes every 6 hours")

    # Fire an immediate first run in a background thread so the server
    # becomes available right away (Render health checks won't time out)
    import threading
    t = threading.Thread(target=_safe_pipeline, daemon=True)
    t.start()
    print("[startup] Initial pipeline run started in background thread")


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


@app.get("/api/status")
def status():
    """Quick liveness + posting count check — useful for Render health monitoring."""
    from db.database import SessionLocal
    from db.schema import PostingORM, VerificationORM
    db = SessionLocal()
    try:
        total = db.query(PostingORM).count()
        verified = db.query(VerificationORM).filter(
            VerificationORM.trust_score >= 70,
            VerificationORM.genuinely_remote == True
        ).count()
        return {"status": "ok", "total_postings": total, "verified_in_feed": verified}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()
