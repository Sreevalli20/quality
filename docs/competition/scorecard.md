# Provisional Scorecard — Challenge 06

> **No official Challenge-06 rubric is published.** promptwars.in
describes evaluation as expert review of *functionality and narrative
depth*; platform code-assessment signals are listed generically
(quality, security, efficiency, testing, accessibility, alignment,
Google services). This scorecard is a **self-assessment**, not a
prediction — no scores are invented.

## Criteria, evidence and gaps

| Criterion | Evidence in repo | Remaining gap |
|---|---|---|
| Problem alignment | Winter-smog routines (daily plan), indoor hacks (Guardian), sustainable alternatives (Lifestyle), impact explanation (Impact + CO₂e log) — all four brief elements covered | — |
| Innovation | Measurement→decision journey; labelled 24h planning outlook; "AI explains, code computes" honesty model | Forecast is an estimate, not a live feed (documented) |
| AI integration | Gemini provider: retries, timeouts, sanitised prompts, labelled output, graceful fallback; conversational follow-ups incl. forecast/impact questions | Gemini unverified live without API key; recommend adding `GEMINI_API_KEY` secret before judging |
| Technical quality | 225 tests; CPCB interpolation continuity; hardened CSV; provider failover; build stamp | — |
| Data reliability | Provenance on every reading; staleness flags; OpenAQ provider (key-gated); no fabricated data | No live forecast source; OpenAQ unverified without key |
| User experience | 9 redesigned pages; journey Home→plan→impact; empty/loading/error states; AppTest coverage | Polish is good; further differentiation possible |
| Visual quality | Custom design system, SVG scene art, AQI ring/gauge, Plotly charts, mobile-verified screenshots | — |
| Accessibility | Semantic headings, labelled controls, contrast-checked buttons; no formal axe audit run | Consider an axe/Lighthouse pass for evidence |
| Real-world usefulness | Works with zero keys via manual/CSV/sample; actionable per-budget indoor advice | Sample data is illustrative (labelled) |
| Demonstration quality | demo-script.md + shots/final/* (desktop/tablet/mobile) | Record/ rehearse the live demo |
| Submission completeness | checklist.md — all artifacts ready | Platform submission is manual (user action) |

## Three highest-impact remaining improvements

1. **Activate Gemini on the live deployment** — add `GEMINI_API_KEY`
   to Streamlit Cloud secrets so evaluators see real AI responses, not
   only the labelled fallback. (External action; code is ready.)
2. **Live forecast feed** — integrate a verified forecast API (e.g.
   Google Maps Platform Air Quality API forecast, or CPCB where
   available) behind the same provider abstraction, keeping the
   estimate as fallback. This is the single biggest credibility gap
   versus competitors with paid Google services.
3. **Accessibility evidence** — run an automated axe/Lighthouse
   accessibility audit and fix findings; "accessibility" is a named
   platform scoring signal and currently rests on manual review only.

## Honest weaknesses (disclosed, not hidden)

- Forecasting is a labelled planning estimate, not an official forecast.
- Live AQI requires `OPENAQ_API_KEY`; without it the app relies on
  manual entry/CSV/samples.
- Recommendations are rule-based, not ML-personalised.
- The build tool was Devin (Cognition), not Google Antigravity as the
  challenge narrative suggests — disclose tooling honestly in the
  build-in-public post.
