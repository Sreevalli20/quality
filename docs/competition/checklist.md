# Submission Checklist — PromptWars Virtual, Challenge 06

Deadline: **November 29, 2026** (verify on the official challenge page;
the public site lists Challenge 06 as "On-going" without a per-challenge
date as of 2026-11-24).

## Verified official requirements (promptwars.in)

The 14-day cycle requires **two submission components**:

1. **Technical** — project code (public repo) + a **live preview** of the
   application.
2. **Narrative** — a "Build-in-Public" post (technical blog and/or
   LinkedIn) explaining the development journey.

Evaluation is by expert review of **functionality and narrative
depth**; code-assessment signals mentioned for the platform include
code quality, security, efficiency, testing, accessibility, problem
alignment and Google-services usage. **No Challenge-06-specific rubric
is published** — see `scorecard.md` for a provisional self-assessment.

## Checklist

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1 | Public GitHub repo, `main` branch | ✅ | github.com/Sreevalli20/quality |
| 2 | Working live preview URL | ⛔ blocked | quality-gyfoxhaaazq8o5appxggja.streamlit.app currently redirects anonymous visitors to Streamlit auth — owner must set app visibility to **Public** in share.streamlit.io (App → Settings → Sharing). Code-side verified via local run + build stamp. |
| 3 | Challenge-aligned features (smog routines, indoor hacks, sustainable alternatives, impact explanation) | ✅ | 9 modules; see README feature table |
| 4 | GenAI integration, honestly disclosed | ✅ | Gemini provider (stdlib urllib, retries, sanitisation) + labelled rule-based fallback; works without key |
| 5 | Google services usage | ⚠️ partial | Gemini API implemented and documented; requires `GEMINI_API_KEY` secret to activate. Add key in Streamlit Cloud secrets before submission to demonstrate live AI. |
| 6 | Forward-looking planning | ✅ | 24-hour planning outlook (labelled estimate, confidence-graded) |
| 7 | Test suite | ✅ | 232 pytest tests passing (incl. tzutil coverage); Streamlit AppTest page journeys |
| 8 | Responsive UI | ✅ | Playwright screenshots at 1440/768/390 in `shots/final/` |
| 9 | README (problem, features, methodology, install, deploy, limitations) | ✅ | README.md |
| 10 | Build-in-public narrative | ✅ draft | docs/competition/narrative.md — post to blog + LinkedIn |
| 11 | Demo script | ✅ | docs/competition/demo-script.md |
| 12 | Screenshots package | ✅ | shots/final/*.png |
| 13 | Secrets check (no keys committed) | ✅ | `.streamlit/secrets.toml` gitignored; verify before push |
| 14 | Submission itself on platform | ⬜ manual | User must submit repo link + live URL + post on promptwars.in before Nov 29 |

## Before submitting — do these

1. **Make the app public (release blocker).** In
   https://share.streamlit.io/ sign in → open the app → **Settings →
   Sharing** → set visibility to **Public**, then confirm the URL loads
   logged-out. Verified 2026-11-24: anonymous requests currently get a
   `303` redirect to Streamlit auth.
2. Add `GEMINI_API_KEY` in Streamlit Cloud → app → Settings → Secrets so
   the live demo shows real AI responses (optional but strengthens the
   GenAI requirement). Add `OPENAQ_API_KEY` too if you want the
   "Fetch live monitoring data" path demonstrated.
3. Open the live URL → About & Data Sources → Build information; record
   the build ID/commit and confirm it matches the final pushed SHA.
4. Post the narrative (blog + LinkedIn) and submit repo + live link +
   post link on the competition platform.
