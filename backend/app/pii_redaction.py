from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Custom recognizer for synthetic roll numbers (format: RK3P25KZBxx where xx is digits)
# Pattern covers e.g. RK3P25KZB01 through RK3P25KZB99 and longer variants
_roll_pattern = Pattern(
    name="roll_number_pattern",
    regex=r"\bRK3P25KZB\d{2,4}\b",
    score=0.9,
)
_roll_recognizer = PatternRecognizer(
    supported_entity="STUDENT_ID",
    patterns=[_roll_pattern],
)

_analyzer = AnalyzerEngine()
_analyzer.registry.add_recognizer(_roll_recognizer)
_anonymizer = AnonymizerEngine()

_OPERATOR_CONFIG = {
    "PERSON":       OperatorConfig("replace", {"new_value": "[PERSON]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE_NUMBER]"}),
    "EMAIL_ADDRESS":OperatorConfig("replace", {"new_value": "[EMAIL_ADDRESS]"}),
    "STUDENT_ID":   OperatorConfig("replace", {"new_value": "[STUDENT_ID]"}),
    "DATE_TIME":    OperatorConfig("replace", {"new_value": "[DATE]"}),
    "LOCATION":     OperatorConfig("replace", {"new_value": "[LOCATION]"}),
    "DEFAULT":      OperatorConfig("replace", {"new_value": "[REDACTED]"}),
}

_ENTITIES = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "STUDENT_ID"]


def redact_text(text: str) -> str:
    if not text or not text.strip():
        return text
    results = _analyzer.analyze(text=text, entities=_ENTITIES, language="en")
    if not results:
        return text
    anonymized = _anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=_OPERATOR_CONFIG,
    )
    return anonymized.text
