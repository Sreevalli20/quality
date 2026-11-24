# Build-in-Public Narrative — PromptWars Virtual, Challenge 06

> Urban Air Quality Assistant — a GenAI-powered assistant helping families
> and communities navigate winter smog: low-emission routines, indoor air
> hacks, sustainable alternatives, explaining the impact of choices.

*Paste-ready for the required blog post / LinkedIn update. Keep claims
factual — every feature listed here exists in the repository.*

---

## Why this problem

Every winter the same advice circulates in Indian cities: "the air is
bad, stay indoors." It is true — and nearly useless. It does not tell a
parent whether the 7 AM school run or the 6 PM walk home is worse. It
does not tell a family whether a bedroom purifier is worth buying, or
what swapping one car trip for a metro ride actually changes — for their
lungs this week and for the neighbourhood's air next winter.

AirAware AI was built to turn an AQI number into **decisions**.

## What makes it different

Most air-quality dashboards stop at the measurement. AirAware AI runs
the full chain:

**Measurement → Understanding → Personalised advice → Daily plan →
Action completion → Environmental impact → Personal report.**

- **Understanding without a chemistry degree.** Pollutant cards show
  sub-indices in plain language; the dominant pollutant is always named.
- **A 24-hour planning outlook.** Likely AQI *categories* per time
  window — best outdoor window, worst window, ventilation guidance —
  built from a diurnal model plus a bounded trend from readings taken in
  the same session. It is labelled a planning estimate everywhere it
  appears, with a confidence grade. It never fabricates hourly readings.
- **Advice that knows your life.** A short profile (commute, household,
  outdoor activity, budget, priorities) re-ranks every recommendation —
  each with *what, why, when, cost, and an alternative*.
- **A day plan you can tick off.** Slot-by-slot guidance tied to the
  active reading, with persistent progress.
- **Impact you can see.** Trip-swap and AC calculators produce honest
  CO₂e estimates, and every logged action accumulates into a personal
  report you can download.

## How the AI is used — honestly

The challenge asks for a GenAI-powered assistant. AirAware AI uses a
**pluggable provider architecture**:

- A deterministic Python rule engine is the foundation — it powers
  every recommendation, answer and plan, always, with no key required.
- When `GEMINI_API_KEY` is configured in Streamlit secrets, Google's
  Gemini can (a) rewrite the daily briefing in natural language and
  (b) answer follow-up questions inside a sanitised, bounded prompt.
- **Every AI response is labelled** ("AI · gemini" vs "rule-based").
  If the provider fails, times out or is unconfigured, the app silently
  degrades to the rule engine — AI is an enhancement layer, never a
  dependency.
- Prompt inputs are sanitised (control characters stripped, length
  capped, untrusted content framed as data), outputs are sanitised and
  HTML-escaped, retries are bounded with exponential backoff, and API
  keys live only in Streamlit secrets.

This split — *AI explains, code computes* — means no number a user sees
was invented by a language model.

## How families benefit

- **Parents:** know which windows are safest for kids' outdoor time,
  with a child-friendly explainer they can share.
- **Commuters:** closed-window/recirculate guidance, mode-swap
  estimates with real CO₂e numbers.
- **Budget-conscious households:** indoor improvements tiered from free
  (ventilation timing, source control) to paid (purifiers), each with
  honest limitations.
- **Everyone:** works fully offline with manual entry, CSV import or
  labelled samples — no account, no tracking, no key required.

## What was technically challenging

- **Honest forecasting.** CPCB publishes no public hourly forecast.
  Rather than fake one, the outlook models AQI *categories* per window
  from a diurnal climatology, adjusts for the dominant pollutant
  (ozone peaks in afternoon sun, not morning traffic), and blends in a
  least-squares trend from session readings — all capped and labelled.
- **AQI correctness.** Piecewise-linear interpolation across CPCB
  breakpoint gaps (the bands are integer ranges with 1-unit holes), so
  AQI 30.0 → 50 and 30.5 → 50.5 instead of jumping a full band.
- **Untrusted data everywhere.** CSV imports, location strings and AI
  prompts are all adversarial surfaces; everything user-influenced is
  validated, escaped and framed as data, never instructions.
- **Session-state correctness.** Plan completion survives reruns and
  is keyed to the measurement fingerprint, so a new reading never
  inherits an old plan's checkmarks.

## What was learned

- The most useful feature is not the index — it is the *next decision*.
- Honesty is a feature: labelled estimates, confidence grades and
  provenance build more trust than confident-sounding numbers.
- A rule engine plus optional AI beats AI-or-nothing: the product works
  on day one and gets better when a key is added.

---

*Built with Python, Streamlit, pandas and Plotly; optional Google Gemini
via a stdlib-only provider. 225 automated tests. Live demo:
https://quality-gyfoxhaaazq8o5appxggja.streamlit.app/
Repo: https://github.com/Sreevalli20/quality*
