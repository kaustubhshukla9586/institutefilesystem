"""
Ingestion pipeline: raw text -> redact PII -> chunk (500/50) -> embed (MiniLM) -> ChromaDB.
Only redacted text ever reaches ChromaDB. The raw original is kept in SQLite (documents.raw)
for the admin-only, audited "reveal" view.
Run with: python -m app.ingestion   (from backend/)
"""
import json
import os
import sys

import chromadb
from sentence_transformers import SentenceTransformer

from .pii_redaction import redact_with_counts

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DOCS_PATH = os.path.join(BASE_DIR, "app", "seed_data", "raw_docs", "documents.json")
# Second, larger synthetic set (same schema), ingested after the original 65 documents.
EXTRA_DOCS_PATH = os.path.join(BASE_DIR, "app", "seed_data", "raw_docs", "documents_extra.json")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "university_docs"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_embed_model = None
_client = None


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size].strip())
        start += size - overlap
    return [c for c in chunks if c]


def get_chroma_collection(reset: bool = False):
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    if reset:
        try:
            _client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    return _client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def ingest_document(db, doc_id: str, title: str, access_level: str, category: str, raw: str,
                    source: str = "seed", uploaded_by: int | None = None, collection=None) -> dict:
    from .models import Document

    redacted, counts = redact_with_counts(raw)
    chunks = chunk_text(redacted)
    if not chunks:
        raise ValueError("Document has no text after extraction.")
    collection = collection or get_chroma_collection()
    collection.add(
        ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
        embeddings=get_embed_model().encode(chunks, show_progress_bar=False).tolist(),
        documents=chunks,
        metadatas=[{"doc_id": doc_id, "access_level": access_level, "category": category,
                    "title": title, "chunk_index": i} for i in range(len(chunks))],
    )
    db.merge(Document(doc_id=doc_id, title=title, access_level=access_level, category=category, raw=raw,
                      redacted=redacted, chunk_count=len(chunks), source=source, uploaded_by=uploaded_by))
    db.commit()
    return {"doc_id": doc_id, "chunks": len(chunks), "entities": dict(counts), "redacted": redacted}


def load_raw_documents() -> list[dict]:
    """Original seed documents plus the optional extra file."""
    docs = json.load(open(RAW_DOCS_PATH, encoding="utf-8"))
    if os.path.exists(EXTRA_DOCS_PATH):
        docs += json.load(open(EXTRA_DOCS_PATH, encoding="utf-8"))
    return docs


def ingest(reset: bool = True):
    from .database import SessionLocal, engine
    from .models import Base, Document

    if not os.path.exists(RAW_DOCS_PATH):
        print(f"[ERROR] documents.json not found at {RAW_DOCS_PATH}")
        sys.exit(1)
    documents = load_raw_documents()
    Base.metadata.create_all(bind=engine)
    collection = get_chroma_collection(reset=reset)
    db = SessionLocal()
    if reset:
        db.query(Document).delete()
        db.commit()
    total = 0
    for d in documents:
        total += ingest_document(db, d["doc_id"], d["title"], d["access_level"], d["category"], d["content"],
                                 collection=collection)["chunks"]
    db.close()
    print(f"[INGEST] Done. Stored {total} chunks across {len(documents)} documents.")
    return total


if __name__ == "__main__":
    ingest(reset=True)
