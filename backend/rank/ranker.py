"""
Ranking layer — applies hard filter then soft-sorts the surviving postings.

Hard filter (P0):
  - trust_score >= MIN_TRUST_SCORE (default 70)
  - genuinely_remote = True
  - posted within 14 days

Soft ranking (P1):
  - freshness (newer = higher)
  - newcomer-friendliness (more signals = higher)
  - trust score (higher = higher)
"""

from models import Posting, VerificationResult, RankedPosting
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ---------------------------------------------------------------------------
# Seniority detection
# ---------------------------------------------------------------------------

SENIORITY_PATTERNS = [
    ("junior",  r"junior|entry.?level|entry level|associate|jr\.?\s|new grad|graduate"),
    ("senior",  r"senior|sr\.?\s|staff\s|principal|experienced"),
    ("lead",    r"\blead\b|tech lead|team lead|engineering manager|\bem\b"),
    ("mid",     r"mid.?level|mid level|intermediate"),
]


def detect_seniority(title: str, description: str = "") -> str:
    """Return 'junior', 'mid', 'senior', 'lead', or 'any'."""
    text = (title + " " + (description[:300] or "")).lower()
    for level, pattern in SENIORITY_PATTERNS:
        if re.search(pattern, text):
            return level
    return "any"


@dataclass
class RankCandidate:
    posting: Posting
    verification: VerificationResult
    posting_id: int
    rank_score: float = 0.0


def _days_ago(posted_at: Optional[datetime]) -> int:
    if posted_at is None:
        return 999
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - posted_at).days


def hard_filter(
    candidates: list[RankCandidate],
    min_trust_score: int = 70,
    max_days: int = 14,
) -> list[RankCandidate]:
    """Drop anything that doesn't clear the bar."""
    passed = []
    for c in candidates:
        v = c.verification
        if not v.genuinely_remote:
            continue
        if v.trust_score < min_trust_score:
            continue
        if _days_ago(c.posting.posted_at) > max_days:
            continue
        passed.append(c)

    print(f"[rank] {len(passed)}/{len(candidates)} passed hard filter")
    return passed


def soft_rank(candidates: list[RankCandidate]) -> list[RankCandidate]:
    """Score and sort candidates. Higher = better."""
    for c in candidates:
        age = _days_ago(c.posting.posted_at)
        # 1.0 = posted today, 0.0 = 14 days ago
        freshness = max(0, 14 - age) / 14
        newcomer_boost = min(
            len(c.verification.newcomer_friendly_signals) * 0.05, 0.2)
        trust_norm = c.verification.trust_score / 100

        c.rank_score = (trust_norm * 0.5) + (freshness *
                                             0.35) + (newcomer_boost * 0.15)

    return sorted(candidates, key=lambda c: c.rank_score, reverse=True)


def to_ranked_postings(candidates: list[RankCandidate]) -> list[RankedPosting]:
    out = []
    for c in candidates:
        p = c.posting
        v = c.verification
        out.append(RankedPosting(
            id=c.posting_id,
            source=p.source,
            source_url=p.source_url,
            company=p.company,
            title=p.title,
            description=p.description,
            location_raw=p.location_raw,
            remote_type=p.remote_type,
            role_family=p.role_family,
            posted_at=p.posted_at,
            trust_score=v.trust_score,
            genuinely_remote=v.genuinely_remote,
            scam_likelihood=v.scam_likelihood,
            newcomer_friendly_signals=v.newcomer_friendly_signals,
            rationale=v.rationale,
            seniority=detect_seniority(p.title, p.description),
        ))
    return out


def rank(
    candidates: list[RankCandidate],
    min_trust_score: int = 70,
    max_days: int = 14,
) -> list[RankedPosting]:
    filtered = hard_filter(candidates, min_trust_score, max_days)
    sorted_candidates = soft_rank(filtered)
    return to_ranked_postings(sorted_candidates)
