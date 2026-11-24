# Provisional Scorecard — Challenge 06

> **No official Challenge-06 rubric is published.** promptwars.in
> describes evaluation as expert review of *functionality and narrative
> depth*; the building phase says "Google Antigravity **or other AI
> tools**". This scorecard is an **internal self-assessment**, not a
> prediction and not an official PromptWars result.

Weights (proposed, per rescue audit):

| Dimension | Weight |
|---|---|
| Problem alignment & real-world usefulness | 15 |
| Functional completeness & reliability | 15 |
| AI integration & intelligence | 15 |
| Technical architecture & code quality | 15 |
| UI/UX & accessibility | 15 |
| Innovation & differentiation | 10 |
| Data accuracy, security & trust | 5 |
| Demonstration & submission quality | 10 |
| **Total** | **100** |

## Scores — initial (commit 3a2c72f) → final (this release)

| Dimension | Initial | Final | Δ | Key evidence / change |
|---|---|---|---|---|
| Problem alignment & usefulness | 13/15 | 14/15 | +1 | All four brief elements present and working (routines, indoor, alternatives, impact). Verified live-rendered pages. Remaining −1: no verified live data without keys. |
| Functional completeness & reliability | 12/15 | 14/15 | +2 | 232 tests pass (was 225). Fixed: server-timezone bug in plan "now" marker and outlook trend; naive-timestamp crash path in alerts; dead-end "Custom / other location"; mobile tab overflow. −1: live app currently behind Streamlit auth (owner action). |
| AI integration & intelligence | 11/15 | 12/15 | +1 | Gemini provider verified in code + fallback tests; follow-up Q&A labelled AI vs rule-based; sanitised prompts. −3: no live Gemini key available to verify end-to-end; assistant still requires manual profile form before chatting. |
| Technical architecture & code quality | 13/15 | 14/15 | +1 | Clean module split, provider abstractions, honest provenance, no circular imports, hardened CSV. +1 for tzutil module fixing a real deployment defect. −1: pages.py is a 2100-line monolith (acceptable but at the limit). |
| UI/UX & accessibility | 11/15 | 13/15 | +2 | Playwright audit 9 pages × 3 viewports: 0 console errors, 0 page overflow, 1 h1/page, 0 missing alts. Fixed mobile overflow on Indoor tabs. −2: no formal axe/Lighthouse audit; heading-level skips remain (Streamlit-generated markup). |
| Innovation & differentiation | 8/10 | 8/10 | 0 | Measurement→decision→plan→impact chain with labelled planning outlook is genuinely differentiated; unchanged this cycle. |
| Data accuracy, security & trust | 5/5 | 5/5 | 0 | CPCB interpolation verified by tests; provenance everywhere; secrets gitignored; prompt-injection hygiene; no fabricated data. |
| Demonstration & submission quality | 7/10 | 9/10 | +2 | Fixed broken live URL in demo script; scorecard made evidence-based; checklist updated. −1: live preview blocked by Streamlit auth; Gemini unverified live; submission itself is manual. |
| **Total** | **80/100** | **89/100** | **+9** | Internal estimate only. |

## Highest-impact remaining gaps (honest)

1. **Public live preview** — the deployed app redirects anonymous users
   to Streamlit auth. This is the single biggest submission risk and is
   an owner-level Streamlit Cloud setting (see checklist).
2. **Live Gemini verification** — add `GEMINI_API_KEY` (+ optionally
   `OPENAQ_API_KEY`) in Streamlit Cloud secrets and re-test the
   assistant end-to-end.
3. **Accessibility evidence** — an axe/Lighthouse pass would convert
   manual review into artefact-backed evidence.

## Disclosed weaknesses (unchanged, by design)

- Forecast is a labelled planning estimate, not an official hourly
  forecast (CPCB publishes none publicly).
- Recommendations are rule-based, not ML-personalised.
- Built with Devin (Cognition), not Google Antigravity — the official
  page allows "Google Antigravity **or other AI tools**"; disclose
  tooling honestly in the build-in-public post.
