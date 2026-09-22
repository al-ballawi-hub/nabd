"""Context-aware safety guardrails for record assignment.

Checks new medical content against a patient's allergies and chronic
conditions using negation-aware keyword matching, and flags duplicate lab
tests within a recent history window. This is a deterministic heuristic layer
(a demo safety engine), not a substitute for clinical judgment.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app import models

ALLERGY_KEYWORDS: dict[str, list[str]] = {
    "penicillin": ["penicillin", "amoxicillin", "ampicillin"],
    "aspirin": ["aspirin"],
    "nsaid": ["ibuprofen", "naproxen", "diclofenac", "celecoxib", "ketorolac", "nsaid"],
    "sulfa": ["sulfa", "sulfamethoxazole", "bactrim", "sulfonamide"],
    "nuts": ["peanut", "nuts", "almond", "walnut", "cashew"],
}

CONDITION_CONFLICTS: dict[str, list[str]] = {
    "asthma": [
        "propranolol", "metoprolol", "atenolol", "nsaid", "aspirin", "ibuprofen", "naproxen"
    ],
    "hypertension": ["pseudoephedrine", "phenylephrine"],
    "diabetes": ["prednisone", "prednisolone", "corticosteroid", "glucocorticoid"],
    "heart failure": ["nsaid", "ibuprofen", "naproxen", "pioglitazone", "verapamil"],
    "kidney": ["nsaid", "ibuprofen", "naproxen", "metformin"],
}

NEGATION_TERMS = (
    "no ", "not ", "never ", "without ", "denies ", "denied ", "negative for ",
    "no history of ", "no evidence of ", "no known ", "ruled out ", "free of ",
    "absence of ", "lacks ", "does not ", "doesn't ",
)

_EMPTY_VALUES = {"none", "n/a", "no known", "no known allergies", "no known drug allergies"}

# Lab test "keys" used to detect duplicates within a recent window.
LAB_TEST_KEYS = [
    "hba1c", "glucose", "creatinine", "cholesterol", "lipid", "cbc",
    "hemoglobin", "tsh", "thyroid", "liver", "alt", "ast", "potassium",
    "sodium", "vitamin d", "vitamin",
]


def _split_list(value: str | None) -> list[str]:
    return [
        item.strip()
        for item in (value or "").split(",")
        if item.strip() and item.strip().lower() not in _EMPTY_VALUES
    ]


def _is_negated(combined: str, index: int) -> bool:
    window = combined[max(0, index - 60):index]
    return any(term in window for term in NEGATION_TERMS)


def _has_affirmed(combined: str, keyword: str) -> bool:
    """True if `keyword` appears at least once outside a negated context."""
    start = 0
    while True:
        idx = combined.find(keyword, start)
        if idx == -1:
            return False
        if not _is_negated(combined, idx):
            return True
        start = idx + len(keyword)
    return False


def _keywords_for_allergy(allergy: str) -> list[str]:
    key = allergy.lower()
    for name, keywords in ALLERGY_KEYWORDS.items():
        if name in key:
            return keywords
    return [key]


def check_record_safety(patient, text: str, content: str) -> list[str]:
    """Return a list of safety warnings for the proposed record."""
    combined = f"{text} {content}".lower()

    allergies = _split_list(patient.allergies)
    conditions = _split_list(patient.chronic_conditions)

    warnings: list[str] = []

    for allergy in allergies:
        for keyword in _keywords_for_allergy(allergy):
            if _has_affirmed(combined, keyword):
                warnings.append(
                    f"'{keyword.title()}' may trigger the patient's {allergy} allergy."
                )
                break

    for condition in conditions:
        condition_key = next(
            (k for k in CONDITION_CONFLICTS if k in condition.lower()),
            None,
        )
        if not condition_key:
            continue
        for med in CONDITION_CONFLICTS[condition_key]:
            if _has_affirmed(combined, med):
                warnings.append(
                    f"'{med.title()}' is contraindicated for the patient's {condition}."
                )

    return list(dict.fromkeys(warnings))


def _extract_lab_test_key(title: str) -> str | None:
    t = title.lower()
    for key in LAB_TEST_KEYS:
        if key in t:
            return key
    return None


def check_duplicate_lab(
    db: Session,
    patient_id: int,
    record_type: str,
    title: str,
    content: str = "",
    days: int = 30,
) -> list[str]:
    """Flag a duplicate lab test if the same test was ordered recently."""
    if record_type != "lab":
        return []

    test_key = _extract_lab_test_key(f"{title} {content}")
    if not test_key:
        return []

    cutoff = date.today() - timedelta(days=days)
    recent = (
        db.query(models.MedicalRecord)
        .filter(
            models.MedicalRecord.patient_id == patient_id,
            models.MedicalRecord.record_type == "lab",
            models.MedicalRecord.record_date >= cutoff,
        )
        .all()
    )

    for rec in recent:
        rec_key = _extract_lab_test_key(f"{rec.title or ''} {rec.content or ''}")
        if rec_key == test_key:
            when = rec.record_date.isoformat() if rec.record_date else "recently"
            return [
                f"Duplicate lab test: a '{test_key}' test was already ordered on {when} "
                f"(within the last {days} days)."
            ]

    return []
