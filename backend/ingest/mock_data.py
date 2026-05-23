"""
Static mock job postings that mimic real We Work Remotely RSS entries.
Used for offline testing and demo fallback.
Covers a range of quality: legitimate roles, fake-remote, scammy, etc.
"""

from datetime import datetime, timedelta

_NOW = datetime.utcnow()

MOCK_POSTINGS = [
    # --- Legitimate, clearly remote engineering roles ---
    {
        "external_id": "mock-001",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-001",
        "company": "Stripe",
        "company_domain": "stripe.com",
        "title": "Senior Backend Engineer",
        "description": (
            "Stripe is looking for a Senior Backend Engineer to join our Payments Infrastructure team. "
            "This is a fully remote role open to candidates worldwide. You will work on distributed systems "
            "that process billions of dollars in transactions. We offer competitive compensation, equity, "
            "and a home-office stipend. No Canadian work experience required."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=2),
    },
    {
        "external_id": "mock-002",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-002",
        "company": "Shopify",
        "company_domain": "shopify.com",
        "title": "Staff Frontend Engineer (React)",
        "description": (
            "Join Shopify's Platform team as a Staff Frontend Engineer. "
            "Fully distributed team — work from anywhere. "
            "We're looking for engineers with deep React and TypeScript expertise. "
            "We actively encourage applications from newcomers to Canada and internationally. "
            "Visa sponsorship available for qualified candidates."
        ),
        "location_raw": "Remote - Canada or USA",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=5),
    },
    {
        "external_id": "mock-003",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-003",
        "company": "Notion",
        "company_domain": "notion.so",
        "title": "Product Designer",
        "description": (
            "Notion is hiring a Product Designer to shape how millions of people organize their work. "
            "Remote-first culture, async by default. Open to candidates globally. "
            "You will collaborate closely with engineers and PMs on our core editor experience."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "design",
        "posted_at": _NOW - timedelta(days=1),
    },
    {
        "external_id": "mock-004",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-004",
        "company": "Automattic",
        "company_domain": "automattic.com",
        "title": "Data Engineer",
        "description": (
            "Automattic (WordPress.com, WooCommerce, Tumblr) is a fully distributed company with no HQ. "
            "We're hiring a Data Engineer to build and maintain our analytics infrastructure. "
            "Competitive salary paid in USD. Equipment budget. Work from anywhere."
        ),
        "location_raw": "Anywhere",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=7),
    },
    {
        "external_id": "mock-005",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-005",
        "company": "HubSpot",
        "company_domain": "hubspot.com",
        "title": "Content Marketing Manager",
        "description": (
            "HubSpot's Content team is looking for a Content Marketing Manager. "
            "Remote eligible across North America. You'll own our blog strategy and SEO roadmap. "
            "3+ years experience in content or editorial roles required."
        ),
        "location_raw": "Remote - USA / Canada",
        "remote_type": "fully_remote",
        "role_family": "marketing",
        "posted_at": _NOW - timedelta(days=3),
    },
    # --- Fake-remote (claims remote, actually hybrid/office) ---
    {
        "external_id": "mock-006",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-006",
        "company": "FinanceCo Inc",
        "company_domain": "financecohr.com",
        "title": "Remote Financial Analyst",
        "description": (
            "Join our dynamic team as a Remote Financial Analyst! "
            "This role is hybrid — you must be located in the Greater Toronto Area. "
            "Occasional travel to our downtown Toronto office will be required. "
            "Strong Excel skills needed."
        ),
        "location_raw": "Toronto, Ontario (Hybrid)",
        "remote_type": "hybrid",
        "role_family": "finance",
        "posted_at": _NOW - timedelta(days=4),
    },
    {
        "external_id": "mock-007",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-007",
        "company": "MidMarket Solutions",
        "company_domain": "midmarketsolutions.ca",
        "title": "Remote Customer Success Manager",
        "description": (
            "We are hiring a Customer Success Manager. While this role is listed as remote, "
            "candidates must be located within 50 miles of our Montreal office for occasional in-person meetings. "
            "Must have Canadian work experience."
        ),
        "location_raw": "Montreal, QC (Remote-ish)",
        "remote_type": "hybrid",
        "role_family": "sales",
        "posted_at": _NOW - timedelta(days=6),
    },
    # --- Scam / low quality postings ---
    {
        "external_id": "mock-008",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-008",
        "company": "Work From Home Pros",
        "company_domain": "wfhpros-hire.net",
        "title": "Data Entry Specialist - Earn $500/week from home!",
        "description": (
            "Earn $500 per week from the comfort of your home! No experience needed. "
            "Simple data entry tasks. Flexible hours. Get paid weekly via PayPal. "
            "Contact us on Telegram: @wfhpros_hire or email wfhpros@gmail.com. "
            "Must purchase a starter kit ($49) before starting."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "data",
        "posted_at": _NOW - timedelta(days=1),
    },
    {
        "external_id": "mock-009",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-009",
        "company": "Global Opportunity Network",
        "company_domain": "globalopp-network.biz",
        "title": "Remote Brand Ambassador - $800/week guaranteed",
        "description": (
            "Work from home as a Brand Ambassador! Guaranteed $800/week — no experience needed. "
            "Set your own schedule. Contact recruiter Jane Smith via WhatsApp: +1-555-0199. "
            "This is a legitimate opportunity for anyone who wants to earn money online."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "marketing",
        "posted_at": _NOW - timedelta(days=2),
    },
    # --- Stale postings (over 30 days) ---
    {
        "external_id": "mock-010",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-010",
        "company": "OldStartup Inc",
        "company_domain": "oldstartup.io",
        "title": "Full Stack Developer",
        "description": (
            "We are looking for a Full Stack Developer to join our growing team. "
            "Fully remote. Experience with React and Node.js required."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=45),
    },
    # --- More solid legitimate roles ---
    {
        "external_id": "mock-011",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-011",
        "company": "Buffer",
        "company_domain": "buffer.com",
        "title": "DevOps Engineer",
        "description": (
            "Buffer is a fully remote company. We're hiring a DevOps Engineer to manage our AWS infrastructure. "
            "Open to candidates from any country. We've been remote-first since 2010. "
            "Transparent salaries, async culture."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=3),
    },
    {
        "external_id": "mock-012",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-012",
        "company": "GitLab",
        "company_domain": "gitlab.com",
        "title": "Backend Engineer - Ruby on Rails",
        "description": (
            "GitLab is an all-remote company with team members in 65+ countries. "
            "We are looking for a Backend Engineer with strong Ruby on Rails experience. "
            "Competitive salary. Stock options. Flexible time off."
        ),
        "location_raw": "Remote - Global",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=8),
    },
    {
        "external_id": "mock-013",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-013",
        "company": "Zapier",
        "company_domain": "zapier.com",
        "title": "Senior Product Manager",
        "description": (
            "Zapier is a remote-first company. We're looking for a Senior Product Manager "
            "to lead our integrations platform. Open globally. No Canadian experience required. "
            "We support visa processing for top candidates."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "product",
        "posted_at": _NOW - timedelta(days=10),
    },
    {
        "external_id": "mock-014",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-014",
        "company": "Doist",
        "company_domain": "doist.com",
        "title": "iOS Engineer",
        "description": (
            "Doist (Todoist, Twist) is fully remote — no offices, no headquarters. "
            "We're hiring an iOS Engineer to work on Todoist. "
            "Work from wherever inspires you. Async-first. Genuinely worldwide."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=6),
    },
    {
        "external_id": "mock-015",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-015",
        "company": "Toptal",
        "company_domain": "toptal.com",
        "title": "Technical Recruiter",
        "description": (
            "Toptal is looking for a Technical Recruiter to help source and screen top engineering talent. "
            "Remote globally. You'll work across time zones with our talent acquisition team."
        ),
        "location_raw": "Remote - Worldwide",
        "remote_type": "fully_remote",
        "role_family": "hr",
        "posted_at": _NOW - timedelta(days=9),
    },
    # --- Borderline / ambiguous ---
    {
        "external_id": "mock-016",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-016",
        "company": "RegionalBank",
        "company_domain": "regionalbank.ca",
        "title": "Remote Banking Advisor",
        "description": (
            "Join our team as a Remote Banking Advisor. This role is available to Ontario residents only. "
            "You will occasionally be required to attend our head office in Mississauga for training."
        ),
        "location_raw": "Ontario, Canada",
        "remote_type": "hybrid",
        "role_family": "finance",
        "posted_at": _NOW - timedelta(days=5),
    },
    {
        "external_id": "mock-017",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-017",
        "company": "Basecamp",
        "company_domain": "basecamp.com",
        "title": "Customer Support Specialist",
        "description": (
            "Basecamp is hiring a Customer Support Specialist. "
            "We are a remote company and have been since 2004. "
            "Open to candidates in the Americas (USA, Canada, Latin America). "
            "Flexible hours, strong benefits."
        ),
        "location_raw": "Remote - Americas",
        "remote_type": "fully_remote",
        "role_family": "support",
        "posted_at": _NOW - timedelta(days=4),
    },
    {
        "external_id": "mock-018",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-018",
        "company": "Linear",
        "company_domain": "linear.app",
        "title": "Growth Engineer",
        "description": (
            "Linear is a remote-first product company building the best issue tracker. "
            "We're looking for a Growth Engineer to own our activation and conversion funnel. "
            "Open to candidates worldwide. Competitive equity."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=2),
    },
    # --- Duplicate (same role as mock-001, different source_url) ---
    {
        "external_id": "mock-019",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-019",
        "company": "Stripe",
        "company_domain": "stripe.com",
        "title": "Senior Backend Engineer",
        "description": (
            "Stripe is looking for a Senior Backend Engineer to join our Payments Infrastructure team. "
            "This is a fully remote role open to candidates worldwide."
        ),
        "location_raw": "Worldwide",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=2),  # Same as mock-001 — dedup test
    },
    {
        "external_id": "mock-020",
        "source": "weworkremotely",
        "source_url": "https://weworkremotely.com/remote-jobs/mock-020",
        "company": "Figma",
        "company_domain": "figma.com",
        "title": "Machine Learning Engineer",
        "description": (
            "Figma is hiring a Machine Learning Engineer to improve our AI-assisted design features. "
            "Remote eligible. We welcome candidates from diverse backgrounds and geographies. "
            "Newcomers and international candidates encouraged to apply."
        ),
        "location_raw": "Remote - USA / Canada / Europe",
        "remote_type": "fully_remote",
        "role_family": "engineering",
        "posted_at": _NOW - timedelta(days=1),
    },
]
