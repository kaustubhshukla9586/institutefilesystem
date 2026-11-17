# Report material: trained access-level classifier

Ready-to-paste text for a new report section. Every number comes from `report/ml_results.json` (seed 42, scikit-learn 1.9.0, generated 2026-11-17). Figures are in `report/figures/`.

---

## X. A trained model that suggests a document's access level

### X.1 Problem

When a faculty member or administrator uploads a document, they must choose its access level (public, faculty or admin). If they pick a level that is too low, students may later retrieve confidential text. We trained a small supervised text classifier that reads the document and **suggests** a level, which the upload form pre-selects. The person uploading always makes the final choice. The model is not part of access control: the role still comes from the verified token, the server still refuses any level above the uploader's own, and retrieval still filters by level inside the Chroma query.

### X.2 Dataset

- **Documents:** the 165 synthetic seed documents (50 public, 60 faculty, 55 admin), one row per document. Median length is 77 words (range 8 to 400).
- **Redaction:** each document is passed through the same redaction function the app uses (`app.pii_redaction.redact_text`) before training, so the model sees the same kind of text it will see at upload time. After redaction, no roll number, e-mail address or phone number pattern remained.
- **Features:** TF-IDF on the redacted text: word unigrams and bigrams, sublinear term frequency, `min_df = 2`, `max_df = 0.9`, lowercase, letters-only tokens (no numbers or IDs), English stop words plus a list of spurious terms (Section X.6). `max_features` was tuned from {1000, 3000, all}.
- **Excluded to avoid label leakage:** the document ID prefix (PUB/FAC/ADM), the level field, and the title.
- **Topic groups:** KMeans (k = 12, seed 42) on TF-IDF of the redacted text gives 12 topic families (9 to 19 documents each). Several families are almost entirely one level, for example all-admin vendor contracts and audits, or all-faculty meeting minutes and allocations. These families are used for the grouped test below.

### X.3 Models compared

All models are scikit-learn `Pipeline`s, so TF-IDF is fitted inside each training fold only.

| Model | Settings searched (GridSearchCV, 3-fold, macro-F1) |
|---|---|
| Majority-class baseline | always predicts the most common class |
| Keyword rule (hand-written) | admin words (e.g. *disciplinary, salary, budget, confidential, audit*) give admin; faculty words (e.g. *faculty, invigilation, marks, moderation*) give faculty; otherwise public |
| Multinomial Naive Bayes | alpha ∈ {0.01, 0.1, 0.5, 1.0} |
| Logistic Regression | C ∈ {0.1, 1, 10, 100} |
| Linear SVM (LinearSVC + sigmoid calibration, 3-fold) | C ∈ {0.01, 0.1, 1, 10} |
| Random Forest | n_estimators ∈ {200, 500}, max_depth ∈ {None, 20} |

### X.4 Evaluation protocol

- **A. Stratified 5-fold cross-validation, repeated 3 times** (15 folds). Tuning is nested inside each training fold.
- **B. Grouped cross-validation** (`GroupKFold`, 6 folds by topic group). Every test fold contains only topic families the model never saw during training. Because a fold can contain just one or two classes, per-fold macro-F1 scores the missing classes as zero. We therefore report B on the pooled out-of-fold predictions (all 165 documents predicted once).
- **C. Held-out test set:** a stratified 80/20 split made once (132 training, 33 test documents). Tuning used only the 80%, and the test set was evaluated once.
- **D. Shuffled-label sanity check:** the chosen pipeline retrained on randomly permuted labels (stratified 5-fold × 3).
- **E. Severe-error rate:** the share of documents predicted at a **lower** level than their true level (for example, admin predicted as public). These are the dangerous errors. Predicting a higher level than the truth ("over-restrictive") is reported separately; it is inconvenient but safe.

### X.5 Results

**Table X.1: model comparison** (A: mean ± s.d. over 15 folds; B: pooled over 6 grouped folds; C: 33 held-out documents.)

| Model | A accuracy | A macro-F1 | B accuracy | B macro-F1 | C accuracy | C macro-F1 | Severe errors (B) | Severe errors (C) |
|---|---|---|---|---|---|---|---|---|
| Majority baseline | 0.364 ± 0.000 | 0.178 ± 0.000 | 0.061 | 0.059 | 0.364 | 0.178 | 0.382 | 0.333 |
| Keyword rule | 0.679 ± 0.058 | 0.669 ± 0.060 | 0.679 | 0.671 | 0.727 | 0.720 | 0.115 | 0.091 |
| Naive Bayes | 0.885 ± 0.032 | 0.885 ± 0.033 | 0.576 | 0.577 | 0.939 | 0.940 | 0.248 | 0.000 |
| Logistic Regression | 0.921 ± 0.043 | 0.922 ± 0.042 | 0.606 | 0.606 | 0.909 | 0.908 | 0.267 | 0.000 |
| **Linear SVM (chosen)** | **0.927 ± 0.035** | **0.928 ± 0.034** | **0.654** | **0.652** | **0.939** | **0.940** | 0.255 | 0.000 |
| Random Forest | 0.875 ± 0.051 | 0.876 ± 0.050 | 0.503 | 0.502 | 0.909 | 0.910 | 0.285 | 0.030 |

For B, the mean per-fold macro-F1 of the Linear SVM is 0.505 ± 0.217 (the fold-mean values for every model are in the JSON file).

**Held-out results for the Linear SVM (C, n = 33):** accuracy 0.939, macro-F1 0.940; severe-error rate 0.000, over-restrictive rate 0.061.

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| public | 1.000 | 0.900 | 0.947 | 10 |
| faculty | 0.917 | 0.917 | 0.917 | 12 |
| admin | 0.917 | 1.000 | 0.957 | 11 |

**Table X.2: confusion matrix, held-out** (rows = true, columns = predicted)

| | public | faculty | admin |
|---|---|---|---|
| **public** | 9 | 1 | 0 |
| **faculty** | 0 | 11 | 1 |
| **admin** | 0 | 0 | 11 |

Both mistakes are over-restrictive (public→faculty, faculty→admin). No document was given a lower level than its true one.

**Sanity check (D):** with shuffled labels, accuracy fell to 0.346 ± 0.057, close to chance (0.33; majority share 0.364). The features do not leak the label.

**Speed:** fitting the tuned pipeline on 132 documents took 0.32 s including the grid search; prediction takes about 0.26 ms per document (excluding redaction). The saved model is 163 KB.

**Figures:**
- `report/figures/ml_model_comparison.png`: accuracy and macro-F1 for each model under A and B.
- `report/figures/ml_confusion_matrix.png`: Linear SVM, held-out set.
- `report/figures/ml_top_terms.png`: top 8 terms per class learned by the Linear SVM.

**Top terms learned (final model):**
- public: *registrar, campus, register, available, free, open, card, pm*
- faculty: *student members, members present, faculty, present, members, representatives, student representatives, minutes*
- admin: *confidential, student class, confidential student, persons named, confidential persons, persons, named, class*

### X.6 Spurious-feature check

A first look at the top terms showed the model relying on text that says nothing about sensitivity: the fictional institution name (*thornwick*, *university*), the public sign-off *"issued by the Office of the Registrar"*, redaction placeholders (*[PERSON]* became the token *person*), and generator sign-offs such as *"minutes recorded by … follow-up actions tracked by …"*, *"roll"*, *"mail / phone"*. We added these words to the stop list and kept only alphabetic tokens. With the final settings and grouped CV, macro-F1 was **0.865 without** the extra stop list and **0.638 with** it. Most of the grouped-CV score had been coming from template wording, not content. We kept the stricter version: it scores lower but reflects what the model would actually rely on.

### X.7 Model choice

The rule was: highest grouped-CV (B) macro-F1 among the trained models, and if a linear model is within 1 percentage point of the best, prefer the linear one because its decisions can be explained term by term. The Linear SVM had the best B macro-F1 (0.652) and is linear, so it was chosen. It was retrained on all 165 documents (C = 1, 3000 features) and saved to `backend/ml/models/access_classifier.joblib` with the class order and version string `access-clf-1.0`.

Under grouped CV, the hand-written keyword rule (B macro-F1 0.671, severe-error rate 0.115) does slightly better than every trained model, and makes fewer severe errors. Two caveats apply: the rule's word list was written by us after reading this corpus, so its score is optimistic; and in A and C the trained model is far better (0.928 and 0.940 versus 0.669 and 0.720).

### X.8 Use in the application

- `POST /documents/suggest-level` (faculty and admin only; students get 403, requests without a token get 401). It uses the same file types (.txt, .md, .pdf), the same 2 MB limit and the same text extraction as upload, redacts the text, and returns the suggested level, the three class probabilities, a confidence flag and the terms that pushed the decision. It stores no document and calls neither Chroma nor the LLM. A `suggest` event is written to the audit log, and the upload event records which level the model had suggested next to the level the user chose.
- **More-restrictive default:** if the top probability is below 0.60 (or the text has fewer than 5 words), the suggestion is the more restrictive of the two most likely classes and is marked "not sure".
- **Server cap unchanged:** if the suggestion is above the uploader's own level, the response says `allowed: false` with `capped_level`, because the upload endpoint will still refuse such a level.
- **Upload form:** shows "Suggested level: Faculty (93% sure)", three probability bars, a "Why?" line, and the sentence *"This is a suggestion from a model trained on our sample documents; you decide the level."* The level selector is pre-selected but can still be changed. If the model file is missing, the endpoint returns a clean 503, the form says the suggestion is unavailable, and upload works as before.

### X.9 Limitations

- **Synthetic, partly template-generated data.** Normal cross-validation (A) gives 0.93, but this is inflated: documents from the same generator template share wording. Testing on unseen topic families (B) drops macro-F1 to 0.65, a gap of about 28 points. B is the more honest estimate for new kinds of documents.
- **Severe errors on unseen topics.** In grouped CV the chosen model under-classified 25.5% of documents, compared with none on the held-out set. This is why it stays a suggestion, defaults to the more restrictive level when unsure, and never replaces the uploader's decision or the server cap.
- **Small dataset** (165 documents, 33 in the test set): one test document is worth 3 percentage points, so the held-out numbers have wide uncertainty.
- **Vocabulary mismatch:** real institutional documents will use different wording, templates and names, so performance on real uploads is unknown until the model is evaluated on them.
- **Remaining template words:** after cleaning, some top terms (*members present*, *persons named*) still come from recurring phrasing in the synthetic documents.
- **Not an access-control mechanism.** The model only pre-fills a form field. Who can read what is still decided by the token role, the server-side level cap and the retrieval filter.
- The sanity check (shuffled labels: 0.346, about chance) shows no label leakage. It does not show that the model generalises to new data.
