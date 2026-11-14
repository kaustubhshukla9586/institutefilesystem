import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..generation import NO_ANSWER, generate_answer
from ..models import AuditLog, User
from ..retrieval import relevant, retrieve

router = APIRouter(tags=["chat"])

REFUSAL_TEXT = ("I can't find anything you're cleared to see about that. "
                "If you think you need access, ask an administrator.")


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class SourceInfo(BaseModel):
    doc_id: str
    title: str
    access_level: str
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    refused: bool
    sources: list[SourceInfo]


def _snippet(text: str, n: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


def answer_question(question: str, role: str, generate=generate_answer) -> dict:
    """Retrieve under the role's filter, drop low-relevance chunks, ask the LLM.
    Refuses (no sources, category-level text) when nothing relevant is allowed, or when the
    model says the allowed documents do not answer it. Never says whether a restricted doc exists."""
    chunks = relevant(retrieve(question, role))
    if not chunks:
        return {"answer": REFUSAL_TEXT, "refused": True, "sources": []}
    answer = generate(question, chunks)
    if not answer or answer.strip().strip(".").upper() == NO_ANSWER:
        return {"answer": REFUSAL_TEXT, "refused": True, "sources": []}
    sources, seen = [], set()
    for c in chunks:
        m = c["metadata"]
        if m["doc_id"] in seen:
            continue
        seen.add(m["doc_id"])
        sources.append({"doc_id": m["doc_id"], "title": m.get("title", "Untitled"),
                        "access_level": m["access_level"], "snippet": _snippet(c["text"])})
    return {"answer": answer, "refused": False, "sources": sources}


@router.post("/query", response_model=QueryResponse)
def query(body: QueryRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = body.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        out = answer_question(q, user.role, generate=generate_answer)
        result = "refused" if out["refused"] else "answered"
    except Exception as e:  # LLM outage / quota: log it, tell the user plainly
        db.add(AuditLog(user_id=user.id, user_role=user.role, event="query", question=q,
                        retrieved_doc_ids="[]", answer=f"error: {type(e).__name__}", result="error"))
        db.commit()
        raise HTTPException(status_code=503, detail="The answer service is unavailable right now. Please try again in a minute.")
    db.add(AuditLog(user_id=user.id, user_role=user.role, event="query", question=q,
                    retrieved_doc_ids=json.dumps([s["doc_id"] for s in out["sources"]]),
                    answer=out["answer"], result=result))
    db.commit()
    return out
