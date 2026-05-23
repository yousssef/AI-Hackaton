"""
We Work Remotely RSS ingestion.
Fetches from https://weworkremotely.com/remote-jobs.rss and normalises entries
to the shared Posting schema.
Falls back to mock data if INGEST_MODE=mock or the feed is unreachable.
"""

from models import Posting
import feedparser
import hashlib
import re
import sys
import os
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

WWR_FEEDS = [
    "https://weworkremotely.com/remote-jobs.rss",
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-marketing-jobs.rss",
]

# Role family keyword map (order matters — first match wins)
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
    text = (title + " " + description).lower()
    for family, pattern in ROLE_FAMILY_MAP:
        if re.search(pattern, text):
            return family
    return "other"


def _clean_html(html: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()


def _parse_company_from_title(raw_title: str) -> tuple[str, str]:
    """
    WWR titles are formatted as "Job Title at Company Name".
    Returns (title, company).
    """
    if " at " in raw_title:
        parts = raw_title.split(" at ", 1)
        return parts[0].strip(), parts[1].strip()
    return raw_title.strip(), "Unknown"


def _make_external_id(company: str, title: str, posted_at: Optional[datetime]) -> str:
    date_str = posted_at.strftime("%Y-%m-%d") if posted_at else "unknown"
    raw = f"{company.lower()}-{title.lower()}-{date_str}"
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_posted_at(entry) -> Optional[datetime]:
    try:
        if hasattr(entry, "published"):
            return dateutil_parser.parse(entry.published)
        if hasattr(entry, "updated"):
            return dateutil_parser.parse(entry.updated)
    except Exception:
        pass
    return None


def fetch_postings() -> list[Posting]:
    """
    Fetch postings from all WWR RSS feeds.
    Returns a deduplicated list of Posting objects.
    """
    seen_ids = set()
    postings = []

    for feed_url in WWR_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                print(f"[wwr] Failed to parse feed: {feed_url}")
                continue

            for entry in feed.entries:
                raw_title = getattr(entry, "title", "")
                title, company = _parse_company_from_title(raw_title)
                description_html = getattr(entry, "summary", "") or getattr(
                    entry, "description", "")
                description = _clean_html(description_html)
                source_url = getattr(entry, "link", "")
                region = getattr(entry, "region", [{}])
                location_raw = region[0].get(
                    "value", "Worldwide") if region else "Worldwide"
                posted_at = _parse_posted_at(entry)

                ext_id = _make_external_id(company, title, posted_at)
                if ext_id in seen_ids:
                    continue
                seen_ids.add(ext_id)

                posting = Posting(
                    source="weworkremotely",
                    source_url=source_url,
                    external_id=ext_id,
                    company=company,
                    company_domain=None,
                    title=title,
                    description=description,
                    location_raw=location_raw,
                    remote_type="unknown",
                    role_family=_detect_role_family(title, description),
                    posted_at=posted_at,
                )
                postings.append(posting)

        except Exception as e:
            print(f"[wwr] Error fetching {feed_url}: {e}")
            continue

    print(f"[wwr] Fetched {len(postings)} postings from live RSS")
    return postings


def fetch_postings_mock() -> list[Posting]:
    """Return mock postings for offline testing."""
    from ingest.mock_data import MOCK_POSTINGS
    postings = []
    for data in MOCK_POSTINGS:
        postings.append(Posting(**data))
    print(f"[wwr] Loaded {len(postings)} mock postings")
    return postings


def get_postings(mode: str = "mock") -> list[Posting]:
    """Entry point — mode is 'live' or 'mock'."""
    if mode == "live":
        postings = fetch_postings()

        # Merge RemoteOK postings
        try:
            from ingest.remoteok import fetch_remoteok
            remoteok_postings = fetch_remoteok()
            postings = postings + remoteok_postings
            print(
                f"[ingest] Combined total: {len(postings)} postings (WWR + RemoteOK)")
        except Exception as exc:
            print(f"[ingest] RemoteOK merge failed (non-fatal): {exc}")

        # Merge Remotive postings
        try:
            from ingest.remotive import fetch_remotive
            remotive_postings = fetch_remotive()
            postings = postings + remotive_postings
            print(
                f"[ingest] Combined total: {len(postings)} postings (+ Remotive)")
        except Exception as exc:
            print(f"[ingest] Remotive merge failed (non-fatal): {exc}")

        # Merge Working Nomads postings
        try:
            from ingest.workingnomads import fetch_workingnomads
            wn_postings = fetch_workingnomads()
            postings = postings + wn_postings
            print(
                f"[ingest] Combined total: {len(postings)} postings (+ Working Nomads)")
        except Exception as exc:
            print(f"[ingest] Working Nomads merge failed (non-fatal): {exc}")

        # Merge Lever postings
        try:
            from ingest.lever import fetch_lever
            lever_postings = fetch_lever()
            postings = postings + lever_postings
            print(
                f"[ingest] Combined total: {len(postings)} postings (+ Lever)")
        except Exception as exc:
            print(f"[ingest] Lever merge failed (non-fatal): {exc}")

        if not postings:
            print("[wwr] Live fetch returned 0 postings — falling back to mock")
            return fetch_postings_mock()
        return postings
    return fetch_postings_mock()
