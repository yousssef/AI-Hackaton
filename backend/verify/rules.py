"""
Rule-based verification filters — fast, cheap, run before LLM.

Filters applied in order:
  1. Posting age         — drop >30 days, flag >14 days
  2. Red-flag language   — scam patterns
  3. Remote authenticity — detect fake-remote language
  4. Duplicate detection — hash(company + title + date)

Returns a FilterResult for each posting with pass/fail and reasons.
"""

import hashlib
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from models import Posting


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

SCAM_PATTERNS = [
    (r"earn\s+\$[\d,]+\s+(per|a)\s+week", "income claim"),
    (r"guaranteed\s+(income|pay|salary|\$)", "guaranteed income"),
    (r"no\s+experience\s+(needed|required|necessary)", "no experience needed"),
    (r"work\s+from\s+home\s+and\s+earn", "earn-from-home pitch"),
    (r"starter\s+kit|starter\s+pack|registration\s+fee|joining\s+fee",
     "upfront payment request"),
    (r"(contact|reach|message)\s+(us\s+)?(on|via|through|at)\s+(telegram|whatsapp)",
     "Telegram/WhatsApp recruiter contact"),
    (r"recruiter.*@(gmail|yahoo|hotmail|outlook)\.(com|ca)",
     "free-email recruiter address"),
    (r"wire\s+transfer|western\s+union|moneygram", "suspicious payment method"),
    (r"multi.?level|mlm|network\s+marketing|pyramid", "MLM indicator"),
    (r"get\s+paid\s+(daily|weekly)\s+via\s+paypal", "PayPal daily/weekly pay claim"),
]

FAKE_REMOTE_PATTERNS = [
    (r"must\s+be\s+located\s+(in|near|within)", "location restriction"),
    (r"(hybrid|in.?office|on.?site)\s*(position|role|work|schedule)?",
     "hybrid/office requirement"),
    (r"occasional(ly)?\s*(travel|visit|attend)\s*(to|the)?\s*(office|hq|headquarters)",
     "occasional office visit"),
    (r"within\s+\d+\s+(miles|km|kilometers)\s+of", "proximity requirement"),
    (r"(toronto|vancouver|montreal|calgary|ottawa|london|new york|san francisco|chicago)\s+(office|hq|based)",
     "city-office requirement"),
    (r"(commute|commuting)\s+required", "commute requirement"),
]

NEWCOMER_UNFRIENDLY_PATTERNS = [
    (r"canadian\s+(work\s+)?experience\s+required", "requires Canadian experience"),
    (r"must\s+have\s+.{0,30}canadian\s+experience",
     "requires Canadian experience"),
    (r"only\s+canadian\s+citizens", "Canadian citizens only"),
]

NEWCOMER_FRIENDLY_PATTERNS = [
    (r"visa\s+sponsorship\s+(available|provided|offered|considered)",
     "visa sponsorship offered"),
    (r"(open|welcome|encourage).*newcomer", "newcomer-friendly language"),
    (r"no\s+canadian\s+experience\s+required", "no Canadian experience required"),
    (r"candidates\s+from\s+(any|all)\s+countr", "open to all countries"),
    (r"work\s+from\s+(anywhere|any\s+country|any\s+location|worldwide)",
     "worldwide eligibility"),
]


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class FilterResult:
    posting: Posting
    passed: bool = True
    drop_reason: Optional[str] = None
    flags: list[str] = field(default_factory=list)
    fake_remote_signals: list[str] = field(default_factory=list)
    scam_signals: list[str] = field(default_factory=list)
    newcomer_unfriendly_signals: list[str] = field(default_factory=list)
    newcomer_friendly_signals: list[str] = field(default_factory=list)
    age_days: Optional[int] = None
    is_stale: bool = False   # >14 days but ≤30
    # None = not checked (no domain available)
    domain_exists: Optional[bool] = None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_age(posting: Posting, max_days: int = 30) -> tuple[bool, Optional[str], int, bool]:
    """Returns (passes, drop_reason, age_days, is_stale)."""
    if posting.posted_at is None:
        return True, None, -1, False

    # Make posted_at timezone-aware if needed
    posted = posting.posted_at
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    age_days = (now - posted).days

    if age_days > max_days:
        return False, f"posting is {age_days} days old (limit: {max_days})", age_days, False
    is_stale = age_days > 14
    return True, None, age_days, is_stale


def _scan_patterns(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    """Return list of matched reasons."""
    found = []
    lower = text.lower()
    for pattern, reason in patterns:
        if re.search(pattern, lower):
            found.append(reason)
    return found


def _check_domain_exists(domain: Optional[str]) -> Optional[bool]:
    """DNS-resolve the company domain. Returns None if domain is missing/unknown."""
    if not domain or domain in ("unknown", ""):
        return None
    # Strip protocol/path if accidentally included
    domain = re.sub(r"https?://", "", domain).split("/")[0].strip()
    try:
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror:
        return False


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

class DuplicateDetector:
    def __init__(self):
        self._seen: set[str] = set()

    def _hash(self, posting: Posting) -> str:
        date_str = posting.posted_at.strftime(
            "%Y-%m-%d") if posting.posted_at else "unknown"
        raw = f"{posting.company.lower().strip()}-{posting.title.lower().strip()}-{date_str}"
        return hashlib.md5(raw.encode()).hexdigest()

    def is_duplicate(self, posting: Posting) -> bool:
        h = self._hash(posting)
        if h in self._seen:
            return True
        self._seen.add(h)
        return False

    def reset(self):
        self._seen.clear()


# ---------------------------------------------------------------------------
# Main filter function
# ---------------------------------------------------------------------------

def apply_filters(
    postings: list[Posting],
    max_age_days: int = 30,
) -> list[FilterResult]:
    """
    Apply all rule-based filters to a list of postings.
    Returns a FilterResult for every posting (passed=True means it survives).
    """
    detector = DuplicateDetector()
    results: list[FilterResult] = []

    for posting in postings:
        result = FilterResult(posting=posting)
        combined_text = f"{posting.title} {posting.description} {posting.location_raw or ''}"

        # 1. Duplicate check (run first so dupes don't waste later checks)
        if detector.is_duplicate(posting):
            result.passed = False
            result.drop_reason = "duplicate posting"
            results.append(result)
            continue

        # 2. Age check
        passes_age, drop_reason, age_days, is_stale = _check_age(
            posting, max_age_days)
        result.age_days = age_days
        result.is_stale = is_stale
        if not passes_age:
            result.passed = False
            result.drop_reason = drop_reason
            results.append(result)
            continue

        # 3. Scam language scan
        scam_signals = _scan_patterns(combined_text, SCAM_PATTERNS)
        result.scam_signals = scam_signals
        if scam_signals:
            result.passed = False
            result.drop_reason = f"scam signals detected: {', '.join(scam_signals)}"
            results.append(result)
            continue

        # 4. Fake-remote detection (flag but don't hard-drop — LLM will score it)
        result.fake_remote_signals = _scan_patterns(
            combined_text, FAKE_REMOTE_PATTERNS)

        # 5. Newcomer signals (informational)
        result.newcomer_unfriendly_signals = _scan_patterns(
            combined_text, NEWCOMER_UNFRIENDLY_PATTERNS)
        result.newcomer_friendly_signals = _scan_patterns(
            combined_text, NEWCOMER_FRIENDLY_PATTERNS)

        # 6. Company domain existence check (flag only — not a hard drop)
        result.domain_exists = _check_domain_exists(posting.company_domain)
        if result.domain_exists is False:
            result.flags.append("company domain does not resolve")

        results.append(result)

    passed = sum(1 for r in results if r.passed)
    print(f"[rules] {passed}/{len(results)} postings passed rule filters")
    return results
