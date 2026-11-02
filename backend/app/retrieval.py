"""
Retrieval: given a query and user role, return top-k relevant chunks
filtered by access_level at the ChromaDB query level.
"""
import os
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

from .ingestion import get_embed_model, CHROMA_DIR, COLLECTION_NAME

# Role → allowed access levels (inclusive upward)
ROLE_ACCESS_MAP = {
    "student": ["public"],
    "faculty": ["public", "faculty"],
    "admin":   ["public", "faculty", "admin"],
}


def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_collection(COLLECTION_NAME)


def retrieve(query: str, user_role: str, top_k: int = 5) -> list[dict]:
    allowed_levels = ROLE_ACCESS_MAP.get(user_role, ["public"])

    model = get_embed_model()
    query_embedding = model.encode([query])[0].tolist()

    collection = _get_collection()

    # Build a ChromaDB $in filter — never pulls restricted chunks into app layer
    if len(allowed_levels) == 1:
        where_filter = {"access_level": {"$eq": allowed_levels[0]}}
    else:
        where_filter = {"access_level": {"$in": allowed_levels}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if results and results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            chunks.append({
                "chunk_id": chunk_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

    return chunks
