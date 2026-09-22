"""Medical-record creation business logic (service layer)."""

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models
from app.services.ai_service import analyze_medical_text
from app.services.patient_service import get_patient
from app.services.safety_service import check_duplicate_lab


def create_record_from_text(
    db: Session,
    patient_id: int,
    text: str,
    override: bool,
    created_by: str,
) -> tuple[dict, bool]:
    """Analyze free text and create a record.

    Returns ``(result_dict, saved)``. When a safety conflict is detected and
    ``override`` is False, the record is not saved and ``saved`` is False.
    """
    patient = get_patient(db, patient_id)

    try:
        # PRIVACY: raw medical text is passed to the AI service but never logged.
        analysis = analyze_medical_text(
            text,
            allergies=[a.name for a in patient.allergies],
            conditions=[c.name for c in patient.chronic_conditions],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Text analysis failed — AI service unavailable",
        ) from exc

    warnings = list(analysis.get("conflicts", []))
    warnings += check_duplicate_lab(
        db,
        patient_id,
        analysis["record_type"],
        analysis["title"],
        analysis["content"],
    )

    if warnings and not override:
        return {
            "saved": False,
            "warnings": warnings,
            "record_type": analysis["record_type"],
            "title": analysis["title"],
            "content": analysis["content"],
        }, False

    # created_by comes from the verified JWT (passed in by the router).
    record = models.MedicalRecord(
        patient_id=patient_id,
        record_type=analysis["record_type"],
        title=analysis["title"],
        content=analysis["content"],
        source="manual",
        record_date=date.today(),
        created_by=created_by,
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save record") from exc

    return {
        "saved": True,
        "warnings": warnings,
        "record_type": record.record_type,
        "title": record.title,
        "content": record.content,
    }, True
