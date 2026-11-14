"""Report-spec checks S-1..S-8. Run from backend/:  python -m scripts.spec_check
Prints PASS/FAIL per check. Uses the real ChromaDB store and FastAPI app (TestClient).
Makes at most 2 Groq calls (S-6/S-7)."""
import collections
import inspect
import json
import os
import re
import sys
import uuid

os.environ.setdefault("APP_ENV", "dev")
from fastapi.testclient import TestClient  # noqa: E402

from app import ingestion, pii_redaction, retrieval  # noqa: E402
from app.main import app  # noqa: E402

RESULTS = []


def check(cid, ok, detail):
    RESULTS.append((cid, "PASS" if ok else "FAIL", detail))
    print(f"{cid}: {'PASS' if ok else 'FAIL'} - {detail}")


def all_chunks():
    col = ingestion.get_chroma_collection()
    got = col.get(include=["documents", "metadatas"])
    return got["documents"], got["metadatas"]


def main():
    docs = json.load(open(ingestion.RAW_DOCS_PATH, encoding="utf-8"))
    by_level = collections.Counter(d["access_level"] for d in docs)
    texts, metas = all_chunks()
    check("S-1", len(docs) == 65 and by_level == {"public": 20, "faculty": 25, "admin": 20}
          and len(texts) == 337 and (ingestion.CHUNK_SIZE, ingestion.CHUNK_OVERLAP) == (500, 50),
          f"docs={len(docs)} {dict(by_level)} chunks={len(texts)} chunking={ingestion.CHUNK_SIZE}/{ingestion.CHUNK_OVERLAP}")

    ents = set(pii_redaction._ENTITIES)
    want = {"PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "STUDENT_ID"}
    roll = re.compile(r"\bRK3P25KZB\d{2,4}\b")
    rolls = sum(len(roll.findall(t)) for t in texts)
    sample = pii_redaction.redact_text("Meet on 12 March 2025 in Mumbai, India.")
    date_kept = "12 March 2025" in sample
    loc_redacted = "Mumbai" not in sample
    check("S-2", want <= ents and "DATE_TIME" not in ents and rolls == 0 and date_kept and loc_redacted,
          f"entities={sorted(ents)} roll_numbers_in_chunks={rolls} date_kept={date_kept} location_redacted={loc_redacted}")

    m = retrieval.ROLE_ACCESS_MAP
    check("S-3", m == {"student": ["public"], "faculty": ["public", "faculty"], "admin": ["public", "faculty", "admin"]},
          f"map={m}")

    src = inspect.getsource(retrieval)
    order = {"public": 0, "faculty": 1, "admin": 2}
    viol = 0
    for role in ("student", "faculty", "admin"):
        for q in ["salary details", "disciplinary case", "exam timetable", "research grant budget", "student grievance"]:
            for c in retrieval.retrieve(q, role, top_k=8):
                if order[c["metadata"]["access_level"]] > order[m[role][-1]]:
                    viol += 1
    check("S-4", "where=" in src and viol == 0, f"where-clause in retrieval={('where=' in src)} over-level chunks={viol}")

    client = TestClient(app)
    client.__enter__()  # run lifespan (seeds demo users)
    from app import auth
    em = f"speccheck-{uuid.uuid4().hex[:6]}@thornwick.example"
    r = client.post("/auth/signup", json={"email": em, "password": "Passw0rd!x", "role": "admin"})
    role_got = r.json().get("role") if r.status_code < 300 else None
    short = client.post("/auth/signup", json={"email": "x" + em, "password": "abc"}).status_code
    check("S-5", "bcrypt" in auth.pwd_context.schemes() and role_got in (None, "student") and short >= 400,
          f"signup role=admin -> status {r.status_code} role={role_got}; 3-char password -> {short}")
    _cleanup(em)

    def login(e):
        return client.post("/auth/login", json={"email": e, "password": "demo1234"}).json()["access_token"]

    st = {"Authorization": f"Bearer {login('student@demo.com')}"}
    ad = {"Authorization": f"Bearer {login('admin@demo.com')}"}
    qpath = "/query"
    alog = "/audit-log"
    restricted_q = "What disciplinary action was taken in the confidential misconduct cases?"
    resp = client.post(qpath, json={"question": restricted_q}, headers=st)
    body = resp.json()
    student_audit = client.get(alog, headers=st).status_code
    a = client.get(alog, headers=ad).json()
    if isinstance(a, dict) and "items" not in a:
        print("audit-log response:", a, "query response:", resp.status_code, body)
    rows = a.get("items", []) if isinstance(a, dict) else a
    last = rows[0] if rows else {}
    has_fields = all(k in last for k in ("user_email", "user_role", "question", "timestamp")) and \
        ("sources" in last or "retrieved_doc_ids" in last)
    check("S-6", last.get("question") == restricted_q and has_fields and student_audit == 403,
          f"query logged={last.get('question') == restricted_q} fields={has_fields} student GET audit -> {student_audit}")

    srcs = body.get("sources", [])
    over = [s for s in srcs if s.get("access_level") != "public"]
    check("S-7", body.get("refused") is True and not srcs and not over,
          f"refused={body.get('refused')} sources={len(srcs)} over-level={len(over)} answer={body.get('answer', '')[:80]!r}")

    counts = collections.Counter(p for t in texts for p in re.findall(r"\[([A-Z_]+)\]", t))
    eval_ok = os.path.exists(os.path.join("eval", "run_eval.py")) and os.path.exists(os.path.join("eval", "questions.json"))
    if eval_ok:
        qs = json.load(open(os.path.join("eval", "questions.json"), encoding="utf-8"))
        lv = collections.Counter(q["target_level"] for q in qs)
        eval_ok = len(qs) == 20 and lv == {"public": 7, "faculty": 7, "admin": 6}
    check("S-8", eval_ok, f"placeholder counts={dict(counts)} eval protocol present(20, 7/7/6)={eval_ok}")

    print("\n| ID | Status | Detail |\n|---|---|---|")
    for cid, s, d in RESULTS:
        print(f"| {cid} | {s} | {d} |")


def _cleanup(email):
    from app.database import SessionLocal
    from app.models import User
    db = SessionLocal()
    db.query(User).filter(User.email.like("%speccheck-%")).delete(synchronize_session=False)
    db.commit()
    db.close()


if __name__ == "__main__":
    sys.exit(main())
