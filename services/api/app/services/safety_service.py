"""Deterministic record guardrails (non-NLP).

Safety conflict detection (allergy/condition checks with negation handling)
lives in `ai_service.py` and is performed by the LLM. This module only holds
deterministic, DB-driven checks that do not require language understanding —
specifically duplicate lab-test detection.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app import models

# Lab test "keys" used to detect duplicates within a recent window.
LAB_TEST_KEYS = [
    "hba1c", "glucose", "creatinine", "cholesterol", "lipid", "cbc",
    "hemoglobin", "tsh", "thyroid", "liver", "alt", "ast", "potassium",
    "sodium", "vitamin d", "vitamin",
]


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
