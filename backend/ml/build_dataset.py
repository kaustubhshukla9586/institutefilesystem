"""Build the access-level dataset: one row per seed document, text redacted with the app's own function.

Run from backend/:  python -m ml.build_dataset
Label-leaking fields (doc_id prefix, level, title) are never used as features; the title is
kept only for reading, and topic_group comes from KMeans on the redacted text.
"""
import json
import os
import re

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from app.pii_redaction import redact_text

SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "app", "seed_data", "raw_docs")
OUT = os.path.join(HERE, "data", "access_dataset.csv")
N_GROUPS = 12

PII_PATTERNS = {
    "roll_number": r"RK3P25KZB\d",
    "email": r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b",
    "phone": r"(?<![\w-])(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?![\w-])",
}


def load_docs() -> list[dict]:
    docs = []
    for name in ("documents.json", "documents_extra.json"):
        path = os.path.join(RAW, name)
        if os.path.exists(path):
            docs += json.load(open(path, encoding="utf-8"))
    return docs


def main():
    docs = load_docs()
    rows = [{"doc_id": d["doc_id"], "title": d["title"], "level": d["access_level"],
             "text_redacted": redact_text(d["content"])} for d in docs]
    df = pd.DataFrame(rows)

    # topic families from the text only (no title, no level)
    tf = TfidfVectorizer(stop_words="english", min_df=2, max_df=0.9, sublinear_tf=True)
    X = tf.fit_transform(df["text_redacted"])
    df["topic_group"] = KMeans(n_clusters=N_GROUPS, random_state=SEED, n_init=10).fit_predict(X)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8")

    print(f"rows: {len(df)}")
    print("class balance:", df["level"].value_counts().to_dict())
    lens = df["text_redacted"].str.split().str.len()
    print(f"words per doc: min {lens.min()}, median {int(lens.median())}, mean {lens.mean():.0f}, max {lens.max()}")
    for g, sub in df.groupby("topic_group"):
        print(f"\ngroup {g} (n={len(sub)}, levels={sub['level'].value_counts().to_dict()})")
        for t in sub["title"].head(8):
            print("   -", t)
        if len(sub) > 8:
            print(f"   ... +{len(sub) - 8} more")
    left = {k: int(df["text_redacted"].str.contains(p, regex=True).sum()) for k, p in PII_PATTERNS.items()}
    print("\nraw PII left in text_redacted (docs):", left, "PASS" if not any(left.values()) else "FAIL")
    print("saved", os.path.normpath(OUT))


if __name__ == "__main__":
    np.random.seed(SEED)
    main()
