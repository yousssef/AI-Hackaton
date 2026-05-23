"""
Working Nomads RSS ingestion.
Feed: https://www.workingnomads.com/jobs?tag=remote&format=rss
Uses feedparser — same pattern as wwr.py.
"""

from models import Posting
import hashlib
import re
import sys
import os
from datetime import datetime
from typing import Optional

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

WORKINGNOMADS_FEED = "https://www.workingnomads.com/jobs?tag=remote&format=rss"

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


def _parse_posted_at(entry) -> Optional[datetime]:
    try:
        if hasattr(entry, "published"):
            return dateutil_parser.parse(entry.published).replace(tzinfo=None)
        if hasattr(entry, "updated"):
            return dateutil_parser.parse(entry.updated).replace(tzinfo=None)
    except Exception:
        pass
    return None


def _make_external_id(title: str, company: str, posted_at: Optional[datetime]) -> str:
    date_str = posted_at.strftime("%Y-%m-%d") if posted_at else "unknown"
    raw = f"{company.lower().strip()}-{title.lower().strip()}-{date_str}"
    return hashlib.md5(raw.encode()).hexdigest()


def fetch_workingnomads() -> list[Posting]:
    """Fetch and normalise postings from Working Nomads RSS feed."""
    try:
        feed = feedparser.parse(WORKINGNOMADS_FEED)
        if feed.bozo and not feed.entries:
            print(f"[workingnomads] Failed to parse feed")
            return []
    except Exception as exc:
        print(f"[workingnomads] Fetch failed: {exc}")
        return []

    seen_ids: set[str] = set()
    postings: list[Posting] = []
    now = datetime.utcnow()

    for entry in feed.entries:
        title = getattr(entry, "title", "").strip()
        # Working Nomads titles are often "Job Title — Company" or "Job Title at Company"
        company = "Unknown"
        if " — " in title:
            parts = title.split(" — ", 1)
            title, company = parts[0].strip(), parts[1].strip()
        elif " at " in title:
            parts = title.split(" at ", 1)
            title, company = parts[0].strip(), parts[1].strip()

        description_html = getattr(entry, "summary", "") or getattr(
            entry, "description", "")
        description = _clean_html(description_html)
        source_url = getattr(entry, "link", "")
        posted_at = _parse_posted_at(entry)

        ext_id = _make_external_id(title, company, posted_at)
        if ext_id in seen_ids:
            continue
        seen_ids.add(ext_id)

        company_domain = re.sub(r"[^a-z0-9]", "", company.lower()) + ".com"

        postings.append(Posting(
            source="workingnomads",
            source_url=source_url,
            external_id=ext_id,
            company=company,
            company_domain=company_domain,
            title=title,
            description=description,
            location_raw="Worldwide",
            remote_type="remote",
            role_family=_detect_role_family(title, description),
            posted_at=posted_at,
            fetched_at=now,
        ))

    print(f"[workingnomads] Fetched {len(postings)} postings")
    return postings
