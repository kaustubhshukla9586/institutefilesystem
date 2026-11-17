"""Access-level suggestion at upload time. Suggests only; access control never reads this.

The model is loaded lazily on first use. If the file is missing or broken, ModelUnavailable is
raised and the caller returns a clean error; the app and the upload endpoint keep working.
"""
import os
import threading

import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "access_classifier.joblib")
CONFIDENT_AT = 0.60
MIN_WORDS = 5

_bundle = None
_lock = threading.Lock()


class ModelUnavailable(RuntimeError):
    pass


def _load():
    global _bundle
    if _bundle is None:
        with _lock:
            if _bundle is None:
                if not os.path.exists(MODEL_PATH):
                    raise ModelUnavailable("The suggestion model file is missing. "
                                           "Run: python -m ml.train_access_classifier")
                import joblib
                try:
                    _bundle = joblib.load(MODEL_PATH)
                except Exception as e:  # corrupt / version mismatch
                    raise ModelUnavailable(f"The suggestion model could not be loaded ({type(e).__name__}).")
    return _bundle


def reset():
    """Forget the loaded model (used after the file is replaced)."""
    global _bundle
    _bundle = None


def predict(text: str) -> dict:
    from app.pii_redaction import redact_text

    b = _load()
    classes = b["classes"]  # public, faculty, admin (index == restrictiveness)
    red = redact_text(text or "")
    pipe = b["pipeline"]
    proba_raw = pipe.predict_proba([red])[0]
    order = [list(b["model_classes"]).index(c) for c in classes]
    proba = np.asarray(proba_raw)[order]
    proba = proba / proba.sum()

    top2 = np.argsort(-proba)[:2]
    confident = bool(proba[top2[0]] >= CONFIDENT_AT) and len(red.split()) >= MIN_WORDS
    idx = int(top2[0]) if confident else int(max(top2))  # not sure -> more restrictive of the top two

    x = pipe.named_steps["tfidf"].transform([red]).toarray()[0]
    contrib = x * b["term_weights"][idx]
    vocab = pipe.named_steps["tfidf"].get_feature_names_out()
    top = [str(vocab[i]) for i in np.argsort(-contrib)[:6] if contrib[i] > 0]

    return {"suggested_level": classes[idx],
            "probabilities": {c: round(float(p), 4) for c, p in zip(classes, proba)},
            "confident": confident, "top_terms": top, "model_version": b["version"]}
