from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings
from app.db import get_db, init_db
from app.seed import run_seed
from app.services.ai_service import analyze_medical_text


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
        raise HTTPException(status_code=404, detail="المريض غير موجود")
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
    response_model=schemas.RecordOut,
    status_code=201,
)
def create_record_from_text(
    patient_id: int,
    payload: schemas.RecordTextIn,
    db: Session = Depends(get_db),
):
    patient = (
        db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="المريض غير موجود")

    try:
        # PRIVACY: raw medical text is passed to the AI service but never logged.
        analysis = analyze_medical_text(payload.text)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="تعذر تحليل النص — فشل الاتصال بخدمة الذكاء الاصطناعي",
        ) from exc

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
    return record
