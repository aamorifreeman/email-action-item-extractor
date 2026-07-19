# InboxIQ

Turn messy emails into structured action items — tasks, resolved deadlines, people,
priority, and a confidence score — with a rule-based NLP pipeline or Gemini, side by side.

InboxIQ is a full-stack application: a **FastAPI** backend built around an AI/ML extraction
pipeline, a persistent **SQLite** store, and a **React + Vite + TypeScript** frontend.

## What it does

Paste an email (or a whole thread) and InboxIQ extracts every action item into a structured card:

- **Task** — the actual ask, cleaned up ("Can you send the slides…" → "Send the slides")
- **Due date** — deadline phrases ("by Friday", "next week", "EOD") **resolved to a concrete date**
- **People** — names mentioned in each task
- **Priority** — a continuous urgency score (0–1) plus a High/Normal label
- **Confidence** — how strongly the pipeline trusts each extracted item
- **Source sentence** — where in the email the task came from

Save tasks (persisted in the database), toggle their status, export to CSV, or open a
prefilled Google Calendar event — no OAuth needed.

## The AI/ML pipeline (the core)

Whichever engine produces the raw items, they flow through one shared pipeline
(`backend/app/ml/pipeline.py`) so both engines get identical enrichment:

```
extract → resolve dates → score priority → score confidence → semantic dedup
```

- **Two extraction engines** behind a common interface (`ml/base.py`):
  - **Rule-Based NLP** (`ml/rule_based.py`) — spaCy + regex: sentence/clause splitting,
    action-verb detection, due-phrase capture, PERSON NER with a "follow up with X" heuristic.
  - **Gemini** (`ml/gemini.py`) — structured JSON output via a response schema, retries, and
    model fallback. If Gemini fails, the API transparently falls back to the rule engine.
- **Date resolution** (`ml/date_resolver.py`) — "Friday"/"next week"/"EOD" → an ISO date.
- **Priority scoring** (`ml/priority.py`) — weighted urgency lexicon → score + label.
- **Confidence scoring** (`ml/confidence.py`) — composite of action-verb strength, resolved
  date, attached person, and phrasing.
- **Semantic dedup + engine comparison** (`ml/embeddings.py`) — sentence-transformers
  embeddings merge near-duplicate tasks and power the `/extract/compare` agreement report.
  Falls back to a deterministic lexical vectorizer when the model can't be downloaded (offline/CI).

## API

Interactive docs at `http://localhost:8000/docs` once the backend is running.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/extract` | Extract with one engine (`rule` or `gemini`) |
| POST | `/api/extract/compare` | Run both engines + agreement report |
| POST | `/api/extract/batch` | Extract across many emails |
| GET/POST | `/api/tasks` | List / save tasks |
| POST | `/api/tasks/bulk` | Save many (with dedup) |
| PATCH/POST/DELETE | `/api/tasks/{id}` `/toggle` | Update / toggle status / delete |
| GET | `/api/tasks/export.csv` | CSV export |
| POST | `/api/integrations/calendar-link` | Google Calendar quick-add links |
| GET | `/health` | Health check |

## Tech stack

- **Backend:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, spaCy, dateparser,
  sentence-transformers, google-genai
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS
- **Tests:** pytest + httpx (13 tests, run fully offline)

## Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm      # optional; blank-pipeline fallback otherwise

cp .env.example .env                          # add GEMINI_API_KEY for the Gemini engine
uvicorn app.main:app --reload
```

The rule-based engine works with no API key. Get a free Gemini key at
[Google AI Studio](https://aistudio.google.com/apikey) for the AI engine.

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to the backend on :8000)
```

### Docker (both together)

```bash
GEMINI_API_KEY=your_key docker compose up --build
# frontend → http://localhost:5173   backend → http://localhost:8000
```

## Tests

```bash
cd backend && pytest
```

## Project structure

```
backend/
  app/
    main.py            # FastAPI app: CORS, lifespan (DB init + model warmup), routers
    config.py          # env-based settings
    database.py        # SQLAlchemy engine/session/Base
    models/task.py     # Task + Extraction ORM models
    schemas/           # Pydantic request/response models
    api/               # extraction, tasks, integrations routers
    ml/                # === AI/ML core: engines + pipeline ===
    services/          # task + extraction services
  tests/               # pytest suite
frontend/
  src/
    api/client.ts      # typed API wrapper
    types.ts           # types mirroring backend schemas
    pages/             # Extract, Tasks, Integrations
    components/        # TaskCard, EngineToggle, ComparePanel, ConfidenceBar
docker-compose.yml
```

## Notes & limitations

- Without network access the spaCy and sentence-transformer models can't download; the app
  degrades gracefully (blank spaCy pipeline + lexical embeddings) so it still runs and tests pass.
- Priority is scored per sentence, so the rule engine can miss urgency phrased in a separate
  sentence from the task — exactly the kind of gap the Gemini engine closes. Comparing the two
  is the point.
