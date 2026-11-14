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
