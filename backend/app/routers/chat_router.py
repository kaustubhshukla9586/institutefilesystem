import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import AuditLog, User
from ..auth import get_current_user
from ..retrieval import retrieve
from ..generation import generate_answer

router = APIRouter(prefix="/chat", tags=["chat"])


class QueryRequest(BaseModel):
    question: str


class SourceInfo(BaseModel):
    doc_id: str
    title: str
    access_level: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]


@router.post("/query", response_model=QueryResponse)
def query(
    body: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    chunks = retrieve(body.question, current_user.role)
    answer = generate_answer(body.question, chunks)

    sources = []
    seen_doc_ids = set()
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        doc_id = meta.get("doc_id", "")
        if doc_id and doc_id not in seen_doc_ids:
            seen_doc_ids.add(doc_id)
            sources.append(SourceInfo(
                doc_id=doc_id,
                title=meta.get("title", "Unknown"),
                access_level=meta.get("access_level", "unknown"),
            ))

    retrieved_doc_ids = json.dumps(list(seen_doc_ids))
    log = AuditLog(
        user_id=current_user.id,
        user_role=current_user.role,
        question=body.question,
        retrieved_doc_ids=retrieved_doc_ids,
        answer=answer,
    )
    db.add(log)
    db.commit()

    return QueryResponse(answer=answer, sources=sources)
