# 🏆 Feature Implementation Tracker
## AI-Powered Remote Job Verification Tool — Scale Without Borders Canada
**Hackathon Timeline:** 3 Days | **Target:** Deployable prototype at a public URL

---

## Legend
| Status | Meaning |
|--------|---------|
| ⬜ TODO | Not started |
| 🔄 IN PROGRESS | Being built |
| ✅ DONE | Complete & tested |
| ❌ BLOCKED | Waiting on dependency |
| 🔁 STRETCH | Nice-to-have, only if ahead |

| Priority | Meaning |
|----------|---------|
| 🔴 P0 | Must-have — demo breaks without it |
| 🟡 P1 | Should-have — demo weakened without it |
| 🟢 P2 | Nice-to-have — polish / v2 |

---

## 📦 Layer 0 — Foundation & Infra

| # | Feature | Priority | Effort | Owner | Status | Notes |
|---|---------|----------|--------|-------|--------|-------|
| 0.1 | Repo setup (GitHub, branch strategy, `.env.example`) | 🔴 P0 | XS | — | ⬜ TODO | Day 1 morning |
| 0.2 | DB schema: `postings`, `verifications`, `feedback` tables | 🔴 P0 | S | — | ⬜ TODO | SQLite for hackathon; Supabase Postgres if time allows |
| 0.3 | Pydantic models for `Posting`, `Verification`, `Feedback` | 🔴 P0 | S | — | ⬜ TODO | Shared types across all layers |
| 0.4 | Config/secrets loader (`python-dotenv`) + `ANTHROPIC_API_KEY` | 🔴 P0 | XS | — | ⬜ TODO | Needed before any LLM calls |
| 0.5 | Scheduled refresh runner (`apscheduler` or cron — every 4–6h) | 🟡 P1 | S | — | ⬜ TODO | Can stub with a manual trigger on Day 1 |
| 0.6 | Seed snapshot of DB for demo fallback (local-mode) | 🟡 P1 | S | — | ⬜ TODO | Protects demo from live API failures |
| 0.7 | README with setup instructions + handoff doc | 🟡 P1 | M | — | ⬜ TODO | Required by Definition of Done |
| 0.8 | Deploy backend to Render / Railway / Fly.io free tier | 🟡 P1 | S | — | ⬜ TODO | Day 3 |

---

## 🔌 Layer 1 — Ingestion

> **Goal:** Pull real, current remote postings from structured, high-quality sources.

| # | Feature | Priority | Effort | Owner | Status | Notes |
|---|---------|----------|--------|-------|--------|-------|
| 1.1 | **Greenhouse** Job Board API ingestion | 🔴 P0 | S | — | ⬜ TODO | First source; free public JSON API |
| 1.2 | **RemoteOK** public API ingestion | 🔴 P0 | S | — | ⬜ TODO | High-quality remote-only feed |
| 1.3 | **Remotive** public API ingestion | 🔴 P0 | S | — | ⬜ TODO | Tech-focused remote roles |
| 1.4 | **Lever** postings API ingestion | 🟡 P1 | S | — | ⬜ TODO | Add after 1.1–1.3 are stable |
| 1.5 | RSS ingestion for We Work Remotely / Working Nomads (`feedparser`) | 🟡 P1 | S | — | ⬜ TODO | Fast to add with `feedparser` |
| 1.6 | Normalize all sources to shared `Posting` schema | 🔴 P0 | M | — | ⬜ TODO | Title, company, description, location, posted_at, source_url |
| 1.7 | Persist raw payloads to DB with `fetched_at` timestamp | 🔴 P0 | S | — | ⬜ TODO | Store raw + normalized side-by-side |
| 1.8 | Adzuna API ingestion (broader coverage) | 🟢 P2 | S | — | ⬜ TODO | Stretch — higher noise |

---

## 🧠 Layer 2 — Verification (AI Core)

> **Goal:** Score every posting on trust, remote authenticity, and scam likelihood.

### 2A — Rule-Based Filters (fast, cheap, run first)

| # | Feature | Priority | Effort | Owner | Status | Notes |
|---|---------|----------|--------|-------|--------|-------|
| 2.1 | **Posting age filter** — drop >30 days, flag >14 days | 🔴 P0 | XS | — | ⬜ TODO | First guard |
| 2.2 | **Company existence check** — domain resolves? Clearbit or DNS check | 🟡 P1 | S | — | ⬜ TODO | Clearbit free tier or simple `socket.getaddrinfo` |
| 2.3 | **Red-flag language scanner** — regex for scam patterns | 🔴 P0 | S | — | ⬜ TODO | "earn $X/week", "no experience", payment requests, Telegram contact, Gmail recruiter |
| 2.4 | **Remote authenticity checker** — detect fake-remote language | 🔴 P0 | S | — | ⬜ TODO | Regex for "hybrid", "must be in office", "occasional travel" |
| 2.5 | **Duplicate detection** — hash on (company + title + posted_date) | 🔴 P0 | XS | — | ⬜ TODO | Prevents same role from 2 sources flooding feed |

### 2B — LLM Classifier (deeper signal, Claude Sonnet 4.5)

| # | Feature | Priority | Effort | Owner | Status | Notes |
|---|---------|----------|--------|-------|--------|-------|
| 2.6 | **LLM classification prompt** — structured JSON output per posting | 🔴 P0 | M | — | ⬜ TODO | Returns: `genuinely_remote`, `remote_confidence`, `scam_likelihood`, `trust_score`, `rationale`, etc. |
| 2.7 | **Batch API calls** — 10–20 postings per call | 🔴 P0 | S | — | ⬜ TODO | Keeps cost to ~$2 per 1,000 postings |
| 2.8 | **Persist LLM response JSON** to `verifications` table | 🔴 P0 | XS | — | ⬜ TODO | Full response stored for UI transparency |
| 2.9 | **Prompt validation** — labeled test set of 30 postings, target ≥85% agreement | 🟡 P1 | M | — | ⬜ TODO | Day 2 morning; tune prompt based on failures |
| 2.10 | **Temperature locked at 0.0–0.2** for consistency | 🔴 P0 | XS | — | ⬜ TODO | Config-level setting |
| 2.11 | **Newcomer-friendliness signals** detection | 🟡 P1 | S | — | ⬜ TODO | No "Canadian experience" required, visa sponsorship mention, inclusive language |

---

## 📊 Layer 3 — Ranking & Relevance

> **Goal:** Surface what matters to Scale Without Borders members, not just what's legitimate.

| # | Feature | Priority | Effort | Owner | Status | Notes |
|---|---------|----------|--------|-------|--------|-------|
| 3.1 | **Hard filter** — `trust_score ≥ 70`, `genuinely_remote = true`, posted ≤14 days | 🔴 P0 | XS | — | ⬜ TODO | Gate for anything surfaced to users |
| 3.2 | **Soft ranking** — freshness weight | 🟡 P1 | S | — | ⬜ TODO | Newer postings rank higher within same trust band |
| 3.3 | **Soft ranking** — newcomer-friendliness boost | 🟡 P1 | S | — | ⬜ TODO | Boost roles flagged as newcomer-friendly |
| 3.4 | **Seniority distribution** — avoid all-senior-eng feed | 🟡 P1 | S | — | ⬜ TODO | Mix seniority levels in surfaced results |
| 3.5 | **Role family matching** — filter by role category (eng, design, marketing, etc.) | 🟡 P1 | M | — | ⬜ TODO | Needed for filter UI in Layer 4 |
| 3.6 | **Embedding-based semantic matching** (Voyage/OpenAI embeddings, cosine sim, top-K) | 🟢 P2 | L | — | ⬜ TODO | Stretch — personalization fast-follow |

---

## 🖥️ Layer 4 — Delivery (Web Dashboard)

> **Goal:** One polished delivery channel — Next.js dashboard deployed to Vercel.

| # | Feature | Priority | Effort | Owner | Status | Notes |
|---|---------|----------|--------|-------|--------|-------|
| 4.1 | **Next.js project scaffold** (App Router + Tailwind + shadcn/ui) | 🔴 P0 | S | — | ⬜ TODO | Day 2 afternoon |
| 4.2 | **Posting list page** — top 50 verified roles | 🔴 P0 | M | — | ⬜ TODO | Core demo surface |
| 4.3 | **Trust score badge** on each posting card | 🔴 P0 | S | — | ⬜ TODO | Color-coded (green ≥85, yellow 70–84) |
| 4.4 | **"Why we surfaced this" rationale** display | 🔴 P0 | S | — | ⬜ TODO | 1-sentence LLM rationale shown on card or expand |
| 4.5 | **Remote badge** — "Verified Remote" label | 🔴 P0 | XS | — | ⬜ TODO | Visual trust signal |
| 4.6 | **Apply link** per posting | 🔴 P0 | XS | — | ⬜ TODO | Links to original source URL |
| 4.7 | **Role family filter** (Engineering, Design, Marketing, etc.) | 🟡 P1 | S | — | ⬜ TODO | Dropdown or tab UI |
| 4.8 | **Freshness filter** (last 7 days / last 14 days) | 🟡 P1 | XS | — | ⬜ TODO | Quick toggle |
| 4.9 | **Feedback buttons** — 👍 / 👎 per posting → writes to `feedback` table | 🟡 P1 | S | — | ⬜ TODO | Day 3 midday |
| 4.10 | **CSV export** for Scale Without Borders staff | 🟡 P1 | S | — | ⬜ TODO | One-click download of current filtered list |
| 4.11 | **Deploy to Vercel** free tier | 🔴 P0 | S | — | ⬜ TODO | Required by Definition of Done |
| 4.12 | **API endpoint** — `/api/postings` (JSON) for digest/email use | 🟢 P2 | S | — | ⬜ TODO | Enables Option B (email digest) without extra work |
| 4.13 | **Newcomer-friendly badge** on eligible postings | 🟢 P2 | XS | — | ⬜ TODO | Visual differentiator for Scale Without Borders audience |

---

## 🔁 Stretch / v2 Features

| # | Feature | Priority | Notes |
|---|---------|----------|-------|
| S.1 | Per-member personalized ranking | 🟢 P2 | Requires member profiles — explicitly v2 |
| S.2 | Login / member auth | 🟢 P2 | Out of scope for hackathon |
| S.3 | Slack / email digest delivery channel | 🟢 P2 | Use CSV export as proxy for now |
| S.4 | Discord bot embed | 🟢 P2 | Only if Scale Without Borders requests it on Day 1 call |
| S.5 | Multi-language support | 🟢 P2 | v2 |

---

## 🗓️ Day-by-Day Execution Map

### Day 1 — Foundation (target: pipeline skeleton running end-to-end)
- [ ] 0.1 Repo + env setup
- [ ] 0.2 DB schema
- [ ] 0.3 Pydantic models
- [ ] 0.4 Secrets config
- [ ] 1.1 Greenhouse ingestion
- [ ] 1.2 RemoteOK ingestion
- [ ] 1.3 Remotive ingestion
- [ ] 1.6 Normalize to shared schema
- [ ] 1.7 Persist to DB
- [ ] 2.1 Posting age filter
- [ ] 2.3 Red-flag language scanner
- [ ] 2.4 Remote authenticity checker
- [ ] 2.5 Duplicate detection
- [ ] 2.6 LLM classification prompt (draft + manual test on 50 postings)

**End-of-Day-1 Gate:** 500+ raw postings in DB, rule filters passing, LLM prompt tested manually.

---

### Day 2 — Verification + Interface (target: end-to-end pipeline + live UI)
- [ ] 2.7 Batch LLM API calls across corpus
- [ ] 2.8 Persist LLM responses
- [ ] 2.9 Prompt validation (30-posting labeled set, ≥85% agreement)
- [ ] 2.10 Lock temperature
- [ ] 2.11 Newcomer-friendliness signals
- [ ] 1.4 Lever ingestion
- [ ] 3.1 Hard filter
- [ ] 3.2 Freshness ranking
- [ ] 3.3 Newcomer boost
- [ ] 4.1 Next.js scaffold
- [ ] 4.2 Posting list page
- [ ] 4.3 Trust score badge
- [ ] 4.4 Rationale display
- [ ] 4.5 Remote badge
- [ ] 4.6 Apply links

**End-of-Day-2 Gate:** UI live with real data; end-to-end pipeline runs.

---

### Day 3 — Polish, Audit, Demo (target: deployed, audited, demo-ready)
- [ ] Fresh ingestion run + 30-posting manual audit (target ≥85% verified)
- [ ] Fix top classifier failures
- [ ] 4.7 Role family filter
- [ ] 4.8 Freshness filter
- [ ] 4.9 Feedback buttons
- [ ] 4.10 CSV export
- [ ] 0.6 Seed snapshot (demo fallback)
- [ ] 4.11 Deploy to Vercel
- [ ] 0.8 Deploy backend
- [ ] 0.7 README + handoff doc
- [ ] Record 3-min Loom as demo backup

**End-of-Day-3 Gate (Definition of Done):** Public URL live, ≥50 verified postings refreshed within 24h, each with trust score + rationale, ≥85% verified-posting rate on sampled audit, README lets Scale Without Borders run it independently.

---

## 🧮 Effort Key
| Label | Est. Time |
|-------|-----------|
| XS | < 30 min |
| S | 30 min – 2 hrs |
| M | 2–4 hrs |
| L | 4–8 hrs |

---

## 📌 Total Feature Count
| Layer | P0 | P1 | P2 | Total |
|-------|----|----|-----|-------|
| Layer 0 — Infra | 4 | 4 | 0 | 8 |
| Layer 1 — Ingestion | 5 | 2 | 1 | 8 |
| Layer 2 — Verification | 7 | 3 | 0 | 10 |
| Layer 3 — Ranking | 1 | 4 | 1 | 6 |
| Layer 4 — Delivery | 7 | 4 | 2 | 13 |
| Stretch / v2 | 0 | 0 | 5 | 5 |
| **Total** | **24** | **17** | **9** | **50** |

**Hackathon scope: 24 P0s + 17 P1s = 41 features across 3 days.**
Focus on P0s first — a clean demo with all 24 P0s beats a half-finished attempt at everything.
