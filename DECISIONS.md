# DECISIONS.md — Architecture & Implementation Notes

This file records design decisions and deviations from the original spec.

---

## Python version compatibility

**Decision**: The system's `requirements.txt` uses flexible version pins (`>=`) rather than exact pins for packages that don't support Python 3.14.

**Why**: The development environment runs Python 3.14.5, which is newer than what spaCy 3.7.6, chromadb 0.5.15, and pydantic 2.9.2 (exact) support. spaCy 3.8+ and chromadb 1.x have pre-built Python 3.14 wheels and were installed instead.

**Actual installed versions (key ones)**:
- spaCy: 3.8.16 (spec said 3.7.6 — 3.8 is compatible and better maintained)
- chromadb: 1.5.9 (spec said 0.5.15 — API is backward-compatible for our usage)
- FastAPI: 0.141.1 (spec said 0.115.0)
- groq SDK: 1.7.0 (spec said 0.11.0 — `chat.completions.create` API is unchanged)
- sentence-transformers: 6.0.1 (spec said 3.1.1)

---

## bcrypt / passlib compatibility

**Decision**: Pinned `bcrypt<5.0.0` (installed 4.3.0) because passlib 1.7.4 (last release, unmaintained) attempts to read `bcrypt.__about__.__version__` which was removed in bcrypt 5.x, causing a startup error.

**Effect**: A harmless `(trapped) error reading bcrypt version` warning is printed at startup. Password hashing and verification work correctly.

---

## FastAPI lifespan API

**Decision**: Used `@asynccontextmanager` `lifespan=` parameter instead of `@app.on_event("startup")`.

**Why**: `on_event` was deprecated in FastAPI 0.93+ in favor of the lifespan context manager. Using the modern API avoids deprecation warnings.

---

## spaCy model: en_core_web_lg (not sm)

**Decision**: Presidio's default NLP engine automatically downloads and uses `en_core_web_lg` when first invoked (during `redact_text`). The spec suggested `en_core_web_sm` as a lightweight option, but `en_core_web_lg` provides significantly better PERSON entity recognition, which is the most important entity type for the use case.

**Trade-off**: ~400 MB download the first time. Both `sm` and `lg` are available after initial run.

---

## ChromaDB metadata filter approach

**Decision**: The `retrieve()` function filters at the ChromaDB query level using the `where` parameter with `$eq` or `$in` operators. Unauthorized chunks are never pulled into Python memory.

**Why**: This is the spec requirement and the correct security posture — it's not just a performance optimization.

**Role access map**:
- `student` → `["public"]`
- `faculty` → `["public", "faculty"]`
- `admin` → `["public", "faculty", "admin"]`

---

## Document generation script behavior

**Decision**: `generate_docs.py` generates exactly 65 documents (20 public, 25 faculty, 20 admin) via the Groq API. It adds a 0.3s delay between calls and a 2s pause every 10 calls to stay within Groq free-tier rate limits.

**Why**: The spec said ~60-80 documents. 65 is a reasonable middle ground with clear category distribution.

---

## Ingestion idempotency

**Decision**: `ingestion.py` clears and rebuilds the Chroma collection on every run (`reset=True` by default).

**Why**: Simpler than incremental updates for a demo system. Re-running the script produces a consistent, clean state. Documented in README.

---

## Role selection at signup

**Decision**: Role is a free-form select in the signup form (student/faculty/admin) with no approval workflow.

**Why**: The spec explicitly allows this: "for demo purposes, let role be selectable at signup — no need for an approval workflow."

---

## JWT storage

**Decision**: JWT stored in `localStorage`.

**Why**: The spec explicitly states "localStorage is fine for this project."

---

## Admin `/documents` endpoint

**Decision**: The `/admin/documents` endpoint reads from `raw_docs/documents.json` rather than querying ChromaDB metadata.

**Why**: ChromaDB's metadata API for listing all unique doc_ids is cumbersome. The documents.json is the authoritative source of document metadata, and this endpoint is display-only (not security-critical). The endpoint still requires admin JWT — the data source doesn't affect the access control.

---

## PII redaction entities

**Decision**: Detecting and redacting: PERSON, PHONE_NUMBER, EMAIL_ADDRESS, DATE_TIME, LOCATION, and STUDENT_ID (custom regex recognizer).

**Why**: The spec required the first three plus STUDENT_ID. DATE_TIME and LOCATION were added because they can appear in sensitive records and should also be redacted from the vector store.

---

## Groq model choice

**Decision**: Using `llama-3.1-8b-instant` as specified.

**Why**: Available on Groq's free tier, fast inference, sufficient quality for a RAG demo. No deviation needed.

## Build-to-report decisions (2026-11-14)
- `v1-fallback` exists only as a tag; branch `submission` created from it.
- `report_build/` (build.py, ref.docx, arch.png) is not anywhere under the user profile. Stage 1 uses the S-1..S-8 claims in the brief as the spec; report edits (Stage 7.1-7.6) are blocked until the sources are added to `report/`.
- Existing `backend/.env` uses `JWT_SECRET`; the backend reads `JWT_SECRET` (falling back to `SECRET_KEY`).
- Sign-up always creates `student`; any `role` field is ignored (not rejected) so old clients still work. Min password 8 (422 otherwise). Faculty/admin exist only as seeded demo users.
- Every request re-loads the user from SQLite; the DB role is what filters retrieval, and a token whose role differs from the DB role is rejected (401).
- JWT 60 min, HS256, secret from `JWT_SECRET`; without it the app refuses to start unless `APP_ENV=dev`.
- CORS: only `CORS_ORIGINS` (default http://localhost:5173), methods GET/POST, headers Authorization/Content-Type, no credentials (bearer token, not cookies).
- Login rate limit: in-memory, 5 failures per (IP, email) per 5 min -> 429. Resets on restart; fine for a single-process demo.
- LOCATION re-enabled (report says it is redacted). DATE_TIME stays unredacted on purpose.
- Fictionalised domains/universities by regex find-and-replace (181 replacements) to Thornwick University / thornwick.example. Presidio's e-mail recognizer validates TLDs and missed `.example`, so a plain e-mail pattern recognizer was added (passed per call as an ad-hoc recognizer; registry add with default names silently dropped it).
- New SQLite file `rag.db` (v2 schema with documents table, audit `event`/`result`). The old `app.db` is left untouched.
- Refusal: no chunk within RELEVANCE_THRESHOLD, or the model replies NO_ANSWER -> `refused: true`, empty sources, one fixed category-level message. The same text is used whether a restricted doc exists or not.
- Answers: system prompt injects today's date, demands concise Markdown, forbids HTML and "according to the context"; output is additionally stripped of HTML tags.
- Redaction hardening found by the Stage 5 leak scan: normalise U+202F/U+00A0/U+2011 before analysis (they broke spaCy and phone patterns); +91 / international phone recognizer; honorific+name recognizer ("Dr. K. S. Rao"); roster recognizer = names written next to a roll number anywhere in the seed corpus, plus their bare first names and surnames (>3 letters). Chunk count is now 337 (was 339) because normalisation shortens text.
- The leak scan's name list (spaCy PERSON on raw docs + honorific patterns + roster) partly overlaps the redactor's own detectors, so "0 names" is a consistency check, not an independent audit. Stated as a limitation.
- RELEVANCE_THRESHOLD = 0.50 cosine distance, set once from `python -m eval.run_eval --calibrate`: the largest allowed-case target distance is 0.494; 15/19 refuse cases have best allowed distance > 0.50. The other 4 rely on the model's NO_ANSWER. Not tuned again after seeing the full results.
- Eval answers cached in backend/eval/results/answer_cache.json (key = model + question + chunk ids); calls paced at 2.5 s with 429 exponential backoff.
- Frontend v2 rebuilt in plain JSX (no TypeScript build step) with Tailwind v4 and shadcn/ui-style primitives (cva + tailwind-merge: Button, Input, Select, Label, Card). Radix/shadcn CLI not needed for this scope. Copied from the Lacuna frontend: colour tokens, the three self-hosted variable fonts, and the redaction cut-out (hash-quantised width, lit edge, sr-only label). No animation libraries: CSS transitions/keyframes only, disabled under prefers-reduced-motion.
- Route guards in the UI only hide navigation and show a friendly 403 page; the backend enforces every permission independently (student gets HTTP 403 from /audit-log, /stats, /documents/{id}).
- Landing clearance toggle shows the real model: access level decides which documents can be retrieved; personal data is redacted for every role (only the admin "original" view shows it, and that view is audited).
- Session token is kept in localStorage (60-min JWT, bearer header). Accepted trade-off for a demo; an httpOnly cookie would resist XSS better.
- Playwright suite (frontend/e2e/app.spec.js) both verifies the UI against the real backend and captures report screenshots. It makes ~5 Groq calls per run.
