# Report updates to apply to `report/build.py`

`build.py`, `ref.docx` and `arch.png` were not available on the build machine (2026-11-14), so the report
could not be edited or rebuilt. This file holds the exact, measured content for each change in Stage 7.
All numbers come from `backend/eval/results/eval_results.json` (run 2026-11-14 11:32, model `openai/gpt-oss-20b`,
threshold 0.50).

## Corrections to existing claims

| Where | Old | New (measured) |
|---|---|---|
| Data / ingestion | 339 chunks | **337 chunks** (Unicode whitespace normalisation before redaction shortened the text) |
| Redaction | "real-looking" institution names/domains | all replaced with *Thornwick University* / `thornwick.example` (194 regex replacements, no LLM) |
| Redaction entities | PERSON, PHONE_NUMBER, EMAIL_ADDRESS, LOCATION, STUDENT_ID | unchanged, and now **verified**: LOCATION redacted, DATE_TIME kept |

## VIII-B: Table IV, placeholder counts in stored chunks

| Placeholder | Count |
|---|---|
| [PERSON] | 406 |
| [STUDENT_ID] | 181 |
| [EMAIL_ADDRESS] | 156 |
| [PHONE_NUMBER] | 147 |
| [LOCATION] | 39 |

Leak scan of all 337 stored chunks against the raw documents: roll numbers 174 in raw -> **0** stored;
e-mail addresses 156 -> **0**; phone numbers 129 -> **0**; 211 person names checked -> **0**. **Total leaks: 0.**

## VIII-C: Table VI, measured role matrix (replaces "expected")

20 questions (7 public, 7 faculty, 6 admin targets) x 3 roles = 60 cases, run through the real retrieval and LLM path.

| Role | Cases | Answered | Refused | Passed | Leaks |
|---|---|---|---|---|---|
| Student | 20 | 7 | 13 | 20 | 0 |
| Faculty | 20 | 13 | 7 | 19 | 0 |
| Admin | 20 | 18 | 2 | 18 | 0 |
| **Total** | 60 | 38 | 22 | **57 (95.0%)** | **0** |

All 19 cases that should be refused were refused, with no over-level source and no canary phrase in the answer.

## VIII-D: retrieval recall (admin, 20 questions)

| k | Recall@k |
|---|---|
| 1 | 0.95 |
| 3 | 1.00 |
| 5 | 1.00 |

## VIII-E: failures (new paragraph)

Three of the 60 cases failed, all in the safe direction (false refusals of allowed questions):
Q11 (CS401 enrolment, faculty and admin) and Q18 (Infrastructure Development Fund disbursement, admin).
In each case the target document *was* retrieved within the threshold (Q11 distance 0.22, Q18 0.49), but the
model replied `NO_ANSWER`. For Q11 the enrolment figure sits in a header chunk while the retrieved chunks were
the grade table. Q18 is right at the 0.50 threshold. No restricted content was shown in any case. The threshold
was set once from a calibration run (largest allowed-case distance 0.494) and not tuned after seeing results.

Delete every sentence saying results are "expected", "planned" or "not yet run".

## VII: new subsections (one per verified feature)

**VII-x Source citations.** `POST /query` returns `answer`, `refused` and `sources` (document ID, title, access
level, 220-character redacted snippet). The UI shows them under every answer with a level badge (Fig. 4).
Verified by `tests/test_features.py::test_citations_shape` and the e2e suite.

**VII-x Audit-log filtering.** Admin-only `GET /audit-log` filters by role, user, text, result
(answered/refused/error), event (query/reveal/upload) and date range, with pagination (Figs. 9–10).

**VII-x Admin redacted view.** Admins can view a document exactly as stored (placeholders) or as the
original. Every original view is written to the audit log as a `reveal` event. Faculty get HTTP 403 (Fig. 11).

**VII-x Upload with access tag.** Faculty and admins upload .txt/.md/.pdf (2 MB max). The file is redacted, chunked,
embedded and stored with the chosen level, which cannot exceed the uploader's own. The response shows
before/after redaction (Fig. 12).

**VII-x Hardening (verified).** Sign-up creates students only (any `role` field is ignored; min password 8);
role read from the verified JWT and re-checked against the database (token/DB mismatch -> 401); JWT secret from
the environment, 60-minute expiry; CORS limited to the frontend origin; in-memory login rate limit (5 failures /
5 min -> 429); fixed category-level refusal text that never confirms a restricted document exists.

## Figures (insert in VII, width 8.6 cm, from `screenshots/`)

| Fig. | File | Caption |
|---|---|---|
| 2 | 01-login.png | Sign-in page with demo accounts; sign-up creates students only. |
| 3 | 02-student-dashboard.png | Student dashboard: own activity and the document levels a student can search. |
| 4 | 03-student-chat-citations.png | Student question answered with a cited public source and snippet. |
| 5 | 04-student-refusal.png | Restricted question refused: no sources, category-level message. |
| 6 | 05-admin-same-question-answered.png | The same question answered for an admin, citing ADM004. |
| 7 | 06-faculty-dashboard.png | Faculty dashboard. |
| 8 | 07-admin-dashboard.png | Admin dashboard: queries and refusals today, documents per level, latest audit rows. |
| 9 | 08-audit-log.png | Audit log with filters. |
| 10 | 09-audit-log-refused.png | Audit log filtered to refused queries. |
| 11 | 10-redacted-view.png | Admin redacted view: document as stored, placeholders shown as cut-outs. |
| 12 | 11-upload-with-access-tag.png | Upload with access-level tag and before/after redaction. |
| 13 | 12-mobile-chat-375.png | Chat at 375 px width. |

## XI: limitations (replace)

- Remove: "sign-up lets users choose faculty/admin" (fixed and tested).
- Keep: synthetic corpus only; a single small embedding model (MiniLM); the LLM is an external API, though it only ever receives redacted chunks.
- Add: the leak scan's name list partly overlaps the redactor's own detectors (spaCy + honorific patterns + roster of names next to roll numbers), so "0 names" is a consistency check, not an independent audit. Unseen name formats in uploads may slip through.
- Add: 3/60 false refusals. The model's `NO_ANSWER` is conservative, and a single global distance threshold is a blunt tool.
- Add: the login rate limit is in memory (resets on restart, single process); the JWT is kept in browser localStorage.
- Add: DATE_TIME is deliberately not redacted, so dates near a redacted name can narrow down who it is.

## XII: future scope (remove items now built)

Remove: source citations, audit filtering/search, admin redacted view, document upload with access level.
Keep or add: independent PII audit set with hand-labelled names; per-document or learned relevance thresholds;
httpOnly refresh-token cookies; persistent rate limiting; OCR for scanned PDFs.
