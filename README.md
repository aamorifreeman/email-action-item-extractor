# InboxIQ

Turn messy emails into structured action items — tasks, deadlines, people, and priority — with a rule-based NLP pipeline or Gemini, side by side.

## What it does

Paste an email (or a whole thread) and InboxIQ extracts every action item into a structured card:

- **Task** — the actual ask, cleaned up ("Can you send the slides…" → "Send the slides")
- **Due date** — deadline phrases like "by Friday", "next week", "EOD"
- **People** — names mentioned in each task
- **Priority** — flagged High when urgency words appear (ASAP, urgent, immediately…)
- **Source sentence** — where in the email the task came from

From there you can save tasks for the session, mark them done, export everything to CSV, or open a prefilled Google Calendar event for any task (no OAuth needed — it uses Calendar's quick-add URL).

## Two extraction engines

The interesting part of this project is that you can run the same email through two approaches and compare:

1. **Rule-Based NLP** — a hand-built pipeline using spaCy and regex:
   - sentence segmentation, then clause splitting on commas and "and" so "do A, do B, and do C" becomes three tasks
   - action-verb detection (send, review, follow up, schedule, …)
   - due-date extraction via regex patterns plus `dateparser` as a fallback
   - people via spaCy `PERSON` NER, with a heuristic for "follow up with X" patterns NER tends to mislabel
   - urgency-word scan for priority

2. **Gemini AI Extraction** — sends the email to Google's Gemini (`gemini-2.5-flash-lite`, falling back to `gemini-2.5-flash`) with a strict JSON-only prompt, then validates and normalizes the response into the exact same schema. Includes retry logic for transient failures — and if Gemini fails entirely, the app automatically falls back to the rule-based pipeline so you always get results.

Both engines return the same data shape, so the rest of the app doesn't care which one produced the results.

## Tech stack

- **Python 3.10+**
- **Streamlit** — multipage UI (Extract / Tasks / Integrations) with custom CSS theming
- **spaCy** — sentence segmentation and named-entity recognition
- **dateparser** — natural-language date phrase detection
- **google-genai** — Gemini API client for the LLM extraction mode

## Setup

```bash
git clone https://github.com/aamorifreeman/email-action-item-extractor.git
cd email-action-item-extractor
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

The spaCy model is optional — without it the app falls back to a blank pipeline with sentence splitting only (people extraction will be weaker).

**Gemini API key** (only needed for the AI extraction mode; rule-based works without it):

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit .streamlit/secrets.toml and paste your key
```

Get a free key from [Google AI Studio](https://aistudio.google.com/apikey). The app also picks up a `GEMINI_API_KEY` environment variable. `secrets.toml` is gitignored — never commit it.

## Run

```bash
streamlit run app.py
```

To sanity-check your Gemini key outside the app:

```bash
python test_gemini.py
```

## Project structure

```
app.py                  # Entrypoint: page config, sidebar, navigation
extractor.py            # Both extraction engines (rule-based + Gemini)
inboxiq_state.py        # Session state, save/dedupe, CSV export, Calendar links
inboxiq_components.py   # Reusable task-card UI
inboxiq_styles.py       # Global CSS / dark theme
views/
  extract.py            # Main page: paste email → extract → results
  tasks.py              # Saved tasks: toggle done, delete, export
  integrations.py       # Calendar quick-add, CSV downloads, roadmap
test_gemini.py          # Standalone Gemini connectivity check
```

## Notes & limitations

- Saved tasks live in Streamlit session state — they reset when the session ends. Persistent storage and real Google Tasks / Notion integrations are on the roadmap.
- Due dates are kept as the original human phrase ("Friday", "next week") rather than resolved to absolute dates; Calendar quick-add only sets a concrete time for "today"/"tomorrow".
- The rule-based engine is intentionally simple (action-verb matching) — it misses implicit asks that the Gemini mode catches. That gap is the point of the comparison.
