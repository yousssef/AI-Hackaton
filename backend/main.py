"""
FastAPI app entry point.
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from api.routes import router
from pipeline import run_pipeline
from config import settings

app = FastAPI(
    title="Scale Without Borders — Verified Remote Jobs API",
    description="AI-powered remote job verification tool",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

_scheduler = BackgroundScheduler(daemon=True)


def _safe_pipeline():
    try:
        run_pipeline()
    except Exception as e:
        print(f"[pipeline] ERROR during run: {e}")


@app.on_event("startup")
async def startup():
    print("[startup] Supabase backend ready")

    _scheduler.add_job(_safe_pipeline, "interval", hours=6, id="pipeline_refresh")
    _scheduler.start()
    print("[startup] Scheduler started — pipeline refreshes every 6 hours")

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
        "db": "supabase",
        "ingest_mode": settings.ingest_mode,
        "classifier_mode": settings.classifier_mode,
        "next_scheduled_refresh": next_run,
    }


@app.get("/api/status")
def status():
    from db.database import get_supabase
    sb = get_supabase()
    try:
        total    = sb.table("postings").select("id", count="exact").execute().count
        verified = (
            sb.table("verifications")
            .select("id", count="exact")
            .gte("trust_score", 70)
            .eq("genuinely_remote", True)
            .execute()
            .count
        )
        return {"status": "ok", "total_postings": total, "verified_in_feed": verified}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
