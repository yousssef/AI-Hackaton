"""
2.9 — Prompt validation: labeled test set with ≥85% agreement target.

Tests the mock classifier (verify/llm.py:classify_mock) against 30 hand-labeled
postings. Each posting has a known ground-truth label:
  - "pass"  → trust_score ≥ 70  (should surface to user)
  - "fail"  → trust_score  < 70  (should be suppressed)

Run:  pytest backend/tests/test_prompt_validation.py -v
"""

from verify.rules import FilterResult
from verify.llm import classify_mock
from models import Posting
import sys
import os
import pytest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_filter_results(postings: list[Posting]) -> list[FilterResult]:
    """Return default FilterResult objects (no flags set) for each posting."""
    return [FilterResult(posting=p) for p in postings]


def _make_posting(title: str, company: str, description: str,
                  location: str = "Remote", remote_type: str = "remote",
                  domain: str = "") -> Posting:
    return Posting(
        source="test",
        source_url="https://example.com/job/1",
        external_id="test-" + title[:20].replace(" ", "-").lower(),
        company=company,
        company_domain=domain or (company.lower().replace(" ", "") + ".com"),
        title=title,
        description=description,
        location_raw=location,
        remote_type=remote_type,
        role_family="engineering",
        posted_at=datetime(2026, 5, 1),
        fetched_at=datetime(2026, 5, 23),
    )


# ---------------------------------------------------------------------------
# Labeled dataset (30 postings)
# Each entry: (posting, expected_label)  label ∈ {"pass", "fail"}
# ---------------------------------------------------------------------------

LABELED_SET = [
    # ── PASS cases (genuine, legitimate remote roles) ──────────────────────

    (_make_posting(
        title="Senior Backend Engineer",
        company="Stripe",
        description=(
            "Stripe is looking for a Senior Backend Engineer to join our payments "
            "infrastructure team. You will design and build distributed systems that "
            "process billions of transactions. Fully remote, work from anywhere. "
            "Competitive salary, equity, and benefits. 5+ years backend experience required."
        ),
        domain="stripe.com",
    ), "pass"),

    (_make_posting(
        title="Frontend Engineer (React)",
        company="Notion",
        description=(
            "Notion is hiring a Frontend Engineer to improve our web editor. "
            "You'll work closely with design to ship delightful user experiences. "
            "This is a fully remote role open to candidates worldwide. "
            "We offer visa sponsorship for eligible candidates."
        ),
        domain="notion.so",
    ), "pass"),

    (_make_posting(
        title="DevOps Engineer",
        company="GitLab",
        description=(
            "GitLab is an all-remote company. We are seeking a DevOps Engineer "
            "to maintain and scale our CI/CD infrastructure. You will own "
            "deployment pipelines and SRE practices. No Canadian experience required. "
            "Candidates from any country are welcome."
        ),
        domain="gitlab.com",
    ), "pass"),

    (_make_posting(
        title="Data Scientist",
        company="Shopify",
        description=(
            "Shopify is hiring a Data Scientist for the merchant analytics team. "
            "You will build ML models to help merchants grow. Remote-first culture, "
            "flexible hours. Strong Python and SQL skills required. Detailed onboarding "
            "provided for newcomers to the e-commerce space."
        ),
        domain="shopify.com",
    ), "pass"),

    (_make_posting(
        title="Product Manager",
        company="Linear",
        description=(
            "Linear is building the future of project management. We need a Product "
            "Manager who can translate customer feedback into product decisions. "
            "Fully distributed team, async-first. 3+ years of PM experience. "
            "Competitive compensation and equity."
        ),
        domain="linear.app",
    ), "pass"),

    (_make_posting(
        title="Full Stack Engineer",
        company="Supabase",
        description=(
            "Supabase is an open-source Firebase alternative. We are hiring a Full "
            "Stack Engineer to build developer tools. Remote role, open to candidates "
            "globally including newcomers to Canada. Excellent documentation culture."
        ),
        domain="supabase.com",
    ), "pass"),

    (_make_posting(
        title="Technical Writer",
        company="Automattic",
        description=(
            "Automattic (makers of WordPress.com) is a fully distributed company. "
            "We are hiring a Technical Writer to document our REST API. "
            "Work from anywhere, asynchronous communication. Great benefits. "
            "Detailed description of responsibilities and expectations provided."
        ),
        domain="automattic.com",
    ), "pass"),

    (_make_posting(
        title="Machine Learning Engineer",
        company="Hugging Face",
        description=(
            "Hugging Face is looking for a Machine Learning Engineer to contribute "
            "to the transformers library and inference infrastructure. Open to candidates "
            "worldwide. Visa sponsorship available. Remote-first team with optional "
            "offices in New York and Paris. Clear career ladder and compensation bands."
        ),
        domain="huggingface.co",
    ), "pass"),

    (_make_posting(
        title="Customer Success Manager",
        company="Zapier",
        description=(
            "Zapier is a fully remote company with 700+ employees across 40+ countries. "
            "We are hiring a Customer Success Manager to help our small business customers. "
            "No prior Zapier experience needed — we provide thorough training. "
            "Salary range: $75,000–$90,000 USD. Newcomers to Canada welcome."
        ),
        domain="zapier.com",
    ), "pass"),

    (_make_posting(
        title="iOS Engineer",
        company="Buffer",
        description=(
            "Buffer is a transparent, fully remote company. We are hiring an iOS Engineer "
            "to build our social media scheduling app. We publish our salaries publicly. "
            "Must have 3+ years of Swift experience. Team is distributed across the globe."
        ),
        domain="buffer.com",
    ), "pass"),

    (_make_posting(
        title="Site Reliability Engineer",
        company="Cloudflare",
        description=(
            "Cloudflare is seeking a Site Reliability Engineer to ensure 99.99% uptime "
            "for our global network. You will work on incidents, capacity planning, and "
            "automation. Remote role based anywhere. Detailed responsibilities and team "
            "structure outlined. Strong Kubernetes and Go skills needed."
        ),
        domain="cloudflare.com",
    ), "pass"),

    (_make_posting(
        title="UI/UX Designer",
        company="Figma",
        description=(
            "Figma is hiring a UI/UX Designer to improve our onboarding flow. "
            "You'll run user research, create wireframes, and collaborate with engineers. "
            "Fully remote option available. Competitive salary with equity. "
            "3+ years product design experience required."
        ),
        domain="figma.com",
    ), "pass"),

    (_make_posting(
        title="Backend Engineer — Infrastructure",
        company="Temporal",
        description=(
            "Temporal builds the open source platform for durable execution. "
            "We are hiring a backend engineer to work on our cloud infrastructure. "
            "Fully remote team, candidates worldwide welcome. Equity and healthcare included. "
            "Must be comfortable with distributed systems and Go or Java."
        ),
        domain="temporal.io",
    ), "pass"),

    (_make_posting(
        title="Content Marketing Manager",
        company="HubSpot",
        description=(
            "HubSpot is hiring a Content Marketing Manager to grow our inbound traffic. "
            "You'll write blog posts, case studies, and email campaigns. Remote role, "
            "open globally. Great benefits package. 2+ years B2B content experience needed."
        ),
        domain="hubspot.com",
    ), "pass"),

    (_make_posting(
        title="Software Engineer — Distributed Systems",
        company="CockroachDB",
        description=(
            "CockroachLabs is hiring a Software Engineer to work on our distributed SQL "
            "database. Fully remote role open worldwide. You'll work on consensus protocols, "
            "storage engines, and query optimization. Strong C++ or Go background preferred. "
            "We offer comprehensive benefits and career growth opportunities."
        ),
        domain="cockroachlabs.com",
    ), "pass"),

    # ── FAIL cases (scams, fake-remote, vague, or suspicious) ───────────────

    (_make_posting(
        title="Work From Home Data Entry Clerk",
        company="EasyJobsNetwork",
        description=(
            "Earn $500–$800 per week from home! No experience needed. "
            "Just type data into our system. Get paid weekly via PayPal or Venmo. "
            "Contact us on Telegram @easyjobs. Starter kit required, $49 refundable deposit."
        ),
        domain="easyjobsnetwork.xyz",
    ), "fail"),

    (_make_posting(
        title="Remote Customer Support Representative",
        company="GlobalHireNow",
        description=(
            "Guaranteed $1200 per week! Work from home, set your own hours. "
            "No interview needed. Just sign up and start earning. "
            "Send your resume to our WhatsApp: +1-555-0199. Limited spots available!"
        ),
        domain="globalhirenow.net",
    ), "fail"),

    (_make_posting(
        title="Online Survey Taker",
        company="QuickCashSurveys",
        description=(
            "Get paid to take surveys from home. Earn up to $50 per survey. "
            "No experience needed. Telegram group for onboarding. "
            "Starter kit purchase required to unlock higher-paying surveys."
        ),
        domain="quickcashsurveys.biz",
    ), "fail"),

    (_make_posting(
        title="Remote Sales Agent — Uncapped Commission",
        company="DiamondEarningsGroup",
        description=(
            "Work from home and earn $2000–$5000 per week! No experience needed. "
            "We provide training via Telegram. Get paid daily via PayPal. "
            "Send your details to WhatsApp to get started today."
        ),
        domain="diamondearningsgroup.info",
    ), "fail"),

    (_make_posting(
        title="Virtual Assistant",
        company="HomeJobsUS",
        description=(
            "Earn $25/hr as a virtual assistant. No experience needed. "
            "Work 2–3 hours per day and make guaranteed income. "
            "Email us to receive your starter kit instructions. Very limited spots."
        ),
        domain="homejobsus.biz",
    ), "fail"),

    (_make_posting(
        title="Software Engineer",
        company="TechCorp",
        description="We are hiring. Send CV.",
        domain="techcorp-careers.xyz",
    ), "fail"),

    (_make_posting(
        title="Marketing Specialist",
        company="BestJobs",
        description="Great opportunity. Apply now. Must be located within 30 miles of downtown Toronto.",
        location="Toronto, ON — hybrid",
        remote_type="hybrid",
        domain="bestjobs.ca",
    ), "fail"),

    (_make_posting(
        title="Remote Data Analyst",
        company="DataFarm",
        description=(
            "Remote role but must commute to our office in Vancouver 3 days per week. "
            "Occasional office visits required for team meetings. "
            "Listed as remote but within 50 miles of our office preferred."
        ),
        location="Vancouver — occasional office",
        remote_type="remote",
        domain="datafarm.co",
    ), "fail"),

    (_make_posting(
        title="Crypto Investment Manager",
        company="CryptoWealth",
        description=(
            "Manage crypto portfolios and earn commissions. "
            "Telegram onboarding. No experience needed. "
            "Get paid in Bitcoin weekly. Guaranteed returns."
        ),
        domain="cryptowealthnow.io",
    ), "fail"),

    (_make_posting(
        title="Business Development Representative",
        company="NetworkMarketingPros",
        description=(
            "Join our team and earn unlimited income! Refer friends and earn $500 per referral. "
            "No experience needed. Contact us on WhatsApp for the starter kit. "
            "Work from home, set your own hours, guaranteed earnings from day one."
        ),
        domain="networkmarketingpros.net",
    ), "fail"),

    (_make_posting(
        title="Package Reshipping Agent",
        company="GlobalLogisticsHome",
        description=(
            "Work from home receiving and reshipping packages. Earn $40 per package. "
            "No experience needed. Paid weekly via Zelle or CashApp. "
            "Contact recruiter on Telegram to apply."
        ),
        domain="globallogisticshome.biz",
    ), "fail"),

    (_make_posting(
        title="Social Media Manager",
        company="ClickFarm",
        description=(
            "Earn $800 per week liking posts and managing fake social media accounts. "
            "Work from home, flexible hours. No experience needed. "
            "Starter kit $99, fully refundable after first month."
        ),
        domain="clickfarm.xyz",
    ), "fail"),

    (_make_posting(
        title="Hiring Now — Multiple Positions",
        company="GlobalTalentHub",
        description=(
            "We are hiring for multiple positions immediately. "
            "No experience required. Earn $600–$1,200 per week guaranteed. "
            "Contact us via Telegram or WhatsApp. Very limited positions available."
        ),
        domain="globaltalenthub.cc",
    ), "fail"),

    (_make_posting(
        title="Remote Typist",
        company="TypeAndEarn",
        description=(
            "Earn money typing at home. $0.05 per word typed. "
            "No experience required. Starter kit required to access job board ($35). "
            "Pay via PayPal every Friday. Contact us on WhatsApp."
        ),
        domain="typeAndEarn.biz",
    ), "fail"),

    (_make_posting(
        title="Amazon Reviewer",
        company="ReviewBoost",
        description=(
            "Get paid to review Amazon products from home. "
            "Keep the products and earn $20–$50 per review. "
            "No experience needed. Onboarding via Telegram. "
            "Apply now — limited spots, earn guaranteed income today."
        ),
        domain="reviewboost.io",
    ), "fail"),
]


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

AGREEMENT_THRESHOLD = 0.85


def test_prompt_validation_agreement():
    """
    Mock classifier must agree with hand-labeled ground truth on ≥85% of
    the 30 labeled postings.
    """
    postings = [p for p, _ in LABELED_SET]
    ground_truth = [label for _, label in LABELED_SET]

    results = classify_mock(postings, _empty_filter_results(postings))
    assert len(results) == len(LABELED_SET), (
        f"classify_mock returned {len(results)} results for {len(LABELED_SET)} inputs"
    )

    correct = 0
    mismatches = []
    for i, (result, expected) in enumerate(zip(results, ground_truth)):
        trust = result.get("trust_score", 0)
        predicted = "pass" if trust >= 70 else "fail"
        if predicted == expected:
            correct += 1
        else:
            mismatches.append(
                f"  [{i:02d}] '{postings[i].title}' @ {postings[i].company}: "
                f"expected={expected}, got={predicted} (trust={trust})"
            )

    agreement = correct / len(LABELED_SET)
    mismatch_report = "\n".join(mismatches)
    assert agreement >= AGREEMENT_THRESHOLD, (
        f"Agreement {agreement:.1%} < {AGREEMENT_THRESHOLD:.0%} threshold "
        f"({correct}/{len(LABELED_SET)} correct)\n"
        f"Mismatches:\n{mismatch_report}"
    )
    print(
        f"\n[prompt-validation] Agreement: {agreement:.1%} ({correct}/{len(LABELED_SET)})")


def test_all_postings_return_required_fields():
    """Every result must contain the expected schema fields."""
    postings = [p for p, _ in LABELED_SET]
    results = classify_mock(postings, _empty_filter_results(postings))
    required = {
        "genuinely_remote", "remote_confidence", "scam_likelihood",
        "scam_reasons", "role_clarity", "employer_legitimacy_signals",
        "newcomer_friendly_signals", "trust_score", "rationale",
    }
    for i, r in enumerate(results):
        missing = required - r.keys()
        assert not missing, f"Result {i} missing fields: {missing}"


def test_known_scam_gets_low_trust():
    """A posting with multiple explicit scam signals must score below 40."""
    scam = _make_posting(
        title="Work From Home Easy Money",
        company="ScamCo",
        description=(
            "Earn $800 per week guaranteed! No experience needed. "
            "Get paid via PayPal. Contact us on Telegram for starter kit."
        ),
    )
    results = classify_mock([scam], _empty_filter_results([scam]))
    assert results[0]["trust_score"] < 40, (
        f"Scam posting scored too high: {results[0]['trust_score']}"
    )


def test_known_legitimate_gets_high_trust():
    """A well-described posting from a known company must score ≥ 70."""
    legit = _make_posting(
        title="Senior Software Engineer",
        company="Stripe",
        description=(
            "Stripe is seeking a Senior Software Engineer to work on payments infrastructure. "
            "Fully remote, open to candidates worldwide. Competitive compensation with equity. "
            "5+ years experience required. Detailed job description with clear responsibilities."
        ),
        domain="stripe.com",
    )
    results = classify_mock([legit], _empty_filter_results([legit]))
    assert results[0]["trust_score"] >= 70, (
        f"Legitimate posting scored too low: {results[0]['trust_score']}"
    )
