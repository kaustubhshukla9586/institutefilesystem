import io
import json
import math
import re
import uuid
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..auth import ACCESS_LEVELS, ROLE_LEVEL, allowed_levels, get_current_user, require_admin, require_staff
from ..database import get_db
from ..ingestion import ingest_document
from ..models import AuditLog, Document, User

router = APIRouter(tags=["admin"])

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_EXT = {".txt", ".md", ".pdf"}


def _row(log: AuditLog, email: str) -> dict:
    try:
        ids = json.loads(log.retrieved_doc_ids or "[]")
    except ValueError:
        ids = []
    return {"id": log.id, "user_email": email, "user_role": log.user_role, "event": log.event,
            "question": log.question, "sources": ids, "answer": log.answer, "result": log.result,
            "timestamp": log.timestamp.isoformat() + "Z"}


def _today_start() -> datetime:
    return datetime.combine(datetime.utcnow().date(), time.min)


@router.get("/audit-log")
def audit_log(
    role: str | None = None, user: str | None = None, q: str | None = None,
    result: str | None = None, event: str | None = None,
    from_: date | None = Query(None, alias="from"), to: date | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db), _admin: User = Depends(require_admin),
):
    qry = db.query(AuditLog, User.email).join(User, User.id == AuditLog.user_id)
    if role:
        qry = qry.filter(AuditLog.user_role == role)
    if user:
        qry = qry.filter(User.email.ilike(f"%{user}%"))
    if q:
        qry = qry.filter(or_(AuditLog.question.ilike(f"%{q}%"), AuditLog.answer.ilike(f"%{q}%")))
    if result:
        qry = qry.filter(AuditLog.result == result)
    if event:
        qry = qry.filter(AuditLog.event == event)
    if from_:
        qry = qry.filter(AuditLog.timestamp >= datetime.combine(from_, time.min))
    if to:
        qry = qry.filter(AuditLog.timestamp < datetime.combine(to + timedelta(days=1), time.min))
    total = qry.count()
    rows = qry.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_row(l, e) for l, e in rows], "total": total, "page": page,
            "pages": max(1, math.ceil(total / page_size))}


def _docs_per_level(db: Session, levels: list[str]) -> dict:
    counts = dict(db.query(Document.access_level, func.count()).group_by(Document.access_level).all())
    return {lv: counts.get(lv, 0) for lv in levels}


@router.get("/stats")
def stats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    today = db.query(AuditLog).filter(AuditLog.event == "query", AuditLog.timestamp >= _today_start())
    latest = db.query(AuditLog, User.email).join(User, User.id == AuditLog.user_id) \
        .order_by(AuditLog.id.desc()).limit(6).all()
    return {
        "queries_today": today.count(),
        "refusals_today": today.filter(AuditLog.result == "refused").count(),
        "reveals_total": db.query(AuditLog).filter(AuditLog.event == "reveal").count(),
        "documents_per_level": _docs_per_level(db, ACCESS_LEVELS),
        "users_per_role": dict(db.query(User.role, func.count()).group_by(User.role).all()),
        "latest_audit": [_row(l, e) for l, e in latest],
    }


@router.get("/my-stats")
def my_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    mine = db.query(AuditLog).filter(AuditLog.user_id == user.id, AuditLog.event == "query")
    recent = mine.order_by(AuditLog.id.desc()).limit(5).all()
    return {
        "role": user.role,
        "queries_today": mine.filter(AuditLog.timestamp >= _today_start()).count(),
        "queries_total": mine.count(),
        "refusals_total": mine.filter(AuditLog.result == "refused").count(),
        "documents_per_level": _docs_per_level(db, allowed_levels(user.role)),
        "recent_questions": [{"question": r.question, "result": r.result,
                              "timestamp": r.timestamp.isoformat() + "Z"} for r in recent],
    }


@router.get("/documents")
def documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Document).filter(Document.access_level.in_(allowed_levels(user.role))) \
        .order_by(Document.access_level, Document.doc_id).all()
    return [{"doc_id": d.doc_id, "title": d.title, "access_level": d.access_level, "category": d.category,
             "chunks": d.chunk_count, "source": d.source} for d in rows]


@router.get("/documents/{doc_id}")
def document_view(doc_id: str, view: str = Query("redacted", pattern="^(redacted|raw)$"),
                  db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Admin-only. `redacted` = exactly what is stored and embedded; `raw` = the original.
    Every raw view is written to the audit log as a `reveal` event."""
    d = db.get(Document, doc_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if view == "raw":
        db.add(AuditLog(user_id=admin.id, user_role=admin.role, event="reveal",
                        question=f"Viewed original of {d.doc_id} ({d.title})",
                        retrieved_doc_ids=json.dumps([d.doc_id]), answer="", result="ok"))
        db.commit()
    placeholders = {}
    for p in re.findall(r"\[([A-Z_]+)\]", d.redacted):
        placeholders[p] = placeholders.get(p, 0) + 1
    return {"doc_id": d.doc_id, "title": d.title, "access_level": d.access_level, "category": d.category,
            "view": view, "text": d.raw if view == "raw" else d.redacted, "placeholders": placeholders}


def _extract(name: str, data: bytes) -> str:
    ext = name[name.rfind("."):].lower() if "." in name else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=415, detail="Only .txt, .md and .pdf files are supported.")
    if ext == ".pdf":
        from pypdf import PdfReader
        try:
            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        except Exception:
            raise HTTPException(status_code=422, detail="That PDF could not be read. Is it password-protected or damaged?")
        if not text.strip():
            raise HTTPException(status_code=422, detail="That PDF has no selectable text (it may be a scan).")
        return text
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="The file is not valid UTF-8 text.")


@router.post("/documents/upload", status_code=201)
async def upload(file: UploadFile = File(...), access_level: str = Form(...), title: str = Form(""),
                 category: str = Form("uploaded"), db: Session = Depends(get_db),
                 user: User = Depends(require_staff)):
    if access_level not in ACCESS_LEVELS:
        raise HTTPException(status_code=400, detail="Access level must be public, faculty or admin.")
    if ACCESS_LEVELS.index(access_level) > ROLE_LEVEL[user.role]:
        raise HTTPException(status_code=403, detail="You can't tag a document above your own access level.")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 2 MB.")
    raw = _extract(file.filename or "", data)
    doc_id = f"UPL-{uuid.uuid4().hex[:8].upper()}"
    title = (title or (file.filename or "Untitled")).strip()[:200]
    try:
        res = ingest_document(db, doc_id, title, access_level, category.strip()[:60] or "uploaded", raw,
                              source="upload", uploaded_by=user.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.add(AuditLog(user_id=user.id, user_role=user.role, event="upload",
                    question=f"Uploaded {doc_id} '{title}' as {access_level}",
                    retrieved_doc_ids=json.dumps([doc_id]), answer="", result="ok"))
    db.commit()
    return {"doc_id": doc_id, "title": title, "access_level": access_level, "chunks": res["chunks"],
            "entities_redacted": res["entities"], "before": raw[:1200], "after": res["redacted"][:1200]}
