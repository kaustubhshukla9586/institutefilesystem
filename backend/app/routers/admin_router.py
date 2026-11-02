import json
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import AuditLog, User
from ..auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


class AuditLogEntry(BaseModel):
    id: int
    user_email: str
    user_role: str
    question: str
    retrieved_doc_ids: list[str]
    answer: str
    timestamp: datetime

    class Config:
        from_attributes = True


class DocumentInfo(BaseModel):
    doc_id: str
    title: str
    access_level: str
    category: str


@router.get("/audit-log", response_model=list[AuditLogEntry])
def get_audit_log(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        try:
            doc_ids = json.loads(log.retrieved_doc_ids)
        except Exception:
            doc_ids = []
        result.append(AuditLogEntry(
            id=log.id,
            user_email=user.email if user else "unknown",
            user_role=log.user_role,
            question=log.question,
            retrieved_doc_ids=doc_ids,
            answer=log.answer,
            timestamp=log.timestamp,
        ))
    return result


@router.get("/documents", response_model=list[DocumentInfo])
def get_documents(_admin: User = Depends(require_admin)):
    docs_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "seed_data", "raw_docs", "documents.json",
    )
    if not os.path.exists(docs_path):
        return []
    with open(docs_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [
        DocumentInfo(
            doc_id=d["doc_id"],
            title=d["title"],
            access_level=d["access_level"],
            category=d["category"],
        )
        for d in raw
    ]
