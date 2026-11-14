"""Access-control tests. Run from backend/:  python -m pytest -q tests
No LLM calls: the generator is stubbed."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.retrieval import ROLE_ACCESS_MAP, retrieve
from app.routers import chat_router

ORDER = {"public": 0, "faculty": 1, "admin": 2}
CAP = {"student": 0, "faculty": 1, "admin": 2}
PROBES = ["salary", "disciplinary hearing", "exam timetable", "research grant", "grievance", "fee waiver",
          "hostel", "board minutes", "performance appraisal", "scholarship", "medical leave", "budget"]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def token(client, email):
    return {"Authorization": "Bearer " + client.post("/auth/login", json={"email": email, "password": "demo1234"}).json()["access_token"]}


@pytest.mark.parametrize("role", ["student", "faculty", "admin"])
def test_retrieval_never_returns_chunks_above_role(role):
    for q in PROBES:
        for c in retrieve(q, role, top_k=10):
            assert ORDER[c["metadata"]["access_level"]] <= CAP[role], (role, q, c["chunk_id"])


@pytest.mark.parametrize("email,role", [("student@demo.com", "student"), ("faculty@demo.com", "faculty")])
def test_query_endpoint_sources_within_role(client, monkeypatch, email, role):
    monkeypatch.setattr(chat_router, "generate_answer", lambda q, ch: "stub answer")
    h = token(client, email)
    for q in PROBES:
        r = client.post("/query", json={"question": q}, headers=h)
        assert r.status_code == 200
        for s in r.json()["sources"]:
            assert s["access_level"] in ROLE_ACCESS_MAP[role]


def test_signup_cannot_create_admin(client):
    em = f"t-{uuid.uuid4().hex[:6]}@thornwick.example"
    r = client.post("/auth/signup", json={"email": em, "password": "longenough1", "role": "admin"})
    assert r.status_code == 201 and r.json()["role"] == "student"
    assert client.post("/auth/signup", json={"email": "y" + em, "password": "short"}).status_code == 422


def test_student_forbidden_on_admin_routes(client):
    h = token(client, "student@demo.com")
    for path in ["/audit-log", "/stats", "/documents/PUB001?view=raw"]:
        assert client.get(path, headers=h).status_code == 403, path


def test_tampered_or_missing_token_rejected(client):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401
