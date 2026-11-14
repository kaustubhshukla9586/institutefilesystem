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

_analyzer = AnalyzerEngine()
_anonymizer = AnonymizerEngine()
_CUSTOM = [_roll_recognizer, _email_recognizer]

# Entities redacted before anything is chunked or embedded. DATE_TIME is deliberately NOT
# redacted: dates (deadlines, effective dates) are what most institutional questions are about.
_ENTITIES = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "STUDENT_ID"]
_OPERATOR_CONFIG = {e: OperatorConfig("replace", {"new_value": f"[{e}]"}) for e in _ENTITIES}


def analyze(text: str):
    if not text or not text.strip():
        return []
    return _analyzer.analyze(text=text, entities=_ENTITIES, language="en", ad_hoc_recognizers=_CUSTOM)


def redact_with_counts(text: str) -> tuple[str, Counter]:
    results = analyze(text)
    if not results:
        return text, Counter()
    out = _anonymizer.anonymize(text=text, analyzer_results=results, operators=_OPERATOR_CONFIG)
    return out.text, Counter(i.entity_type for i in out.items)


def redact_text(text: str) -> str:
    return redact_with_counts(text)[0]
