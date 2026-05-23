"""
LLM-based job posting classifier using Claude Sonnet.

Two modes:
  - live: calls Anthropic API in batches of 10 postings per request
  - mock: returns deterministic scores based on rule signals (no API needed)

Output per posting:
  {
    "genuinely_remote": bool,
    "remote_confidence": 0–1,
    "scam_likelihood": 0–1,
    "scam_reasons": [...],
    "role_clarity": 0–1,
    "employer_legitimacy_signals": [...],
    "newcomer_friendly_signals": [...],
    "trust_score": 0–100,
    "rationale": "one sentence"
  }
"""

import json
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Posting, VerificationResult
from verify.rules import FilterResult


CLASSIFICATION_PROMPT = """You are an expert job posting analyst for Scale Without Borders Canada.
Your job is to evaluate remote job postings and determine their legitimacy, remote authenticity, and friendliness to newcomers.

For each posting, return a JSON object with EXACTLY these fields:
- genuinely_remote (boolean): true only if the role is verifiably, fully remote with no office attendance required
- remote_confidence (float 0-1): confidence in the remote assessment
- scam_likelihood (float 0-1): probability this is a scam or misleading posting
- scam_reasons (array of strings): specific scam signals detected (empty if none)
- role_clarity (float 0-1): how clearly defined the role and responsibilities are
- employer_legitimacy_signals (array of strings): signals the employer is legitimate (e.g. "established company domain", "clear job description")
- newcomer_friendly_signals (array of strings): signals welcoming to newcomers to Canada (e.g. "no Canadian experience required", "visa sponsorship")
- trust_score (integer 0-100): overall trust score (70+ = surface to users)
- rationale (string): one sentence explaining the trust score decision

Evaluate these {count} job postings and return a JSON array with one object per posting, in the same order:

{postings_json}

Return ONLY the JSON array, no other text."""


def _format_postings_for_prompt(postings: list[Posting]) -> str:
    formatted = []
    for i, p in enumerate(postings):
        formatted.append({
            "index": i,
            "title": p.title,
            "company": p.company,
            "company_domain": p.company_domain or "unknown",
            "description": p.description[:800],  # truncate to control token usage
            "location": p.location_raw or "unknown",
            "remote_type": p.remote_type or "unknown",
        })
    return json.dumps(formatted, indent=2)


def classify_live(
    postings: list[Posting],
    api_key: str,
    batch_size: int = 10,
    temperature: float = 0.1,
) -> list[dict]:
    """Call Claude API to classify postings in batches."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    all_results = []

    for i in range(0, len(postings), batch_size):
        batch = postings[i: i + batch_size]
        prompt = CLASSIFICATION_PROMPT.format(
            count=len(batch),
            postings_json=_format_postings_for_prompt(batch),
        )

        try:
            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            batch_results = json.loads(raw)
            all_results.extend(batch_results)
            print(f"[llm] Classified batch {i // batch_size + 1} ({len(batch)} postings)")
        except Exception as e:
            print(f"[llm] Error classifying batch {i // batch_size + 1}: {e}")
            # Fall back to mock scores for this batch
            for posting in batch:
                all_results.append(_mock_score_single(posting, []))

    return all_results


def _mock_score_single(posting: Posting, rule_result_flags: list[str]) -> dict:
    """
    Deterministic mock scoring — no API needed.
    Uses simple heuristics so results are reproducible and testable.
    """
    import re

    text = f"{posting.title} {posting.description} {posting.location_raw or ''}".lower()

    # Detect fake-remote
    fake_remote_hits = sum(1 for p in [
        r"hybrid", r"in.?office", r"must be located", r"occasional.*office",
        r"within \d+ miles", r"commute required"
    ] if re.search(p, text))

    genuinely_remote = fake_remote_hits == 0
    remote_confidence = max(0.1, 1.0 - (fake_remote_hits * 0.3))

    # Detect scam signals
    scam_hits = sum(1 for p in [
        r"earn \$\d+ per week", r"no experience needed", r"telegram", r"whatsapp",
        r"starter kit", r"guaranteed.*\$", r"get paid.*paypal"
    ] if re.search(p, text))

    scam_likelihood = min(1.0, scam_hits * 0.35)

    # Role clarity — longer descriptions tend to be more real
    role_clarity = min(1.0, len(posting.description) / 300)

    # Legitimacy signals
    legit_signals = []
    if posting.company_domain and posting.company_domain not in ("unknown", ""):
        legit_signals.append("known company domain")
    well_known = ["stripe", "shopify", "notion", "automattic", "gitlab", "zapier",
                  "buffer", "basecamp", "figma", "hubspot", "doist", "linear", "toptal"]
    if any(co in posting.company.lower() for co in well_known):
        legit_signals.append("well-known company")
    if len(posting.description) > 200:
        legit_signals.append("detailed job description")

    # Newcomer signals
    newcomer_signals = []
    for pattern, label in [
        (r"visa sponsorship", "visa sponsorship offered"),
        (r"no canadian experience", "no Canadian experience required"),
        (r"newcomer", "newcomer-friendly language"),
        (r"worldwide|any country|globally|anywhere", "open worldwide"),
    ]:
        if re.search(pattern, text):
            newcomer_signals.append(label)

    # Compute trust score
    trust = 50
    if genuinely_remote:
        trust += 20
    trust += int(role_clarity * 15)
    trust -= int(scam_likelihood * 60)
    trust += len(legit_signals) * 5
    trust += len(newcomer_signals) * 3
    if fake_remote_hits > 0:
        trust -= fake_remote_hits * 10
    trust = max(0, min(100, trust))

    # Rationale
    if scam_hits > 0:
        rationale = f"Flagged as likely scam ({scam_hits} scam signal(s) detected)."
    elif fake_remote_hits > 0:
        rationale = f"Listed as remote but contains {fake_remote_hits} office/location restriction(s)."
    elif trust >= 85:
        rationale = f"Highly trusted remote role from a verified employer ({posting.company})."
    elif trust >= 70:
        rationale = f"Legitimate remote posting from {posting.company} with good role clarity."
    else:
        rationale = f"Lower confidence — limited employer signals or unclear remote policy."

    return {
        "genuinely_remote": genuinely_remote,
        "remote_confidence": round(remote_confidence, 2),
        "scam_likelihood": round(scam_likelihood, 2),
        "scam_reasons": [f"scam signal detected" for _ in range(scam_hits)],
        "role_clarity": round(role_clarity, 2),
        "employer_legitimacy_signals": legit_signals,
        "newcomer_friendly_signals": newcomer_signals,
        "trust_score": trust,
        "rationale": rationale,
    }


def classify_mock(postings: list[Posting], filter_results: list[FilterResult]) -> list[dict]:
    """Mock classifier — deterministic scores using rule signals + heuristics."""
    results = []
    filter_map = {id(fr.posting): fr for fr in filter_results}

    for posting in postings:
        fr = filter_map.get(id(posting))
        flags = (fr.flags if fr else [])
        score = _mock_score_single(posting, flags)
        results.append(score)

    print(f"[llm] Mock-classified {len(results)} postings")
    return results


def classify(
    postings: list[Posting],
    filter_results: list[FilterResult],
    mode: str = "mock",
    api_key: Optional[str] = None,
) -> list[VerificationResult]:
    """
    Main entry point.
    Returns VerificationResult objects (posting_id is set to 0 here;
    the pipeline sets it after DB insertion).
    """
    if mode == "live" and api_key:
        raw_scores = classify_live(postings, api_key)
    else:
        raw_scores = classify_mock(postings, filter_results)

    results = []
    for posting, score in zip(postings, raw_scores):
        vr = VerificationResult(
            posting_id=0,  # filled in by pipeline after DB write
            genuinely_remote=score.get("genuinely_remote", False),
            remote_confidence=score.get("remote_confidence", 0.5),
            scam_likelihood=score.get("scam_likelihood", 0.0),
            scam_reasons=score.get("scam_reasons", []),
            role_clarity=score.get("role_clarity", 0.5),
            employer_legitimacy_signals=score.get("employer_legitimacy_signals", []),
            newcomer_friendly_signals=score.get("newcomer_friendly_signals", []),
            trust_score=score.get("trust_score", 50),
            rationale=score.get("rationale", ""),
        )
        results.append(vr)

    return results
