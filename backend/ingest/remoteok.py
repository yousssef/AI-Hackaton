"""
RemoteOK public API ingestion.
Endpoint: https://remoteok.com/api  (no auth required)
Normalises entries to the shared Posting schema.
"""

from models import Posting
import hashlib
import re
import sys
import os
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

REMOTEOK_API = "https://remoteok.com/api"

ROLE_FAMILY_MAP = [
    ("engineering", r"engineer|developer|backend|frontend|full.?stack|devops|sre|ios|android|mobile|ml|machine learning|data scientist"),
    ("design", r"design|ux|ui|product design|visual"),
    ("marketing", r"marketing|seo|content|growth|brand|copywriter|social media"),
    ("product", r"product manager|pm|product owner"),
    ("data", r"data analyst|data entry|analytics|bi |business intelligence"),
    ("finance", r"finance|accounting|financial|cfo|controller"),
    ("hr", r"recruiter|hr |human resources|talent|people ops"),
    ("sales", r"sales|account executive|customer success|account manager"),
    ("support", r"support|customer service|customer care|helpdesk"),
]


def _detect_role_family(title: str, description: str) -> str:
    text = (title + " " + (description or "")).lower()
    for family, pattern in ROLE_FAMILY_MAP:
        if re.search(pattern, text):
            return family
    return "other"


def _clean_html(raw: str) -> str:
    if not raw:
        return ""
    return BeautifulSoup(raw, "html.parser").get_text(separator=" ", strip=True)


def _parse_epoch(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def fetch_remoteok(limit: int = 50) -> list[Posting]:
    """Fetch and normalise postings from RemoteOK public API."""
    try:
        headers = {"User-Agent": "ScaleWithoutBorders-JobVerifier/1.0"}
        response = httpx.get(REMOTEOK_API, headers=headers,
                             timeout=15, follow_redirects=True)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print(f"[remoteok] Fetch failed: {exc}")
        return []

    # First element is a legal notice dict — skip non-job items
    jobs = [item for item in data if isinstance(
        item, dict) and item.get("id") and item.get("position")]

    postings: list[Posting] = []
    now = datetime.utcnow()

    for job in jobs[:limit]:
        title = job.get("position", "").strip()
        company = job.get("company", "").strip()
        if not title or not company:
            continue

        description = _clean_html(job.get("description", ""))
        tags = job.get("tags") or []
        location_raw = ", ".join(job.get("location") or []) or "Remote"
        source_url = job.get("url", "")
        if source_url and not source_url.startswith("http"):
            source_url = f"https://remoteok.com{source_url}"

        # Build a stable external ID from the RemoteOK numeric id
        external_id = hashlib.md5(str(job.get("id", "")).encode()).hexdigest()
        company_domain = re.sub(r"[^a-z0-9]", "", company.lower()) + ".com"

        postings.append(Posting(
            source="remoteok",
            source_url=source_url,
            external_id=external_id,
            company=company,
            company_domain=company_domain,
            title=title,
            description=description,
            location_raw=location_raw,
            remote_type="remote",
            role_family=_detect_role_family(title, description),
            posted_at=_parse_epoch(job.get("epoch") or job.get("date")),
            fetched_at=now,
        ))

    print(f"[remoteok] Fetched {len(postings)} postings")
    return postings
