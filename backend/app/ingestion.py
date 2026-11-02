"""
Ingestion pipeline: load raw docs → redact PII → chunk → embed → store in ChromaDB.
Run with: python -m app.ingestion  (from the backend/ directory)
"""
import json
import os
import sys

import chromadb
from sentence_transformers import SentenceTransformer

from .pii_redaction import redact_text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DOCS_PATH = os.path.join(BASE_DIR, "app", "seed_data", "raw_docs", "documents.json")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "university_docs"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_embed_model = None


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        print("[EMBED] Loading sentence-transformer model (all-MiniLM-L6-v2)…")
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if c]


def get_chroma_collection(reset: bool = False):
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[CHROMA] Dropped existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def ingest(reset: bool = True):
    if not os.path.exists(RAW_DOCS_PATH):
        print(f"[ERROR] documents.json not found at {RAW_DOCS_PATH}")
        print("  Run: python -m app.seed_data.generate_docs  first.")
        sys.exit(1)

    with open(RAW_DOCS_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)

    print(f"[INGEST] Loaded {len(documents)} documents from documents.json")

    model = get_embed_model()
    collection = get_chroma_collection(reset=reset)

    total_chunks = 0
    for doc in documents:
        doc_id = doc["doc_id"]
        access_level = doc["access_level"]
        category = doc["category"]
        title = doc["title"]
        raw_content = doc["content"]

        redacted = redact_text(raw_content)
        chunks = chunk_text(redacted)

        embeddings = model.encode(chunks, show_progress_bar=False).tolist()

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "access_level": access_level,
                "category": category,
                "title": title,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        total_chunks += len(chunks)

    print(f"[INGEST] Done. Stored {total_chunks} chunks across {len(documents)} documents.")
    return total_chunks


if __name__ == "__main__":
    ingest(reset=True)
