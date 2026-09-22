"""Patient, records and family-members business logic (service layer)."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.services.risk_service import summarize_risks


def list_patients(db: Session, limit: int, offset: int) -> tuple[list[models.Patient], int]:
    query = db.query(models.Patient)
    total = query.count()
    items = query.order_by(models.Patient.id).offset(offset).limit(limit).all()
    return items, total


def get_patient(db: Session, patient_id: int) -> models.Patient:
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def list_records(
    db: Session, patient_id: int, limit: int, offset: int
) -> tuple[list[models.MedicalRecord], int]:
    get_patient(db, patient_id)  # 404 if the patient does not exist
    query = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.patient_id == patient_id
    )
    total = query.count()
    items = query.order_by(models.MedicalRecord.id.desc()).offset(offset).limit(limit).all()
    return items, total


def list_family(
    db: Session, patient_id: int, limit: int, offset: int
) -> tuple[list[models.FamilyMember], int]:
    get_patient(db, patient_id)
    query = db.query(models.FamilyMember).filter(
        models.FamilyMember.patient_id == patient_id
    )
    total = query.count()
    items = query.order_by(models.FamilyMember.id).offset(offset).limit(limit).all()
    return items, total


def _get_or_create_condition(db: Session, name: str) -> models.Condition:
    condition = db.query(models.Condition).filter(models.Condition.name == name).first()
    if not condition:
        condition = models.Condition(name=name)
        db.add(condition)
        db.flush()
    return condition


def add_family_member(
    db: Session, patient_id: int, payload: schemas.FamilyMemberIn
) -> models.FamilyMember:
    get_patient(db, patient_id)
    member = models.FamilyMember(
        patient_id=patient_id,
        relation=payload.relation,
        name=payload.name,
        gender=payload.gender,
        age=payload.age,
        deceased=payload.deceased,
    )
    try:
        db.add(member)
        db.flush()
        for name in payload.conditions:
            member.conditions.append(_get_or_create_condition(db, name))
        db.commit()
        db.refresh(member)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to save family member"
        ) from exc
    return member


def get_risks(db: Session, patient_id: int) -> dict:
    patient = get_patient(db, patient_id)
    records, _ = list_records(db, patient_id, limit=1000, offset=0)
    family, _ = list_family(db, patient_id, limit=1000, offset=0)
    return summarize_risks(patient, records, family)
