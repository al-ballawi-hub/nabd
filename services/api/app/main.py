from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, require_doctor
from app.db import get_db, init_db
from app.seed import run_seed
from app.services.ai_service import analyze_medical_text
from app.services.risk_service import summarize_risks
from app.services.safety_service import check_duplicate_lab


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/auth/login", response_model=schemas.TokenOut)
def login(payload: schemas.LoginIn):
    token = create_access_token(payload.name, payload.role)
    return schemas.TokenOut(
        access_token=token,
        token_type="bearer",
        name=payload.name,
        role=payload.role,
    )


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "nabd"}


@app.post("/api/v1/seed")
def seed(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_doctor),
) -> dict:
    return run_seed(db)


@app.get("/api/v1/patients", response_model=list[schemas.PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return db.query(models.Patient).all()


@app.get("/api/v1/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.get("/api/v1/patients/{patient_id}/records", response_model=list[schemas.RecordOut])
def get_records(
    patient_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return (
        db.query(models.MedicalRecord)
        .filter(models.MedicalRecord.patient_id == patient_id)
        .all()
    )


@app.post(
    "/api/v1/patients/{patient_id}/records/text",
    response_model=schemas.RecordTextResult,
)
def create_record_from_text(
    patient_id: int,
    payload: schemas.RecordTextIn,
    response: Response,
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    patient = (
        db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        # PRIVACY: raw medical text is passed to the AI service but never logged.
        analysis = analyze_medical_text(
            payload.text,
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

    if warnings and not payload.override:
        response.status_code = status.HTTP_200_OK
        return schemas.RecordTextResult(
            saved=False,
            warnings=warnings,
            record_type=analysis["record_type"],
            title=analysis["title"],
            content=analysis["content"],
        )

    # created_by is taken from the verified JWT, never from the request body.
    record = models.MedicalRecord(
        patient_id=patient_id,
        record_type=analysis["record_type"],
        title=analysis["title"],
        content=analysis["content"],
        source="manual",
        record_date=date.today(),
        created_by=user["name"],
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save record") from exc

    response.status_code = status.HTTP_201_CREATED
    return schemas.RecordTextResult(
        saved=True,
        warnings=warnings,
        record_type=record.record_type,
        title=record.title,
        content=record.content,
    )


@app.get("/api/v1/patients/{patient_id}/risks", response_model=schemas.RiskSummary)
def get_patient_risks(
    patient_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    patient = (
        db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    records = (
        db.query(models.MedicalRecord)
        .filter(models.MedicalRecord.patient_id == patient_id)
        .all()
    )
    family = (
        db.query(models.FamilyMember)
        .filter(models.FamilyMember.patient_id == patient_id)
        .all()
    )
    return summarize_risks(patient, records, family)


@app.get(
    "/api/v1/patients/{patient_id}/family",
    response_model=list[schemas.FamilyMemberOut],
)
def list_family(
    patient_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return (
        db.query(models.FamilyMember)
        .filter(models.FamilyMember.patient_id == patient_id)
        .all()
    )


@app.post(
    "/api/v1/patients/{patient_id}/family",
    response_model=schemas.FamilyMemberOut,
    status_code=201,
)
def add_family_member(
    patient_id: int,
    payload: schemas.FamilyMemberIn,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_doctor),
):
    patient = (
        db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    member = models.FamilyMember(patient_id=patient_id, **payload.model_dump())
    try:
        db.add(member)
        db.commit()
        db.refresh(member)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save family member") from exc

    return member
