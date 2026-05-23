from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional
from datetime import datetime


class Posting(BaseModel):
    source: str
    source_url: str
    external_id: str
    company: str
    company_domain: Optional[str] = None
    title: str
    description: str
    location_raw: Optional[str] = None
    remote_type: Optional[str] = None  # "fully_remote", "hybrid", "unknown"
    # "engineering", "design", "marketing", etc.
    role_family: Optional[str] = None
    posted_at: Optional[datetime] = None
    fetched_at: datetime = None

    def __init__(self, **data):
        if data.get("fetched_at") is None:
            data["fetched_at"] = datetime.utcnow()
        super().__init__(**data)


class VerificationResult(BaseModel):
    posting_id: int
    genuinely_remote: bool
    remote_confidence: float  # 0–1
    scam_likelihood: float    # 0–1
    scam_reasons: list[str] = []
    role_clarity: float       # 0–1
    employer_legitimacy_signals: list[str] = []
    newcomer_friendly_signals: list[str] = []
    trust_score: int          # 0–100
    rationale: str
    classifier_version: str = "1.0"
    verified_at: datetime = None

    def __init__(self, **data):
        if data.get("verified_at") is None:
            data["verified_at"] = datetime.utcnow()
        super().__init__(**data)


class FeedbackSignal(BaseModel):
    posting_id: int
    user_id: Optional[str] = "anonymous"
    signal: str   # "up" | "down"
    note: Optional[str] = None


class RankedPosting(BaseModel):
    """Combined posting + verification result returned by the API."""
    id: int
    source: str
    source_url: str
    company: str
    title: str
    description: str
    location_raw: Optional[str]
    remote_type: Optional[str]
    role_family: Optional[str]
    posted_at: Optional[datetime]
    trust_score: int
    genuinely_remote: bool
    scam_likelihood: float
    newcomer_friendly_signals: list[str]
    rationale: str
    seniority: Optional[str] = None  # "junior", "mid", "senior", "lead", "any"

    class Config:
        from_attributes = True
