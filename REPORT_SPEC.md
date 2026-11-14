# Report spec checklist

Source: claims S-1..S-8 as listed in the build brief. `report/build.py` was **not found** on this machine (see DECISIONS.md), so the full report text could not be scanned.
Checks are automated in `backend/scripts/spec_check.py` (`python -m scripts.spec_check` from `backend/`).

| ID | Section | Claim | How to check | Status (Stage 1) |
|---|---|---|---|---|
| S-1 | Data / ingestion | 65 docs (20 public / 25 faculty / 20 admin), 339 chunks, chunking 500/50 | count documents.json + Chroma collection; read constants | PASS |
| S-2 | Redaction | PERSON, PHONE_NUMBER, EMAIL_ADDRESS, LOCATION, STUDENT_ID redacted; DATE_TIME kept; 0 roll numbers stored | entity list; regex scan of all chunks; probe sentence with a date + city | FAIL (LOCATION not in entity list) |
| S-3 | Access model | public < faculty < admin; student=public, faculty=+faculty, admin=all | ROLE_ACCESS_MAP | PASS |
| S-4 | Retrieval | role from verified JWT; filter inside the Chroma query | `where=` in query; 15 probes x 3 roles, count over-level chunks | PASS (0 over-level) |
| S-5 | Auth | JWT + bcrypt; faculty/admin not self-selectable at sign-up | sign-up with role=admin; 3-char password | FAIL (admin created, short password accepted) |
| S-6 | Audit | every query logged (user, role, question, sources, time); admin-only read | query then read log as admin; student gets 403 | PASS |
| S-7 | Generation | Groq answers; restricted question -> clear refusal, no restricted source | student asks admin-only question | FAIL (no `refused` flag, 4 unrelated public sources returned) |
| S-8 | Evaluation | Table IV placeholder counts; 20 questions 7/7/6, 60 cases | count placeholders; eval/questions.json | FAIL (no eval harness). Counts: PERSON 356, EMAIL 160, PHONE 61, STUDENT_ID 168 |
