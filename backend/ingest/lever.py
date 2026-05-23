"""
Lever job board ingestion.
Lever exposes a public postings endpoint per company:
  GET https://api.lever.co/v0/postings/{company}?mode=json&commitment=remote
No API key needed for public listings.
"""

from models import Posting
import hashlib
import re
import sys
import os
import time
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

LEVER_BASE = "https://api.lever.co/v0/postings"

# Remote-friendly companies known to use Lever — extend as needed
LEVER_COMPANIES = [
    "netlify",
    "vercel",
    "stripe",
    "notion",
    "linear",
    "supabase",
    "planetscale",
    "render",
    "fly",
    "retool",
    "brex",
    "mercury",
    "benchling",
    "temporal",
    "turso",
    "grafana",
    "posthog",
    "loom",
    "figma",
    "miro",
]

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


def _make_external_id(company_slug: str, lever_id: str) -> str:
    raw = f"lever-{company_slug}-{lever_id}"
    return hashlib.md5(raw.encode()).hexdigest()


def _fetch_company(client: httpx.Client, company: str, now: datetime) -> list[Posting]:
    """Fetch remote postings for a single Lever company slug."""
    url = f"{LEVER_BASE}/{company}"
    params = {"mode": "json", "commitment": "remote"}
    try:
        resp = client.get(url, params=params, timeout=10)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[lever] {company}: fetch error — {exc}")
        return []

    postings: list[Posting] = []
    for item in data:
        lever_id = item.get("id", "")
        title = item.get("text", "").strip()
        if not title or not lever_id:
            continue

        teams = item.get("categories", {}).get("team", "")
        commitment = item.get("categories", {}).get("commitment", "")
        location_raw = item.get("categories", {}).get("location", "Remote")

        # Combine all description blocks
        description_html = ""
        for block in item.get("descriptionBody", "") or []:
            if isinstance(block, dict):
                description_html += block.get("content", "")
            elif isinstance(block, str):
                description_html += block
        if not description_html:
            description_html = item.get(
                "description", "") or item.get("descriptionPlain", "")
        description = _clean_html(description_html) or item.get(
            "descriptionPlain", "")

        posted_at_ms = item.get("createdAt")
        posted_at: Optional[datetime] = None
        if posted_at_ms:
            try:
                posted_at = datetime.utcfromtimestamp(posted_at_ms / 1000)
            except Exception:
                pass

        source_url = item.get(
            "hostedUrl", f"https://jobs.lever.co/{company}/{lever_id}")
        company_name = item.get("company", company.title())

        postings.append(Posting(
            source="lever",
            source_url=source_url,
            external_id=_make_external_id(company, lever_id),
            company=company_name,
            company_domain=f"{company}.com",
            title=title,
            description=description,
            location_raw=location_raw or "Remote",
            remote_type="remote",
            role_family=_detect_role_family(title, description),
            posted_at=posted_at,
            fetched_at=now,
        ))

    return postings


def fetch_lever(max_per_company: int = 10) -> list[Posting]:
    """Fetch remote postings from all configured Lever companies."""
    now = datetime.utcnow()
    all_postings: list[Posting] = []

    with httpx.Client(headers={"Accept": "application/json"}) as client:
        for company in LEVER_COMPANIES:
            results = _fetch_company(client, company, now)
            all_postings.extend(results[:max_per_company])
            time.sleep(0.2)  # polite delay between company requests

    print(
        f"[lever] Fetched {len(all_postings)} postings across {len(LEVER_COMPANIES)} companies")
    return all_postings
