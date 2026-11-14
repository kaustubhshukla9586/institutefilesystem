# Evaluation results

Generated 2026-11-14 11:32:57 | model `openai/gpt-oss-20b` | relevance threshold 0.5 (cosine distance) | LLM calls this run 2, cache hits 43

## (a) Leak scan (65 documents, 337 chunks)

| Check | Raw documents | Stored chunks (leaks) |
|---|---|---|
| Roll numbers | 174 | 0 |
| E-mail addresses | 156 | 0 |
| Phone numbers | 129 | 0 |
| Person names (211 checked) | - | 0 |
| **Total leaks** |  | **0** |

| Placeholder | Count in stored chunks |
|---|---|
| PERSON | 406 |
| STUDENT_ID | 181 |
| EMAIL_ADDRESS | 156 |
| PHONE_NUMBER | 147 |
| LOCATION | 39 |

## (b) Role matrix (20 questions x 3 roles = 60 cases)

| Role | Cases | Answered | Refused | Passed | Leaks |
|---|---|---|---|---|---|
| student | 20 | 7 | 13 | 20 | 0 |
| faculty | 20 | 13 | 7 | 19 | 0 |
| admin | 20 | 18 | 2 | 18 | 0 |
| **All** | 60 | 38 | 22 | **57/60** | 0 |

Pass rate: 95.0%

### Failing cases

| Q | Role | Expected | Why it failed |
|---|---|---|---|
| Q11 | faculty | ALLOW | refused |
| Q11 | admin | ALLOW | refused |
| Q18 | admin | ALLOW | refused |

## (c) Retrieval recall

| k | Recall@k (admin, 20 questions) |
|---|---|
| 1 | 0.95 |
| 3 | 1.0 |
| 5 | 1.0 |
