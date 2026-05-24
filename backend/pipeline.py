"""
Main pipeline orchestrator.
Runs: Ingest → Rule-filter → LLM classify → Rank → Persist to Supabase
"""

import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from db.database import get_supabase
from ingest.wwr import get_postings
from verify.rules import apply_filters
from verify.llm import classify
from rank.ranker import RankCandidate, rank
from models import RankedPosting


def _upsert_posting(sb, posting) -> int:
    """Upsert a posting and return its DB id."""
    fetched_at = posting.fetched_at.isoformat() if posting.fetched_at else datetime.now(timezone.utc).isoformat()
    posted_at  = posting.posted_at.isoformat()  if posting.posted_at  else None

    data = {
        "source":         posting.source,
        "source_url":     posting.source_url,
        "external_id":    posting.external_id,
        "company":        posting.company,
        "company_domain": posting.company_domain,
        "title":          posting.title,
        "description":    posting.description,
        "location_raw":   posting.location_raw,
        "remote_type":    posting.remote_type,
        "role_family":    posting.role_family,
        "posted_at":      posted_at,
        "fetched_at":     fetched_at,
    }

    result = (
        sb.table("postings")
        .upsert(data, on_conflict="source,external_id")
        .execute()
    )
    return result.data[0]["id"]


def _upsert_verification(sb, posting_id: int, verification) -> None:
    """Upsert a verification row."""
    data = {
        "posting_id":                  posting_id,
        "trust_score":                 verification.trust_score,
        "genuinely_remote":            verification.genuinely_remote,
        "remote_confidence":           verification.remote_confidence,
        "scam_likelihood":             verification.scam_likelihood,
        "scam_reasons":                verification.scam_reasons,                   # list → jsonb
        "role_clarity":                verification.role_clarity,
        "employer_legitimacy_signals": verification.employer_legitimacy_signals,    # list → jsonb
        "newcomer_friendly_signals":   verification.newcomer_friendly_signals,      # list → jsonb
        "rationale":                   verification.rationale,
        "classifier_version":          verification.classifier_version,
        "verified_at":                 datetime.now(timezone.utc).isoformat(),
    }

    sb.table("verifications").upsert(data, on_conflict="posting_id").execute()


def run_pipeline(
    ingest_mode: str = None,
    classifier_mode: str = None,
) -> list[RankedPosting]:
    ingest_mode     = ingest_mode     or settings.ingest_mode
    classifier_mode = classifier_mode or settings.classifier_mode

    print(f"\n{'='*50}")
    print(f"[pipeline] Starting | ingest={ingest_mode} | classifier={classifier_mode}")
    print(f"{'='*50}")

    sb = get_supabase()

    # --- Layer 1: Ingest ---
    raw_postings = get_postings(mode=ingest_mode)
    print(f"[pipeline] Layer 1 done: {len(raw_postings)} raw postings")

    # --- Layer 2a: Rule filters ---
    filter_results  = apply_filters(raw_postings, max_age_days=settings.max_posting_age_days)
    passed_filter   = [fr for fr in filter_results if fr.passed]
    passed_postings = [fr.posting for fr in passed_filter]
    print(f"[pipeline] Layer 2a done: {len(passed_postings)} passed rules")

    if not passed_postings:
        print("[pipeline] No postings survived rule filters. Done.")
        return []

    # --- Layer 2b: LLM classifier ---
    verifications = classify(
        passed_postings,
        passed_filter,
        mode=classifier_mode,
        api_key=settings.anthropic_api_key,
    )
    print(f"[pipeline] Layer 2b done: {len(verifications)} verified")

    # --- Persist to Supabase + build rank candidates ---
    candidates: list[RankCandidate] = []

    for posting, verification in zip(passed_postings, verifications):
        try:
            posting_id = _upsert_posting(sb, posting)
            _upsert_verification(sb, posting_id, verification)
            verification.posting_id = posting_id
            candidates.append(RankCandidate(
                posting=posting,
                verification=verification,
                posting_id=posting_id,
            ))
        except Exception as e:
            print(f"[pipeline] DB error for {posting.company}/{posting.title}: {e}")
            continue

    print(f"[pipeline] Persisted {len(candidates)} postings to Supabase")

    # --- Layer 3: Rank ---
    ranked = rank(candidates, min_trust_score=settings.min_trust_score)
    print(f"[pipeline] Layer 3 done: {len(ranked)} postings in final feed")
    print(f"{'='*50}\n")

    return ranked


if __name__ == "__main__":
    results = run_pipeline()
    print(f"\nTop {min(5, len(results))} postings:")
    for rp in results[:5]:
        print(f"  [{rp.trust_score}] {rp.title} @ {rp.company} — {rp.rationale}")
