from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")  # student | faculty | admin
    created_at = Column(DateTime, default=_now)

    audit_logs = relationship("AuditLog", back_populates="user")


class Document(Base):
    """Registry of every ingested document. `raw` is the original text (admin-only reveal);
    `redacted` is exactly what was chunked and embedded."""
    __tablename__ = "documents"

    doc_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    access_level = Column(String, nullable=False, index=True)  # public | faculty | admin
    category = Column(String, nullable=False, default="general")
    raw = Column(Text, nullable=False)
    redacted = Column(Text, nullable=False)
    chunk_count = Column(Integer, nullable=False, default=0)
    source = Column(String, nullable=False, default="seed")  # seed | upload
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_role = Column(String, nullable=False)
    event = Column(String, nullable=False, default="query", index=True)  # query | reveal | upload
    question = Column(Text, nullable=False)  # the question, or a description for reveal/upload
    retrieved_doc_ids = Column(Text, nullable=False, default="[]")  # JSON list
    answer = Column(Text, nullable=False, default="")
    result = Column(String, nullable=False, default="answered", index=True)  # answered | refused | error | ok
    timestamp = Column(DateTime, default=_now, index=True)

    user = relationship("User", back_populates="audit_logs")
