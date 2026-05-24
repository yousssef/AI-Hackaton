"""
FastAPI routes — Supabase backend.

GET  /api/postings        — ranked, verified feed (query: role_family, limit, days)
GET  /api/postings/{id}   — single posting detail
POST /api/feedback        — submit thumbs up/down
POST /api/refresh         — trigger a fresh pipeline run
GET  /api/export/csv      — CSV download of current feed
"""

import csv
import io
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import FeedbackSignal
from db.database import get_supabase
from rank.ranker import detect_seniority

router = APIRouter()


def _cutoff_str(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _get_verified_posting_ids(sb, days: int, min_trust: int = 70) -> list[int]:
    """Return posting IDs whose verifications pass the hard filter."""
    result = (
        sb.table("verifications")
        .select("posting_id")
        .gte("trust_score", min_trust)
        .eq("genuinely_remote", True)
        .execute()
    )
    return [row["posting_id"] for row in result.data]


def _build_row(p: dict) -> dict:
    """Flatten a postings row (with embedded verifications) into the API shape."""
    v = p.get("verifications") or {}
    desc = p.get("description") or ""
    return {
        "id":                        p["id"],
        "source":                    p.get("source"),
        "source_url":                p.get("source_url"),
        "company":                   p.get("company"),
        "title":                     p.get("title"),
        "description":               desc[:500] + "..." if len(desc) > 500 else desc,
        "location_raw":              p.get("location_raw"),
        "remote_type":               p.get("remote_type"),
        "role_family":               p.get("role_family"),
        "posted_at":                 p.get("posted_at"),
        "trust_score":               v.get("trust_score", 0),
        "genuinely_remote":          v.get("genuinely_remote", False),
        "scam_likelihood":           v.get("scam_likelihood", 1.0),
        "newcomer_friendly_signals": v.get("newcomer_friendly_signals") or [],
        "rationale":                 v.get("rationale", ""),
        "seniority":                 detect_seniority(p.get("title") or "", desc),
    }


@router.get("/postings")
def get_postings(
    role_family: Optional[str] = Query(None),
    days: int = Query(14),
    limit: int = Query(50),
):
    sb = get_supabase()
    cutoff = _cutoff_str(days)

    # Step 1: IDs that pass verification hard filter
    verified_ids = _get_verified_posting_ids(sb, days)
    if not verified_ids:
        return []

    # Step 2: Postings within date range + verified
    query = (
        sb.table("postings")
        .select("*, verifications(*)")
        .in_("id", verified_ids)
        .gte("posted_at", cutoff)
        .order("posted_at", desc=True)
        .limit(limit)
    )
    if role_family:
        query = query.eq("role_family", role_family.lower())

    result = query.execute()
    return [_build_row(p) for p in result.data]


@router.get("/postings/{posting_id}")
def get_posting(posting_id: int):
    sb = get_supabase()
    result = (
        sb.table("postings")
        .select("*, verifications(*)")
        .eq("id", posting_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Posting not found")

    p = result.data
    row = _build_row(p)
    row["description"] = p.get("description")  # full description for detail view
    v = p.get("verifications") or {}
    row["employer_legitimacy_signals"] = v.get("employer_legitimacy_signals") or []
    row["remote_confidence"]           = v.get("remote_confidence")
    row["role_clarity"]                = v.get("role_clarity")
    return row


@router.post("/feedback")
def submit_feedback(feedback: FeedbackSignal):
    sb = get_supabase()

    if feedback.signal not in ("up", "down"):
        raise HTTPException(status_code=400, detail="signal must be 'up' or 'down'")

    # Verify posting exists
    check = sb.table("postings").select("id").eq("id", feedback.posting_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Posting not found")

    sb.table("feedback").insert({
        "posting_id": feedback.posting_id,
        "user_id":    feedback.user_id or "anonymous",
        "signal":     feedback.signal,
        "note":       feedback.note,
    }).execute()

    return {"status": "ok", "posting_id": feedback.posting_id, "signal": feedback.signal}


@router.post("/refresh")
def refresh_pipeline():
    from pipeline import run_pipeline
    results = run_pipeline()
    return {"status": "ok", "postings_in_feed": len(results)}


@router.get("/export/csv")
def export_csv(days: int = Query(14)):
    sb = get_supabase()
    cutoff = _cutoff_str(days)

    verified_ids = _get_verified_posting_ids(sb, days)
    if not verified_ids:
        output = io.StringIO()
        csv.writer(output).writerow(["No verified postings found"])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv")

    result = (
        sb.table("postings")
        .select("*, verifications(*)")
        .in_("id", verified_ids)
        .gte("posted_at", cutoff)
        .order("posted_at", desc=True)
        .execute()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Company", "Title", "Role Family", "Location",
        "Trust Score", "Genuinely Remote", "Rationale",
        "Apply Link", "Posted At",
    ])
    for p in result.data:
        v = p.get("verifications") or {}
        writer.writerow([
            p.get("company"), p.get("title"), p.get("role_family"), p.get("location_raw"),
            v.get("trust_score", ""), v.get("genuinely_remote", ""),
            v.get("rationale", ""),
            p.get("source_url"),
            (p.get("posted_at") or "")[:10],
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=verified_remote_jobs.csv"},
    )
