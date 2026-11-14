# Project Log

## Entry 1 — 2026-11-02
**Prompt used:** M0 frontend foundation for Lacuna: move the old frontend to `frontend_v1`, scaffold a new Vite/React app with tokens, motion system, route skeleton, a mock API that behaves like the LLM-last backend, contract docs, a `/_kit` page and guard-rail scripts.
**Why:** To lay down the design system and a mock API contract so the M1+ screens and the backend can be built in parallel against one agreed interface.
**Aim:** A buildable, lint-clean, tested foundation plus `API_CONTRACT.md`, `SCREENS.md` and `DECISIONS_UI.md` derived from `docs/DECISIONS.md` and `docs/SRS.md`.
**Files affected:** `Log.md` (created). Nothing else.
**Outcome:** Not started. The `Lacuna` folder was empty: no `docs/DECISIONS.md`, no `docs/SRS.md`, no `frontend/`, no `backend/`, and it is not a git repo, so the required inputs and the `git mv` step did not exist. Stopped without guessing at the spec.

## Entry 2 — 2026-11-02
**Prompt used:** Find and vet installable Claude/agent skills for the Lacuna frontend stack across 16 categories, with security review, install commands and a `[SKILLS: ...]` line.
**Why:** To pick a small, safe set of skills before the frontend build prompts run, without repeating skills already installed.
**Aim:** A vetted list (no more than 20 skills) with exact install commands, security verdicts, gaps and rejections.
**Files affected:** `Log.md` (appended this entry).
**Outcome:** Partly done. 11 skills recommended, with sources opened through web fetches. Several categories have no good skill (cursor/micro-interactions, motion a11y, security UI, variable-font typography, Lenis with real reduced-motion handling) and need small custom skills. Last-commit dates were mostly not visible, and bundled scripts were only checked through repo pages, not cloned.

## Entry 3 — 2026-11-14
**Prompt used:** Build the project to match the submitted report (v1 baseline + Lacuna look): spec checklist, backend fixes, 4 features, new frontend, real evaluation, screenshots, report update, README and demo script.
**Why:** The report described behaviour ("expected" results, students-only sign-up, LOCATION redaction, refusals) that the v1 code did not have or had not measured; the submission must be true and demonstrable.
**Aim:** Make every report claim pass a real check, replace expected numbers with measured ones, and ship a usable UI for the viva demo.
**Files affected:** REPORT_SPEC.md, DECISIONS.md, README.md, Log.md, docs/DEMO_SCRIPT.md, report/REPORT_UPDATES.md, screenshots/*.png + _checks.json; backend/app/{auth,database,generation,ingestion,main,models,pii_redaction,retrieval}.py, backend/app/routers/{auth,chat,admin}_router.py, backend/app/seed_data/raw_docs/documents.json, backend/requirements.txt, backend/.env.example, backend/scripts/spec_check.py, backend/tests/{test_access,test_features}.py, backend/eval/{run_eval.py,questions.json,results/*}; frontend/ rebuilt (package.json, vite.config.js, index.html, playwright.config.js, e2e/app.spec.js, public/fonts, src/**; v1 src files deleted).
**Outcome:** Stages 0–6 done on branch `submission`: S-1..S-8 all PASS, 12 backend tests pass, leaks 0, role matrix 57/60 (3 false refusals, 0 leaks), recall@1/3/5 = 0.95/1.0/1.0, Lighthouse mobile 100/100/100, axe 0 serious, 6/6 e2e. Stage 7 partial: report/build.py was not on the machine, so the .docx/PDF were not edited or rebuilt; exact replacement text is in report/REPORT_UPDATES.md.
