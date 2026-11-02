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
