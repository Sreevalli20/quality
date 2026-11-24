# AirAware AI — Intelligent Urban Air Quality Assistant

**PromptWars Challenge 06**

AirAware AI is a Python + Streamlit application that helps urban residents —
individuals, families, students and communities — turn air-quality information
into practical everyday decisions. It does not just display pollution data: it
calculates a CPCB-method AQI, explains what it means, and generates personalised
guidance on outdoor activity, indoor protection, low-emission travel and daily
routines.

## Problem statement

Urban air pollution is a daily reality for millions of Indians, yet most people
cannot answer simple questions: *Is it safe to exercise today? Should I open my
windows? Is the metro better than my car for this trip? What can my household do
tonight?* AirAware AI answers these questions with transparent, auditable logic
and honest data provenance.

## Target users

- Office workers and students with fixed commutes
- Parents and caregivers managing children's exposure
- Fitness enthusiasts deciding between outdoor and indoor exercise
- Households wanting to cut emissions and save money
- Communities organising cleaner commuting and awareness drives

## Features

| Module | What it does |
|---|---|
| **Home** | Welcoming dashboard with guided entry choices (manual entry, CSV upload, labelled sample data, optional live provider fetch), a "Today's intelligence" card (AQI, dominant pollutant, best outdoor window, indoor-first flag, plan progress), alerts, feature tour and module CTAs |
| **Air Quality Explorer** | Guided pollutant form (empty fields, unit + plain-language hints), CPCB AQI assessment, sub-index charts, gauge, health guidance, data-completeness warnings, CSV comparison |
| **Personal AI Assistant** | Companion-style profile form → prioritised advice with *what / why / when / cost / alternative* per item; conversational follow-up Q&A labelled *AI* vs *rule-based*; optional AI briefing via pluggable provider (Gemini); stale-briefing invalidation; Markdown personal report download |
| **My Daily Air Plan** | Editable hour-by-hour schedule adapted to current AQI with a "now" time-slot marker; per-slot completion checkboxes with live progress tied to the active reading; regenerates when the reading changes; CSV download. Includes a **24-hour planning outlook**: likely AQI category per time window (diurnal model + bounded session trend, confidence-graded, never fabricated hourly readings) with best/worst windows, activity verdicts and ventilation guidance. All times shown in **your** timezone (sidebar selector — the deployed server runs UTC) |
| **Indoor Air Guardian** | Illustrated room-picker (bedroom, living room, kitchen, study, children's room), budget-tier tabs (free → higher-cost), smart ventilation advice, indoor-air sources guide |
| **Green Lifestyle Planner** | Personalised sustainable-living options across transport, energy, waste and household — with honest benefits *and* limitations; "I'll try this" shortlisting and a bridge to impact tracking |
| **Environmental Impact** | CO₂e savings estimator for mode shifts and AC reduction, action log with cumulative chart, CSV report |
| **Family & Community** | Household checklist with progress, child-friendly explainer, community action ideas, family plan |
| **About & Data Sources** | Methodology, assumptions and limitations |

## How it works

1. **Home → Start your air-quality check** — choose a guided path:
   *enter measurements* (empty fields with unit hints, partial data OK),
   *upload a CSV*, *explore labelled sample data*, or — when a provider
   key is configured — *fetch live monitoring data*.
2. **Assess** — pollutant concentrations are converted to sub-indices using
   official CPCB breakpoints; the overall AQI is the maximum sub-index.
3. **Decide** — a deterministic rule engine combines the AQI category,
   dominant pollutant and your profile into prioritised recommendations,
   each with what/why/when/cost/alternative. A labelled **day-ahead
   planning outlook** estimates likely AQI categories per time window so
   you can pick the safest outdoor and ventilation windows.
4. **Act & track** — daily plan, indoor improvements, greener swaps and a
   personal impact log with downloadable reports.

## AQI calculation methodology

- Implements the **CPCB National Air Quality Index (NAQI)** method.
- Each pollutant has published 24-hour breakpoints (8-hour for O₃); a
  concentration is mapped to a sub-index by **continuous piecewise-linear
  interpolation** through every breakpoint corner, so values inside the
  1-unit gaps between declared bands interpolate smoothly instead of
  jumping a full band.
- **Overall AQI = maximum sub-index**; that pollutant is the dominant one.
- Averaging periods follow CPCB (24 h, O₃ 8 h).
- **Partial measurements** (e.g. only PM2.5) produce a *partial* assessment —
  the app explicitly warns that the true AQI could be higher. It never
  fabricates missing pollutants.
- A directly supplied AQI is accepted only when no pollutant data exists.

Categories: Good (0–50), Satisfactory (51–100), Moderate (101–200), Poor
(201–300), Very Poor (301–400), Severe (401–500), Severe+ (>500).

## Data sources and provenance

Every measurement records **value, unit, source and timestamp**.

- **User-entered** — treated as user-provided, unverified.
- **CSV import** — parsed and validated locally; nothing is uploaded.
- **Sample demonstration data** — illustrative values for demos, always
  labelled *"NOT live"*; never presented as real readings.
- **Live provider data** *(optional)* — fetched on demand from configured
  providers (OpenAQ v3) via `airaware/providers.py`. Results keep the
  provider's own measurement timestamp and station name; readings older
  than 24 h are explicitly flagged as stale, never relabelled as current.
- **No reading is ever fabricated.** Without a provider key the app works
  fully offline from manual entry, CSV import or labelled samples.

CSV columns accept common aliases case-, whitespace- and
punctuation-insensitively (`pm25`, `PM2.5`, `PM 2.5`, `PM2.5 (µg/m3)`,
`no2`, `carbon monoxide`, `station name`, …). Unit-variant columns are
converted to canonical CPCB units where the conversion is exact
(e.g. `pm10 (mg/m3)` × 1000 → µg/m³; `CO (µg/m³)` ÷ 1000 → mg/m³);
columns in units that cannot be converted safely (e.g. ppm) are rejected
with an explicit warning. Optional columns: `aqi` (used only when no
pollutant columns have values for that row), `location`/`city`/`station`,
`timestamp`/`datetime`/`date`/`time`.

Robustness: uploads are limited to 2 MB / 5,000 rows; malformed lines are
counted and reported; identical rows (same location, time and values) are
de-duplicated; missing timestamps fall back to import time with a
warning; naive timestamps are assumed UTC with a warning; out-of-range
values are rejected, never silently corrected.

## Recommendation methodology

Recommendations are generated by a **deterministic Python rule engine**
(`airaware/recommendations.py`) that maps:

```
AQI category + dominant pollutant + user profile
    → prioritised actions with explicit reasons
```

Every recommendation displays **what to do, why it matters, when, an
approximate cost (only where defensible) and a practical alternative** —
so the logic is fully auditable.

**Optional AI briefing:** the assistant uses a pluggable provider
architecture (`airaware/ai.py`). If `GEMINI_API_KEY` (and optionally
`GEMINI_MODEL`, default `gemini-2.0-flash`) is set in
`.streamlit/secrets.toml` or Streamlit Cloud secrets, the Gemini provider
generates a natural-language briefing via Google's API. Calls use only
the Python standard library (`urllib`), a 25 s timeout, up to 3 attempts
with exponential backoff on transient errors (timeouts, 429, 5xx), and a
system instruction that forbids inventing figures. Inputs embedded in the
prompt are sanitised and framed as untrusted data; output is sanitised,
length-capped and HTML-escaped before display. A briefing is fingerprinted
to the exact reading + profile it was generated from — change either and
the app asks you to regenerate rather than showing stale AI text. Every
failure mode falls back to the rule engine, and AI output is always
labelled *AI-generated*. Additional providers can be registered in
`_PROVIDER_CLASSES` without touching the UI.

## Live data providers

`airaware/providers.py` defines an `AirQualityProvider` contract
(`configured()`, `health_check()`, `latest()`) with failover ordering in
`fetch_latest()`. `OpenAQProvider` implements it against the OpenAQ v3
API:

- Activate by setting `OPENAQ_API_KEY` in secrets (free key from
  openaq.org). A "Fetch live monitoring data" entry appears on Home.
- Results carry `source="external"`, the station name, the provider's own
  measurement timestamp, and per-pollutant unit validation (unexpected
  units are skipped, never misconverted).
- Readings older than 24 h are returned but flagged "freshest available,
  not current" — stale data is never presented as live.
- The About page shows each provider's configuration and health status.
- Any provider failure returns `None`; the UI falls back honestly to
  manual entry / CSV / samples.

## Environmental impact assumptions

Vehicle factors are generic CO₂e estimates (kg CO₂e per vehicle-km):

| Mode | Factor | Basis |
|---|---|---|
| Petrol car | 0.192 | ~18 km/l + upstream emissions |
| Diesel car | 0.171 | ~20 km/l |
| Electric car | 0.095 | Indian grid ≈0.82 kg CO₂/kWh |
| Petrol bike/scooter | 0.075 | ~45 km/l |
| CNG auto | 0.055 | per vehicle-km |
| Bus | 0.040 | per passenger-km |
| Metro/rail | 0.020 | per passenger-km |
| Cycle / walk | 0.000 | human power |

Fuel prices and economy are defaults the user can override. AC savings use a
typical 1.5 kW draw and the same grid factor. All figures are **estimates of
climate benefit** — explicitly distinguished from measured reductions and
from local PM2.5 reductions.

## Technology

- **Python 3.14.6** · **Streamlit** (UI) · **pandas** (CSV) · **plotly** (charts)
- Optional **Gemini API** via stdlib `urllib` — only when a key is configured
- No database, no required API keys, no paid services, no secrets in code
- All state lives in the browser session; reports are downloadable files

## Project structure

```
app.py                  Streamlit entry point (sidebar navigation + reading card)
airaware/
  aqi.py                CPCB breakpoints, sub-indices, categories
  data.py               Measurement model, sample data, CSV validation/import
  recommendations.py    Rule-based recommendation engine + UserProfile
  planner.py            Daily routine planner
  indoor.py             Indoor air content (rooms, budget tiers)
  lifestyle.py          Green lifestyle options + personalisation
  impact.py             Emission factors & impact calculations
  alerts.py             Rule-based alerts with severity labels
  ai.py                 Pluggable AI providers (Gemini: retries, sanitisation)
  providers.py          Live AQI data providers (OpenAQ) with health checks
  report.py             Personal Markdown report generator
  charts.py             Plotly chart helpers
  ui.py                 Design system, CSS, cards, navigation helpers
  pages.py              Page renderers for all modules
tests/                  pytest suite (unit tests + AppTest page/journey tests)
.streamlit/config.toml  Theme & server config
requirements.txt
README.md
```

## Installation & running

```bash
# Python 3.14.6 recommended (see limitations below)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 — the **Home** page offers guided ways to
load a reading: *enter measurements* manually, *upload a CSV*, *explore
labelled sample data*, and *fetch live data* when a provider key is
configured. The sidebar then navigates between the nine modules;
it always shows your current reading and its provenance.

### Try the sample data

Home → **Explore demonstration data** → pick a city → *Load this sample*.
All sample readings are labelled as non-live (`source: sample`) and a warning
banner appears wherever they are used.

### Enter measurements manually

Home or **Air Quality Explorer** → *Enter my own measurements*. Leave fields
empty for pollutants you don't know — partial data produces a partial,
honestly-labelled assessment rather than fabricated values. An overall AQI
can be entered directly and is used only when no pollutant values exist.

### Import real data (CSV format)

Export a CPCB / state-board / OpenAQ table to CSV. One row = one observation.

- **Pollutant columns** (at least one required, or an `aqi` column):
  `pm25`/`PM2.5`, `pm10`, `no2`, `so2`, `co` (mg/m³), `o3`, `nh3` — common
  aliases are accepted case-insensitively.
- **Optional columns:** `aqi` (used only when no pollutant columns have
  values for that row), `location`/`city`/`station`,
  `timestamp`/`datetime`/`date`/`time`.
- Limits: 2 MB, 5,000 rows. Values are range-checked; invalid cells are
  skipped with warnings, never silently corrected.

Upload via **Home → Upload my air-quality report**, or the CSV comparison
panel inside the Explorer.

### Optional live data (OpenAQ)

Add to `.streamlit/secrets.toml`:

```toml
OPENAQ_API_KEY = "your-key-here"   # free key from https://openaq.org
```

Home then shows **Fetch live monitoring data**: optionally enter a city
name, and AirAware pulls the freshest real station reading with its own
timestamp. Provider health is visible on the About page. Without a key the
option simply does not appear.

### Optional Gemini configuration

```toml
GEMINI_API_KEY = "your-key-here"
GEMINI_MODEL = "gemini-2.0-flash"   # optional; this is the default
```

With a valid key, **Personal AI Assistant** gains a "Generate AI briefing"
button (25 s timeout, up to 3 attempts with backoff on transient errors).
Every failure mode — missing key, quota, network, malformed response —
falls back silently to the rule-based plan, output is sanitised and
HTML-escaped, and always labelled *AI-generated*. The app runs fully
without a key.

## Suggested demo journey (≈5 minutes)

1. **Home** — hero explains the promise; choose *Explore demonstration
   data* and load a sample city (everything is labelled *sample*, never
   live).
2. **Air Quality Explorer** — the gauge, dominant pollutant,
   completeness meter and plain-language pollutant cards show how one
   bad pollutant drives the CPCB AQI.
3. **Personal AI Assistant** — complete the short profile form, review
   prioritised advice (what / why / when / cost / alternative), then ask
   a follow-up question — the answer is labelled *rule-based* (or *AI*
   when a provider key is configured).
4. **My Daily Air Plan** — tick slots off as you "complete" them; the
   progress bar updates live and resets when the reading changes.
5. **Indoor Air Guardian** — pick a room, compare budget tiers, read the
   sources-worth-controlling guide.
6. **Green Lifestyle Planner** — shortlist swaps with *I'll try this*.
7. **Environmental Impact** — log a trip swap and AC savings; watch
   CO₂e accumulate with honest assumptions.
8. **Family & Community** — work through the household checklist.
9. **About & Data Sources** — methodology, provider status, build stamp
   and limitations, all in one place.

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

225 tests cover AQI breakpoints, interpolation continuity across
breakpoint gaps and category-boundary edge cases (including
fractional/user-supplied AQI), invalid inputs, CSV parsing edge cases
(punctuation-insensitive headers, unit conversion, duplicates, malformed
lines, timestamp handling), live-provider success/failure/staleness paths,
AI provider retries and output sanitisation, recommendation rules,
planner logic and time-slot mapping, the day-ahead planning outlook
(diurnal model, session trend, confidence grading, honesty labelling),
emission calculations, report
generation, HTML-escaping of user data, and Streamlit AppTest smoke tests
that exercise navigation and key journeys across all nine pages.

## Streamlit Community Cloud deployment

1. Push this repository to GitHub (public).
2. In Streamlit Community Cloud: **New app → select repo → main file `app.py`**.
3. Requirements are read from `requirements.txt` automatically.
4. *(Optional)* Add `GEMINI_API_KEY` under **Settings → Secrets** to enable
   the AI briefing; omit it and the rule engine powers everything.

**Python version note:** the project targets **Python 3.14.6**. At the time
of writing, Streamlit Community Cloud's default runtime is an earlier 3.x;
if the platform does not offer 3.14, the app is expected to run on 3.11+
(the code uses only stable, broadly compatible features), but this has not
been verified on the live platform — check the deployed app's runtime before
submission and disclose any mismatch honestly.

## Security & privacy

- File uploads limited to 2 MB / 5,000 rows; parsing is local and
  defensive (malformed lines counted and reported, values range-checked,
  duplicate rows de-duplicated, oversized files rejected before parsing).
- All user-influenced strings rendered as HTML (location names, profile
  fields, KPI values, alert text, AI output) are HTML-escaped — imported
  CSV content cannot inject markup into the UI.
- AI prompts sanitise untrusted inputs (control characters stripped,
  length-capped) and frame them as data, not instructions; a system
  instruction forbids inventing figures; model output is sanitised,
  length-capped and HTML-escaped before display.
- API keys (Gemini, OpenAQ) are read from Streamlit secrets only —
  never hardcoded, never logged, never placed in prompts. Provider and
  AI calls have explicit timeouts; AI retries are bounded with backoff.
- No telemetry. No personal data is persisted anywhere; everything lives
  in the session or in files you explicitly download.

## Limitations

- **Live fetch requires a provider API key** — without `OPENAQ_API_KEY`
  the app relies on manual entry, CSV import or labelled samples (by
  design, nothing is fabricated).
- Recommendations are **rule-based**, not ML-personalised (the optional
  AI layer only re-explains them).
- Indoor guidance is qualitative; a real PM2.5 sensor would enable
  quantitative tracking.
- The 24-hour outlook is a **labelled planning estimate** (diurnal
  model + bounded session trend), not an official hourly forecast; CPCB
  publishes no public forecast feed. A verified live forecast API could
  replace it in future.
- Impact figures are generic estimates; the new mode's own fare is not
  subtracted from "fuel saved".

## Future improvements

- A verified live forecast feed (e.g. Google Air Quality API forecast)
  to replace the labelled planning estimate.
- Additional live providers (CPCB/state-board endpoints where public).
- Multi-day exposure logging and personal AQI history.
- Family/household sharing via local exports.

## Competition submission (PromptWars Virtual — Challenge 06)

- [`docs/competition/narrative.md`](docs/competition/narrative.md) —
  build-in-public narrative for the required blog/LinkedIn post.
- [`docs/competition/demo-script.md`](docs/competition/demo-script.md) —
  2–3 minute demo walkthrough.
- [`docs/competition/checklist.md`](docs/competition/checklist.md) —
  submission checklist with status.
- [`docs/competition/scorecard.md`](docs/competition/scorecard.md) —
  provisional self-assessment (no official rubric is published).
- Screenshots: `shots/final/` (desktop, tablet, mobile, all nine pages).

## License

MIT — see repository for details.
