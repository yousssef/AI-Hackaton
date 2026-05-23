"""
FastAPI routes.

GET /api/postings        — ranked, verified feed (query: role_family, limit, days)
GET /api/postings/{id}   — single posting detail
POST /api/feedback       — submit thumbs up/down
POST /api/refresh        — trigger a fresh pipeline run
GET /api/export/csv      — CSV download of current feed
"""

from models import RankedPosting, FeedbackSignal
from db.schema import PostingORM, VerificationORM, FeedbackORM
from db.database import get_db_dependency
import json
import csv
import io
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


router = APIRouter()


def _build_ranked_posting(p: PostingORM) -> dict:
    v = p.verification
    from rank.ranker import detect_seniority
    return {
        "id": p.id,
        "source": p.source,
        "source_url": p.source_url,
        "company": p.company,
        "title": p.title,
        "description": p.description[:500] + "..." if p.description and len(p.description) > 500 else p.description,
        "location_raw": p.location_raw,
        "remote_type": p.remote_type,
        "role_family": p.role_family,
        "posted_at": p.posted_at.isoformat() if p.posted_at else None,
        "trust_score": v.trust_score if v else 0,
        "genuinely_remote": v.genuinely_remote if v else False,
        "scam_likelihood": v.scam_likelihood if v else 1.0,
        "newcomer_friendly_signals": json.loads(v.newcomer_friendly_signals or "[]") if v else [],
        "rationale": v.rationale if v else "",
        "seniority": detect_seniority(p.title, p.description or ""),
    }


@router.get("/postings")
def get_postings(
    role_family: Optional[str] = Query(
        None, description="Filter by role family (engineering, design, etc.)"),
    days: int = Query(14, description="Max posting age in days"),
    limit: int = Query(50, description="Max results to return"),
    db: Session = Depends(get_db_dependency),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_naive = cutoff.replace(tzinfo=None)

    query = (
        db.query(PostingORM)
        .join(VerificationORM)
        .filter(
            VerificationORM.trust_score >= 70,
            VerificationORM.genuinely_remote == True,
            PostingORM.posted_at >= cutoff_naive,
        )
        .order_by(VerificationORM.trust_score.desc(), PostingORM.posted_at.desc())
    )

    if role_family:
        query = query.filter(PostingORM.role_family == role_family.lower())

    postings = query.limit(limit).all()
    return [_build_ranked_posting(p) for p in postings]


@router.get("/postings/{posting_id}")
def get_posting(posting_id: int, db: Session = Depends(get_db_dependency)):
    p = db.query(PostingORM).filter(PostingORM.id == posting_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Posting not found")
    result = _build_ranked_posting(p)
    # Include full description for detail view
    result["description"] = p.description
    if p.verification:
        result["employer_legitimacy_signals"] = json.loads(
            p.verification.employer_legitimacy_signals or "[]")
        result["remote_confidence"] = p.verification.remote_confidence
        result["role_clarity"] = p.verification.role_clarity
    return result


@router.post("/feedback")
def submit_feedback(feedback: FeedbackSignal, db: Session = Depends(get_db_dependency)):
    posting = db.query(PostingORM).filter(
        PostingORM.id == feedback.posting_id).first()
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")

    if feedback.signal not in ("up", "down"):
        raise HTTPException(
            status_code=400, detail="signal must be 'up' or 'down'")

    fb = FeedbackORM(
        posting_id=feedback.posting_id,
        user_id=feedback.user_id or "anonymous",
        signal=feedback.signal,
        note=feedback.note,
    )
    db.add(fb)
    db.commit()
    return {"status": "ok", "posting_id": feedback.posting_id, "signal": feedback.signal}


@router.post("/refresh")
def refresh_pipeline():
    """Trigger a fresh pipeline run (async in production; sync here for simplicity)."""
    from pipeline import run_pipeline
    results = run_pipeline()
    return {"status": "ok", "postings_in_feed": len(results)}


@router.get("/export/csv")
def export_csv(
    days: int = Query(14),
    db: Session = Depends(get_db_dependency),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_naive = cutoff.replace(tzinfo=None)

    postings = (
        db.query(PostingORM)
        .join(VerificationORM)
        .filter(
            VerificationORM.trust_score >= 70,
            VerificationORM.genuinely_remote == True,
            PostingORM.posted_at >= cutoff_naive,
        )
        .order_by(VerificationORM.trust_score.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Company", "Title", "Role Family", "Location",
        "Trust Score", "Genuinely Remote", "Rationale",
        "Apply Link", "Posted At"
    ])
    for p in postings:
        v = p.verification
        writer.writerow([
            p.company, p.title, p.role_family, p.location_raw,
            v.trust_score if v else "", v.genuinely_remote if v else "",
            v.rationale if v else "",
            p.source_url,
            p.posted_at.strftime("%Y-%m-%d") if p.posted_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=verified_remote_jobs.csv"},
    )
