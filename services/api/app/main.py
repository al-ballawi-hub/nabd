from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings
from app.db import get_db, init_db
from app.seed import run_seed
from app.services.ai_service import analyze_medical_text
from app.services.safety_service import check_record_safety


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


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "nabd"}


@app.post("/api/v1/seed")
def seed(db: Session = Depends(get_db)) -> dict:
    return run_seed(db)


@app.get("/api/v1/patients", response_model=list[schemas.PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return db.query(models.Patient).all()


@app.get("/api/v1/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.get("/api/v1/patients/{patient_id}/records", response_model=list[schemas.RecordOut])
def get_records(patient_id: int, db: Session = Depends(get_db)):
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
):
    patient = (
        db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        # PRIVACY: raw medical text is passed to the AI service but never logged.
        analysis = analyze_medical_text(payload.text)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Text analysis failed — AI service unavailable",
        ) from exc

    # PRIVACY: safety check reads the patient profile but never logs it.
    warnings = check_record_safety(patient, payload.text, analysis["content"])

    if warnings and not payload.override:
        response.status_code = status.HTTP_200_OK
        return schemas.RecordTextResult(
            saved=False,
            warnings=warnings,
            record_type=analysis["record_type"],
            title=analysis["title"],
            content=analysis["content"],
        )

    record = models.MedicalRecord(
        patient_id=patient_id,
        record_type=analysis["record_type"],
        title=analysis["title"],
        content=analysis["content"],
        source="manual",
        record_date=date.today(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    response.status_code = status.HTTP_201_CREATED
    return schemas.RecordTextResult(
        saved=True,
        warnings=warnings,
        record_type=record.record_type,
        title=record.title,
        content=record.content,
    )
