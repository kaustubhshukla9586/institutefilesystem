"""Train and compare access-level classifiers (public / faculty / admin).

Run from backend/:  python -m ml.train_access_classifier
Writes: ml/models/access_classifier.joblib, ../report/ml_results.json, ../report/figures/ml_*.png
Every number in the report comes from ml_results.json.
"""
import json
import os
import platform
import random
import sys
import time
from datetime import date

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import (GridSearchCV, GroupKFold, RepeatedStratifiedKFold, StratifiedKFold,
                                     train_test_split)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

SEED = 42
VERSION = "access-clf-1.0"
CLASSES = ["public", "faculty", "admin"]  # index == restrictiveness
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "access_dataset.csv")
MODEL_OUT = os.path.join(HERE, "models", "access_classifier.joblib")
REPORT = os.path.normpath(os.path.join(HERE, "..", "..", "report"))
FIG = os.path.join(REPORT, "figures")

# Spurious-feature stop list (see DECISIONS.md): fictional institution name, redaction placeholders,
# and sign-off boilerplate. These say nothing about how sensitive a document is.
SPURIOUS = {"thornwick", "university", "example", "person", "email_address", "phone_number", "location",
            "student_id", "https", "www", "issued", "notice", "office",
            # template sign-offs and field labels left next to redaction placeholders (run-1 inspection)
            "recorded", "follow", "tracked", "actions", "prepared", "copy", "copies", "circulated", "roll",
            "mail", "phone", "contact", "chair", "liaison", "representative"}
TOKEN_PATTERN = r"(?u)\b[a-zA-Z][a-zA-Z]+\b"  # letters only: drops numbers, dates and IDs
STOP_BASE = sorted(ENGLISH_STOP_WORDS)
STOP_FULL = sorted(ENGLISH_STOP_WORDS | SPURIOUS)


class KeywordRule(BaseEstimator, ClassifierMixin):
    """Hand-written baseline: admin words -> admin, faculty words -> faculty, else public."""
    ADMIN = ("disciplinary", "salary", "salaries", "budget", "confidential", "audit", "vendor", "procurement",
             "appraisal", "defaulter", "board of management", "incident")
    FACULTY = ("faculty", "invigilation", "marks", "moderation", "grade", "department meeting", "timetable",
               "allocation", "attendance")

    def fit(self, X, y):
        self.classes_ = np.array(CLASSES)
        return self

    def predict(self, X):
        out = []
        for t in X:
            t = t.lower()
            out.append("admin" if any(w in t for w in self.ADMIN)
                       else "faculty" if any(w in t for w in self.FACULTY) else "public")
        return np.array(out)


def tfidf(stop=STOP_FULL):
    return TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2, max_df=0.9,
                           stop_words=stop, lowercase=True, token_pattern=TOKEN_PATTERN)


def models():
    mf = [1000, 3000, None]
    return {
        "Majority baseline": (Pipeline([("tfidf", tfidf()), ("clf", DummyClassifier(strategy="most_frequent"))]), None),
        "Keyword rule": (KeywordRule(), None),
        "Naive Bayes": (Pipeline([("tfidf", tfidf()), ("clf", MultinomialNB())]),
                        {"tfidf__max_features": mf, "clf__alpha": [0.01, 0.1, 0.5, 1.0]}),
        "Logistic Regression": (Pipeline([("tfidf", tfidf()),
                                          ("clf", LogisticRegression(max_iter=5000, random_state=SEED))]),
                                {"tfidf__max_features": mf, "clf__C": [0.1, 1, 10, 100]}),
        "Linear SVM": (Pipeline([("tfidf", tfidf()),
                                 ("clf", CalibratedClassifierCV(LinearSVC(random_state=SEED), cv=3))]),
                       {"tfidf__max_features": mf, "clf__estimator__C": [0.01, 0.1, 1, 10]}),
        "Random Forest": (Pipeline([("tfidf", tfidf()),
                                    ("clf", RandomForestClassifier(random_state=SEED, n_jobs=1))]),
                          {"tfidf__max_features": mf, "clf__n_estimators": [200, 500],
                           "clf__max_depth": [None, 20]}),
    }


def tuned(est, grid):
    if grid is None:
        return clone(est)
    return GridSearchCV(clone(est), grid, scoring="f1_macro",
                        cv=StratifiedKFold(3, shuffle=True, random_state=SEED), n_jobs=-1)


def severe(y_true, y_pred):
    t = np.array([CLASSES.index(v) for v in y_true])
    p = np.array([CLASSES.index(v) for v in y_pred])
    return float(np.mean(p < t)), float(np.mean(p > t))


def run_cv(est, grid, X, y, splits, groups=None):
    """Outer loop with tuning inside each training fold (nested). Returns per-fold scores."""
    acc, f1, sev, over, params = [], [], [], [], []
    oof = np.empty(len(y), dtype=object)  # out-of-fold predictions (last repeat wins for repeated CV)
    for tr, te in splits.split(X, y, groups):
        m = tuned(est, grid).fit(X[tr], y[tr])
        p = m.predict(X[te])
        oof[te] = p
        acc.append(accuracy_score(y[te], p))
        f1.append(f1_score(y[te], p, average="macro", labels=CLASSES, zero_division=0))
        s, o = severe(y[te], p)
        sev.append(s)
        over.append(o)
        if hasattr(m, "best_params_"):
            params.append({k: v for k, v in m.best_params_.items()})
    r = lambda a: [round(float(v), 4) for v in a]
    return {"accuracy_mean": round(float(np.mean(acc)), 4), "accuracy_std": round(float(np.std(acc)), 4),
            "macro_f1_mean": round(float(np.mean(f1)), 4), "macro_f1_std": round(float(np.std(f1)), 4),
            "severe_error_rate_mean": round(float(np.mean(sev)), 4),
            "over_restrictive_rate_mean": round(float(np.mean(over)), 4),
            # pooled = metrics on all out-of-fold predictions together; needed for grouped CV, where a
            # fold can hold only one or two classes and per-fold macro-F1 then counts absent classes as 0
            "pooled_accuracy": round(float(accuracy_score(y, oof)), 4),
            "pooled_macro_f1": round(float(f1_score(y, oof, average="macro", labels=CLASSES)), 4),
            "pooled_severe_error_rate": round(severe(y, oof)[0], 4),
            "pooled_over_restrictive_rate": round(severe(y, oof)[1], 4),
            "fold_accuracy": r(acc), "fold_macro_f1": r(f1), "fold_best_params": params}


def term_weights(pipe):
    """Per-class weight per TF-IDF term, used for the 'Why?' line and the top-terms figure."""
    clf = pipe.named_steps["clf"]
    if isinstance(clf, LogisticRegression):
        return clf.coef_
    if isinstance(clf, CalibratedClassifierCV):
        return np.mean([c.estimator.coef_ for c in clf.calibrated_classifiers_], axis=0)
    if isinstance(clf, MultinomialNB):
        lp = clf.feature_log_prob_
        return lp - lp.mean(axis=0, keepdims=True)
    if isinstance(clf, RandomForestClassifier):  # no sign; same importance for every class
        return np.tile(clf.feature_importances_, (len(clf.classes_), 1))
    return None


def reorder(w, classes):
    idx = [list(classes).index(c) for c in CLASSES]
    return w[idx]


def top_terms(pipe, n=20):
    vocab = np.array(pipe.named_steps["tfidf"].get_feature_names_out())
    w = reorder(term_weights(pipe), pipe.named_steps["clf"].classes_)
    return {c: vocab[np.argsort(-w[i])[:n]].tolist() for i, c in enumerate(CLASSES)}


def main():
    random.seed(SEED)
    np.random.seed(SEED)
    df = pd.read_csv(DATA)
    X = df["text_redacted"].fillna("").to_numpy()
    y = df["level"].to_numpy()
    groups = df["topic_group"].to_numpy()
    n_groups = len(set(groups))
    A_split = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    B_split = GroupKFold(n_splits=6)

    res = {"version": VERSION, "date": date.today().isoformat(), "seed": SEED,
           "n_documents": int(len(df)), "class_counts": df["level"].value_counts().to_dict(),
           "n_topic_groups": n_groups, "classes": CLASSES,
           "features": {"tfidf": "word 1-2 grams, sublinear_tf, min_df=2, max_df=0.9, lowercase, "
                                 "English stop words + spurious-term list",
                        "spurious_stop_terms": sorted(SPURIOUS),
                        "excluded_inputs": ["doc_id prefix", "access level field", "title"]},
           "protocol": {"A": "RepeatedStratifiedKFold(5 splits x 3 repeats), tuning nested inside each fold",
                        "B": f"GroupKFold(6) by topic_group ({n_groups} KMeans topic families), tuning nested",
                        "C": "stratified 80/20 split made once; tuned on the 80% only; evaluated once",
                        "D": "chosen pipeline with shuffled labels, stratified 5-fold x 3",
                        "E": "severe = predicted lower than true level; over-restrictive = predicted higher",
                        "inner_tuning": "GridSearchCV, StratifiedKFold(3), scoring macro-F1"},
           "library_versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                                "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__},
           "models": {}}

    # ---- A and B for every model ----
    for name, (est, grid) in models().items():
        t0 = time.perf_counter()
        a = run_cv(est, grid, X, y, A_split)
        b = run_cv(est, grid, X, y, B_split, groups)
        res["models"][name] = {"grid": {k: [str(v) for v in vs] for k, vs in (grid or {}).items()},
                               "A_stratified_cv": a, "B_grouped_cv": b,
                               "cv_seconds": round(time.perf_counter() - t0, 1)}
        print(f"{name:20s} A acc {a['accuracy_mean']:.3f}±{a['accuracy_std']:.3f} F1 {a['macro_f1_mean']:.3f} | "
              f"B pooled acc {b['pooled_accuracy']:.3f} F1 {b['pooled_macro_f1']:.3f} "
              f"(fold-mean F1 {b['macro_f1_mean']:.3f}) severe {b['pooled_severe_error_rate']:.3f}")

    # ---- choose: best grouped (pooled) macro-F1; prefer linear if within 1 point ----
    ml_names = ["Naive Bayes", "Logistic Regression", "Linear SVM", "Random Forest"]
    bF = {n: res["models"][n]["B_grouped_cv"]["pooled_macro_f1"] for n in ml_names}
    best = max(ml_names, key=lambda n: (bF[n], -ml_names.index(n)))
    chosen = best
    linear = [n for n in ("Logistic Regression", "Linear SVM") if bF[best] - bF[n] <= 0.01]
    if best not in ("Logistic Regression", "Linear SVM") and linear:
        chosen = max(linear, key=lambda n: bF[n])
    res["choice"] = {"best_by_grouped_f1": best, "chosen": chosen,
                     "rule": "best grouped-CV macro-F1; a linear model within 1 point is preferred (explainable)"}
    print("best by grouped F1:", best, "-> chosen:", chosen)
    est, grid = models()[chosen]

    # ---- C: held-out test ----
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    t0 = time.perf_counter()
    m = tuned(est, grid).fit(Xtr, ytr)
    train_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    p = m.predict(Xte)
    pred_ms = (time.perf_counter() - t0) / len(Xte) * 1000
    cm = confusion_matrix(yte, p, labels=CLASSES)
    s, o = severe(yte, p)
    res["C_held_out"] = {"model": chosen, "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
                         "best_params": {k: str(v) for k, v in m.best_params_.items()},
                         "accuracy": round(accuracy_score(yte, p), 4),
                         "macro_f1": round(f1_score(yte, p, average="macro"), 4),
                         "per_class": {c: {k: round(v, 4) for k, v in d.items()} for c, d in
                                       classification_report(yte, p, labels=CLASSES, output_dict=True,
                                                             zero_division=0).items() if c in CLASSES},
                         "confusion_matrix": {"labels": CLASSES, "rows_true_cols_pred": cm.tolist()},
                         "severe_error_rate": round(s, 4), "over_restrictive_rate": round(o, 4),
                         "train_seconds_incl_grid": round(train_s, 2), "predict_ms_per_doc": round(pred_ms, 3)}
    # held-out for the other ML models too (same split), for the table
    for n in ml_names:
        if n == chosen:
            continue
        e2, g2 = models()[n]
        p2 = tuned(e2, g2).fit(Xtr, ytr).predict(Xte)
        res["models"][n]["C_held_out"] = {"accuracy": round(accuracy_score(yte, p2), 4),
                                          "macro_f1": round(f1_score(yte, p2, average="macro"), 4),
                                          "severe_error_rate": round(severe(yte, p2)[0], 4)}
    for n in ("Majority baseline", "Keyword rule"):
        p2 = models()[n][0].fit(Xtr, ytr).predict(Xte)
        res["models"][n]["C_held_out"] = {"accuracy": round(accuracy_score(yte, p2), 4),
                                          "macro_f1": round(f1_score(yte, p2, average="macro", labels=CLASSES,
                                                                     zero_division=0), 4),
                                          "severe_error_rate": round(severe(yte, p2)[0], 4)}
    res["models"][chosen]["C_held_out"] = {k: res["C_held_out"][k] for k in ("accuracy", "macro_f1",
                                                                             "severe_error_rate")}

    # ---- final model on all documents ----
    final = tuned(est, grid).fit(X, y)
    pipe = final.best_estimator_
    res["final_params"] = {k: str(v) for k, v in final.best_params_.items()}

    # ---- D: shuffled labels with the chosen pipeline (fixed params) ----
    rng = np.random.RandomState(SEED)
    ys = rng.permutation(y)
    accs = [accuracy_score(ys[te], clone(pipe).fit(X[tr], ys[tr]).predict(X[te]))
            for tr, te in A_split.split(X, ys)]
    res["D_shuffled_labels"] = {"accuracy_mean": round(float(np.mean(accs)), 4),
                                "accuracy_std": round(float(np.std(accs)), 4),
                                "majority_share": round(float(pd.Series(y).value_counts(normalize=True).max()), 4)}
    print("shuffled-label accuracy:", res["D_shuffled_labels"])

    # ---- spurious-feature check: effect of the extra stop list on the chosen model (grouped CV) ----
    base_pipe = clone(pipe).set_params(tfidf__stop_words=STOP_BASE)
    nostop = run_cv(base_pipe, None, X, y, B_split, groups)
    res["spurious_check"] = {"top20_without_extra_stop": top_terms(clone(base_pipe).fit(X, y)),
                             "B_pooled_macro_f1_without_extra_stop": nostop["pooled_macro_f1"],
                             "B_pooled_accuracy_without_extra_stop": nostop["pooled_accuracy"],
                             "B_pooled_macro_f1_with_extra_stop":
                                 run_cv(clone(pipe), None, X, y, B_split, groups)["pooled_macro_f1"],
                             "note": "fixed final params, grouped CV; compare with chosen model's B scores"}
    res["top_terms"] = top_terms(pipe)
    for c, ts in res["top_terms"].items():
        print(f"top {c}: {', '.join(ts)}")

    # ---- save model ----
    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    w = reorder(term_weights(pipe), pipe.named_steps["clf"].classes_)
    joblib.dump({"pipeline": pipe, "classes": CLASSES, "model_classes": list(pipe.named_steps["clf"].classes_),
                 "term_weights": w.astype(np.float32), "version": VERSION, "model_name": chosen,
                 "trained_on": int(len(df)), "date": res["date"]}, MODEL_OUT, compress=3)
    res["model_file"] = {"path": "backend/ml/models/access_classifier.joblib",
                         "bytes": os.path.getsize(MODEL_OUT)}

    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(REPORT, "ml_results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    figures(res)
    print("model bytes:", res["model_file"]["bytes"])


def figures(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False})
    W = 3.39  # 8.6 cm

    names = list(res["models"])
    short = {"Majority baseline": "Majority", "Keyword rule": "Keyword", "Naive Bayes": "NB",
             "Logistic Regression": "LogReg", "Linear SVM": "SVM", "Random Forest": "RF"}
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.2), sharey=True)
    x = np.arange(len(names))
    for ax, key, bkey, ttl in ((axes[0], "accuracy_mean", "pooled_accuracy", "Accuracy"),
                               (axes[1], "macro_f1_mean", "pooled_macro_f1", "Macro-F1")):
        a = [res["models"][n]["A_stratified_cv"][key] for n in names]
        b = [res["models"][n]["B_grouped_cv"][bkey] for n in names]
        ax.bar(x - 0.2, a, 0.4, label="A: stratified CV", color="#4c72b0")
        ax.bar(x + 0.2, b, 0.4, label="B: grouped CV", color="#dd8452")
        ax.set_xticks(x, [short[n] for n in names], rotation=45, ha="right")
        ax.set_title(ttl)
        ax.set_ylim(0, 1)
    axes[0].legend(frameon=False, fontsize=6, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "ml_model_comparison.png"), dpi=300)
    plt.close(fig)

    cm = np.array(res["C_held_out"]["confusion_matrix"]["rows_true_cols_pred"])
    fig, ax = plt.subplots(figsize=(2.4, 2.1))
    ax.imshow(cm, cmap="Blues")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xticks(range(3), CLASSES)
    ax.set_yticks(range(3), CLASSES)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"{res['C_held_out']['model']}, held-out (n={res['C_held_out']['n_test']})")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "ml_confusion_matrix.png"), dpi=300)
    plt.close(fig)

    pipe = joblib.load(MODEL_OUT)
    w, vocab = pipe["term_weights"], pipe["pipeline"].named_steps["tfidf"].get_feature_names_out()
    fig, axes = plt.subplots(3, 1, figsize=(W, 4.2))
    for i, (ax, c) in enumerate(zip(axes, CLASSES)):
        idx = np.argsort(-w[i])[:8][::-1]
        ax.barh(range(8), w[i][idx], color="#4c72b0")
        ax.set_yticks(range(8), vocab[idx], fontsize=6)
        ax.set_title(f"{c} (top 8 terms, SVM weight)", fontsize=7, loc="left")
        ax.tick_params(axis="x", labelsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "ml_top_terms.png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
