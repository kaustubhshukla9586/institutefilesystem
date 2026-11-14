import re
from collections import Counter

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Synthetic roll numbers, e.g. RK3P25KZB01 .. RK3P25KZB9999
_roll_recognizer = PatternRecognizer(
    supported_entity="STUDENT_ID", name="RollNumberRecognizer",
    patterns=[Pattern(name="roll_number_pattern", regex=r"\bRK3P25KZB\d{2,4}\b", score=0.9)],
)

# Presidio's built-in e-mail recognizer validates the TLD, so it misses the reserved
# fictional domain thornwick.example; this plain pattern catches any address.
_email_recognizer = PatternRecognizer(
    supported_entity="EMAIL_ADDRESS", name="AnyTldEmailRecognizer",
    patterns=[Pattern(name="email_any_tld", regex=r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", score=0.95)],
)

# Indian mobile numbers (+91 98123 45678, 098123-45678, 9812345678) and other long dialled numbers.
_phone_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER", name="IndianPhoneRecognizer",
    patterns=[Pattern(name="in_mobile", regex=r"(?<![\w-])(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?![\w-])", score=0.9),
              Pattern(name="intl_dialled", regex=r"(?<![\w-])\+\d{1,3}[\s-]?\(?\d{2,4}\)?(?:[\s-]?\d{3,4}){2,3}(?![\w-])", score=0.85)],
)

# Honorific + name, including initials: "Dr. K. S. Rao", "Prof. Aditi Sharma", "Ms A. S. Padhye".
_titled_recognizer = PatternRecognizer(
    supported_entity="PERSON", name="TitledNameRecognizer",
    patterns=[Pattern(name="titled_name",
                      regex=r"\b(?:Dr|Prof|Mr|Ms|Mrs|Shri|Smt)\.?\s+(?:[A-Z]\.\s*){0,3}[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}",
                      score=0.8)],
)

_analyzer = AnalyzerEngine()
_anonymizer = AnonymizerEngine()
_CUSTOM = [_roll_recognizer, _email_recognizer, _phone_recognizer, _titled_recognizer]

# Generated text uses narrow no-break spaces and non-breaking hyphens, which defeat spaCy
# tokenisation and phone patterns. Normalise them before analysis.
_NORMALISE = str.maketrans({" ": " ", " ": " ", " ": " ", " ": " ", "‑": "-", "‐": "-"})


def normalise(text: str) -> str:
    return text.translate(_NORMALISE)

# Entities redacted before anything is chunked or embedded. DATE_TIME is deliberately NOT
# redacted: dates (deadlines, effective dates) are what most institutional questions are about.
_ENTITIES = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "STUDENT_ID"]
_OPERATOR_CONFIG = {e: OperatorConfig("replace", {"new_value": f"[{e}]"}) for e in _ENTITIES}


# ---- Roster: a capitalised name written right next to a roll number is a student's name. ----
_NAME = r"([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})"
_ROLL = r"RK3P25KZB\d{2,4}"
_ROSTER_PATTERNS = [
    re.compile(_NAME + r"\**\W{0,6}(?:Roll(?: No)?\.?:?|roll)?\s*" + _ROLL),   # Ananya Verma – Roll No. RK..
    re.compile(_ROLL + r"\)?\s*(?:–|-|\(|,)\s*" + _NAME),                      # RK.. – Ananya Verma / RK.. (Ananya Verma)
]
_NOT_NAMES = {"Roll No", "Roll Nos", "Student Id", "Case Number", "Course Code"}
_corpus_roster: set[str] | None = None
_PREFIXES = {"Professor", "Student", "Officer", "Dr", "Prof"}


def roster_from(text: str) -> set[str]:
    names = set()
    for p in _ROSTER_PATTERNS:
        names.update(m.group(1) for m in p.finditer(text))
    return {n for n in names if n not in _NOT_NAMES}


def corpus_roster() -> set[str]:
    """Names attached to roll numbers anywhere in the seed corpus (built once)."""
    global _corpus_roster
    if _corpus_roster is None:
        import json
        import os
        path = os.path.join(os.path.dirname(__file__), "seed_data", "raw_docs", "documents.json")
        _corpus_roster = set()
        if os.path.exists(path):
            for d in json.load(open(path, encoding="utf-8")):
                _corpus_roster |= roster_from(normalise(d["content"]))
    return _corpus_roster


def analyze(text: str):
    if not text or not text.strip():
        return []
    recognizers = list(_CUSTOM)
    full = corpus_roster() | roster_from(text)
    # also the bare first names of rostered people ("- Meera: [PHONE_NUMBER]")
    firsts = {n.split()[-2] if n.split()[0] in _PREFIXES else n.split()[0] for n in full}
    lasts = {n.split()[-1] for n in full}
    names = sorted(full | {f for f in firsts | lasts if len(f) > 3 and f not in _PREFIXES})
    if names:
        recognizers.append(PatternRecognizer(supported_entity="PERSON", name="RosterRecognizer",
                                             deny_list=names, deny_list_score=0.95))
    return _analyzer.analyze(text=text, entities=_ENTITIES, language="en", ad_hoc_recognizers=recognizers)


def redact_with_counts(text: str) -> tuple[str, Counter]:
    text = normalise(text or "")
    results = analyze(text)
    if not results:
        return text, Counter()
    out = _anonymizer.anonymize(text=text, analyzer_results=results, operators=_OPERATOR_CONFIG)
    return out.text, Counter(i.entity_type for i in out.items)


def redact_text(text: str) -> str:
    return redact_with_counts(text)[0]
