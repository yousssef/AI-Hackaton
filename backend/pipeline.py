"""
Main pipeline orchestrator.
Runs: Ingest → Rule-filter → LLM classify → Rank → Persist
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from db.database import get_db
from db.schema import create_tables, PostingORM, VerificationORM
from ingest.wwr import get_postings
from verify.rules import apply_filters
from verify.llm import classify
from rank.ranker import RankCandidate, rank
from models import RankedPosting
from db.database import engine


def run_pipeline(
    ingest_mode: str = None,
    classifier_mode: str = None,
) -> list[RankedPosting]:
    ingest_mode = ingest_mode or settings.ingest_mode
    classifier_mode = classifier_mode or settings.classifier_mode

    print(f"\n{'='*50}")
    print(f"[pipeline] Starting | ingest={ingest_mode} | classifier={classifier_mode}")
    print(f"{'='*50}")

    # Ensure tables exist
    create_tables(engine)

    # --- Layer 1: Ingest ---
    raw_postings = get_postings(mode=ingest_mode)
    print(f"[pipeline] Layer 1 done: {len(raw_postings)} raw postings")

    # --- Layer 2a: Rule filters ---
    filter_results = apply_filters(raw_postings, max_age_days=settings.max_posting_age_days)
    passed_filter = [fr for fr in filter_results if fr.passed]
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

    # --- Persist to DB + build rank candidates ---
    candidates: list[RankCandidate] = []

    with get_db() as db:
        for posting, verification in zip(passed_postings, verifications):
            # Upsert posting
            existing = (
                db.query(PostingORM)
                .filter_by(source=posting.source, external_id=posting.external_id)
                .first()
            )
            if existing:
                posting_orm = existing
            else:
                posting_orm = PostingORM(
                    source=posting.source,
                    source_url=posting.source_url,
                    external_id=posting.external_id,
                    company=posting.company,
                    company_domain=posting.company_domain,
                    title=posting.title,
                    description=posting.description,
                    location_raw=posting.location_raw,
                    remote_type=posting.remote_type,
                    role_family=posting.role_family,
                    posted_at=posting.posted_at,
                    fetched_at=posting.fetched_at,
                )
                db.add(posting_orm)
                db.flush()  # get the ID

            # Upsert verification
            existing_v = (
                db.query(VerificationORM)
                .filter_by(posting_id=posting_orm.id)
                .first()
            )
            if existing_v:
                ver_orm = existing_v
                ver_orm.trust_score = verification.trust_score
                ver_orm.genuinely_remote = verification.genuinely_remote
                ver_orm.remote_confidence = verification.remote_confidence
                ver_orm.scam_likelihood = verification.scam_likelihood
                ver_orm.scam_reasons = json.dumps(verification.scam_reasons)
                ver_orm.role_clarity = verification.role_clarity
                ver_orm.employer_legitimacy_signals = json.dumps(verification.employer_legitimacy_signals)
                ver_orm.newcomer_friendly_signals = json.dumps(verification.newcomer_friendly_signals)
                ver_orm.rationale = verification.rationale
            else:
                ver_orm = VerificationORM(
                    posting_id=posting_orm.id,
                    trust_score=verification.trust_score,
                    genuinely_remote=verification.genuinely_remote,
                    remote_confidence=verification.remote_confidence,
                    scam_likelihood=verification.scam_likelihood,
                    scam_reasons=json.dumps(verification.scam_reasons),
                    role_clarity=verification.role_clarity,
                    employer_legitimacy_signals=json.dumps(verification.employer_legitimacy_signals),
                    newcomer_friendly_signals=json.dumps(verification.newcomer_friendly_signals),
                    rationale=verification.rationale,
                    classifier_version=verification.classifier_version,
                )
                db.add(ver_orm)

            verification.posting_id = posting_orm.id
            candidates.append(RankCandidate(
                posting=posting,
                verification=verification,
                posting_id=posting_orm.id,
            ))

    print(f"[pipeline] Persisted {len(candidates)} postings to DB")

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
