"""Active-medication management and drug-warning persistence (service layer)."""

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models, schemas


def list_medications(db: Session, patient_id: int) -> list[models.PatientMedication]:
    return (
        db.query(models.PatientMedication)
        .filter(models.PatientMedication.patient_id == patient_id)
        .order_by(models.PatientMedication.id)
        .all()
    )


def add_medication(
    db: Session, patient_id: int, payload: schemas.MedicationIn
) -> models.PatientMedication:
    medication = _get_or_create_medication(db, payload.name)
    existing = (
        db.query(models.PatientMedication)
        .filter(
            models.PatientMedication.patient_id == patient_id,
            models.PatientMedication.medication_id == medication.id,
            models.PatientMedication.status == "active",
        )
        .first()
    )
    if existing:
        return existing  # already active — no-op

    pm = models.PatientMedication(
        patient_id=patient_id,
        medication_id=medication.id,
        status="active",
        dosage=payload.dosage,
        started_on=date.today(),
    )
    try:
        db.add(pm)
        db.commit()
        db.refresh(pm)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save medication") from exc
    return pm


def stop_medication(
    db: Session, patient_id: int, medication_id: int
) -> models.PatientMedication:
    pm = (
        db.query(models.PatientMedication)
        .filter(
            models.PatientMedication.patient_id == patient_id,
            models.PatientMedication.id == medication_id,
        )
        .first()
    )
    if not pm:
        raise HTTPException(status_code=404, detail="Medication not found")

    pm.status = "stopped"
    try:
        db.commit()
        db.refresh(pm)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to update medication"
        ) from exc
    return pm


def _get_or_create_medication(db: Session, name: str) -> models.Medication:
    medication = (
        db.query(models.Medication).filter(models.Medication.name == name).first()
    )
    if not medication:
        medication = models.Medication(name=name)
        db.add(medication)
        db.flush()
    return medication


def register_active_medication(
    db: Session, patient_id: int, name: str, dosage: str | None = None
) -> None:
    """Register a medication as active. No commit — the caller owns the transaction."""
    medication = _get_or_create_medication(db, name)
    existing = (
        db.query(models.PatientMedication)
        .filter(
            models.PatientMedication.patient_id == patient_id,
            models.PatientMedication.medication_id == medication.id,
            models.PatientMedication.status == "active",
        )
        .first()
    )
    if existing:
        return

    db.add(
        models.PatientMedication(
            patient_id=patient_id,
            medication_id=medication.id,
            status="active",
            dosage=dosage,
            started_on=date.today(),
        )
    )


def store_drug_warnings(db: Session, patient_id: int, conflicts: list[dict]) -> None:
    """Persist drug-drug / drug-disease conflicts. No commit — caller commits."""
    for conflict in conflicts:
        if conflict.get("type") not in {"drug-drug", "drug-disease"}:
            continue
        db.add(
            models.DrugWarning(
                patient_id=patient_id,
                severity=conflict.get("severity", "moderate"),
                type=conflict.get("type", "drug-disease"),
                message=conflict.get("message", ""),
            )
        )
