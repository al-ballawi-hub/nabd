"""Top Risks aggregation for the physician dashboard.

Synthesizes a patient's chronic conditions, allergies, recent abnormal lab
findings and hereditary (family) history into a single executive summary.
"""

from app import models

_EMPTY_VALUES = {"none", "n/a", "no known"}

ABNORMAL_MARKERS = (
    "above", "high", "elevated", "abnormal", "outside", "positive",
    "poor", "weakness", "borderline", "indicating", "poorly",
)

HEREDITARY_FLAG_CONDITIONS = (
    "diabetes", "hypertension", "cancer", "heart", "cardiac", "coronary",
    "stroke", "asthma", "alzheimer", "parkinson", "thyroid",
)


def _split(value: str | None) -> list[str]:
    return [
        item.strip()
        for item in (value or "").split(",")
        if item.strip() and item.strip().lower() not in _EMPTY_VALUES
    ]


def _is_abnormal(content: str) -> bool:
    return any(marker in (content or "").lower() for marker in ABNORMAL_MARKERS)


def summarize_risks(
    patient: models.Patient,
    records: list[models.MedicalRecord],
    family: list[models.FamilyMember],
) -> dict:
    chronic = _split(patient.chronic_conditions)
    allergies = _split(patient.allergies)

    abnormal_labs = []
    for rec in records:
        if rec.record_type in {"lab", "report"} and rec.content and _is_abnormal(rec.content):
            abnormal_labs.append(
                {
                    "title": rec.title or "Abnormal finding",
                    "date": rec.record_date.isoformat() if rec.record_date else None,
                    "detail": (rec.content or "")[:160],
                }
            )

    hereditary_risks = []
    for member in family:
        for condition in _split(member.conditions):
            if any(flag in condition.lower() for flag in HEREDITARY_FLAG_CONDITIONS):
                status = "deceased" if member.deceased else "living"
                hereditary_risks.append(
                    f"{member.relation.title()}: {condition} ({status})"
                )

    score = len(chronic) * 2 + len(abnormal_labs) * 2 + len(hereditary_risks) + len(allergies)
    if score >= 7:
        risk_level = "high"
    elif score >= 3:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "chronic_conditions": chronic,
        "allergies": allergies,
        "abnormal_labs": abnormal_labs,
        "hereditary_risks": hereditary_risks,
        "risk_level": risk_level,
    }
