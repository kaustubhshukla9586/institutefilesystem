"""
Retrieval: top-k chunks for a query, filtered by access level INSIDE the ChromaDB query
(the `where` clause), so restricted chunks never reach the application layer.
"""
import os

from .auth import allowed_levels
from .ingestion import get_chroma_collection, get_embed_model

ROLE_ACCESS_MAP = {r: allowed_levels(r) for r in ("student", "faculty", "admin")}

# Cosine distance above which a chunk is treated as "not about this question".
# Calibrated on the Stage 5 evaluation questions; see DECISIONS.md.
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.50"))


def where_for_role(role: str) -> dict:
    levels = ROLE_ACCESS_MAP.get(role, ["public"])
    return {"access_level": {"$in": levels}}


def retrieve(query: str, user_role: str, top_k: int = 5) -> list[dict]:
    emb = get_embed_model().encode([query])[0].tolist()
    res = get_chroma_collection().query(
        query_embeddings=[emb], n_results=top_k, where=where_for_role(user_role),
        include=["documents", "metadatas", "distances"],
    )
    out = []
    for i, cid in enumerate(res["ids"][0] if res and res["ids"] else []):
        out.append({"chunk_id": cid, "text": res["documents"][0][i], "metadata": res["metadatas"][0][i],
                    "distance": res["distances"][0][i]})
    return out


def relevant(chunks: list[dict], threshold: float | None = None) -> list[dict]:
    t = RELEVANCE_THRESHOLD if threshold is None else threshold
    return [c for c in chunks if c["distance"] <= t]
