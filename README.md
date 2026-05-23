# Scale Without Borders — Verified Remote Jobs

An AI-powered remote job board that ingests postings from multiple sources, filters out scams and fake-remote listings, and surfaces only trust-verified opportunities to newcomers to Canada.

---

## Architecture

```
Ingestion → Rule filters → LLM classifier (Claude Sonnet) → Ranker → API → Next.js UI
```

| Layer | Tech |
|-------|------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, SQLite |
| LLM | Anthropic Claude Sonnet (claude-sonnet-4-5) |
| Scheduler | APScheduler (6-hour refresh) |
| Frontend | Next.js 16, Tailwind v4, TypeScript |
| Deploy | Vercel (frontend), Render/Railway (backend) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/) (optional — mock mode works without one)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY, INGEST_MODE, CLASSIFIER_MODE

uvicorn main:app --reload --port 8000
```

API is now live at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI is now live at `http://localhost:3000`.

---

## Environment Variables

Create `backend/.env` from `backend/.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | `mock-key` | Anthropic API key for LLM classification |
| `INGEST_MODE` | `mock` | `mock` uses local sample data; `live` hits real APIs |
| `CLASSIFIER_MODE` | `mock` | `mock` uses heuristic scoring; `live` calls Claude |
| `DATABASE_URL` | `sqlite:////tmp/jobs.db` | SQLAlchemy database URL |
| `MAX_POSTING_AGE_DAYS` | `30` | Drop postings older than this |
| `MIN_TRUST_SCORE` | `70` | Minimum trust score to surface a posting |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/postings` | Ranked, verified feed. Query: `role_family`, `limit`, `days` |
| `GET` | `/api/postings/{id}` | Single posting detail |
| `POST` | `/api/feedback` | Submit thumbs up/down feedback |
| `POST` | `/api/refresh` | Trigger a fresh pipeline run |
| `GET` | `/api/export/csv` | CSV download of current feed |
| `GET` | `/health` | Health check — shows next scheduled refresh |

---

## Job Sources

| Source | Type | File |
|--------|------|------|
| We Work Remotely | RSS | `ingest/wwr.py` |
| RemoteOK | Public API | `ingest/remoteok.py` |
| Remotive | Public API | `ingest/remotive.py` |
| Working Nomads | RSS | `ingest/workingnomads.py` |
| Lever | Per-company API | `ingest/lever.py` |

All sources are merged in `ingest/wwr.py:get_postings()`. Each source failure is non-fatal.

---

## Pipeline

1. **Ingest** — fetch postings from all sources (`INGEST_MODE=live`) or load mock data
2. **Rule filters** (`verify/rules.py`) — drop stale postings, flag fake-remote language, detect scam signals, check domain DNS
3. **LLM classification** (`verify/llm.py`) — Claude Sonnet scores each posting: `trust_score`, `genuinely_remote`, `scam_likelihood`, `newcomer_friendly_signals`
4. **Rank** (`rank/ranker.py`) — sort by trust score, detect seniority level
5. **Store** — upsert to SQLite via SQLAlchemy
6. **Serve** — FastAPI exposes ranked results; refreshes every 6 hours via APScheduler

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

Includes `tests/test_prompt_validation.py` — 30 labeled postings asserting ≥85% classifier agreement.

---

## Deployment

### Frontend (Vercel)

1. Push the repo to GitHub
2. Import the repo in [vercel.com](https://vercel.com) — set **Root Directory** to `frontend`
3. No environment variables needed for the frontend

### Backend (Render / Railway)

1. Create a new Web Service pointing to the `backend/` directory
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables: `ANTHROPIC_API_KEY`, `INGEST_MODE=live`, `CLASSIFIER_MODE=live`
5. Update `CORS` origins in `main.py` with your Vercel deployment URL

---

## Project Structure

```
backend/
  main.py            # FastAPI app, APScheduler, startup lifecycle
  config.py          # Settings (pydantic-settings, reads .env)
  models.py          # Pydantic models: Posting, RankedPosting, VerificationResult
  pipeline.py        # Orchestrates ingest → verify → rank → store
  requirements.txt
  api/
    routes.py        # All API endpoints
  db/
    database.py      # SQLAlchemy engine + session
    schema.py        # ORM models + create_tables()
  ingest/
    wwr.py           # WWR RSS + source aggregator (get_postings entry point)
    remoteok.py      # RemoteOK API
    remotive.py      # Remotive API
    workingnomads.py # Working Nomads RSS
    lever.py         # Lever per-company API
    mock_data.py     # Sample postings for local dev
  verify/
    rules.py         # Rule-based filters (age, fake-remote, scam, DNS)
    llm.py           # Claude Sonnet classifier + mock fallback
  rank/
    ranker.py        # Trust score sort + seniority detection
  tests/
    test_prompt_validation.py  # 30-posting labeled validation suite

frontend/
  app/
    page.tsx         # Main job board UI
    layout.tsx       # Root layout + fonts
    globals.css      # Tailwind v4 globals
  vercel.json        # Vercel deploy config + security headers
  next.config.ts     # Next.js config
```