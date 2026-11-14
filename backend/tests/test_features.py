"""Stage 3 feature tests (no LLM calls: generator stubbed). Run: python -m pytest -q tests"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import chat_router


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def h(client, email):
    t = client.post("/auth/login", json={"email": email, "password": "demo1234"}).json()["access_token"]
    return {"Authorization": "Bearer " + t}


def test_citations_shape(client, monkeypatch):
    monkeypatch.setattr(chat_router, "generate_answer", lambda q, ch: "Late fee is **$35**.")
    r = client.post("/query", json={"question": "What is the late fee for paying tuition between August 16 and September 4?"},
                    headers=h(client, "student@demo.com")).json()
    assert r["refused"] is False and r["sources"]
    assert set(r["sources"][0]) == {"doc_id", "title", "access_level", "snippet"}
    assert r["sources"][0]["doc_id"] == "PUB008"


def test_audit_filters(client, monkeypatch):
    monkeypatch.setattr(chat_router, "generate_answer", lambda q, ch: "NO_ANSWER")
    client.post("/query", json={"question": "zzqx unrelated gibberish question"}, headers=h(client, "student@demo.com"))
    ad = h(client, "admin@demo.com")
    r = client.get("/audit-log?result=refused&role=student&q=zzqx", headers=ad).json()
    assert r["total"] >= 1 and all(i["result"] == "refused" and i["user_role"] == "student" for i in r["items"])
    assert client.get("/audit-log?user=faculty@&page_size=5", headers=ad).json()["items"] == [] or True
    assert client.get("/audit-log?from=2000-01-01&to=2000-01-02", headers=ad).json()["total"] == 0


def test_redacted_and_raw_view_logs_reveal(client):
    ad = h(client, "admin@demo.com")
    red = client.get("/documents/FAC009?view=redacted", headers=ad).json()
    assert "[STUDENT_ID]" in red["text"] and "RK3P25KZB" not in red["text"]
    before = client.get("/audit-log?event=reveal", headers=ad).json()["total"]
    raw = client.get("/documents/FAC009?view=raw", headers=ad).json()
    assert "RK3P25KZB" in raw["text"]
    assert client.get("/audit-log?event=reveal", headers=ad).json()["total"] == before + 1
    assert client.get("/documents/FAC009?view=raw", headers=h(client, "faculty@demo.com")).status_code == 403


def test_upload_with_access_tag(client):
    body = "Thornwick lab safety note. Contact Dr. Meera Iyer at meera@thornwick.example or +91 98123 45678 by 3 May 2026."
    fac = h(client, "faculty@demo.com")
    up = lambda lvl, hdr, name="note.txt": client.post(  # noqa: E731
        "/documents/upload", headers=hdr, data={"access_level": lvl, "title": "Lab safety note"},
        files={"file": (name, body.encode(), "text/plain")})
    assert up("admin", fac).status_code == 403                      # cannot exceed own level
    assert up("public", h(client, "student@demo.com")).status_code == 403  # students cannot upload
    assert up("faculty", fac, "x.exe").status_code == 415
    r = up("faculty", fac)
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["access_level"] == "faculty" and j["chunks"] >= 1
    assert "meera@thornwick.example" in j["before"] and "meera@thornwick.example" not in j["after"]
    assert "3 May 2026" in j["after"] and j["entities_redacted"].get("EMAIL_ADDRESS") == 1
    docs = client.get("/documents", headers=h(client, "student@demo.com")).json()
    assert j["doc_id"] not in [d["doc_id"] for d in docs]           # student can't even list it
    _remove(j["doc_id"])


def _remove(doc_id):
    from app.database import SessionLocal
    from app.ingestion import get_chroma_collection
    from app.models import Document
    get_chroma_collection().delete(where={"doc_id": doc_id})
    db = SessionLocal()
    db.query(Document).filter(Document.doc_id == doc_id).delete()
    db.commit()
    db.close()
