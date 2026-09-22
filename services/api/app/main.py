from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import schemas
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, require_doctor
from app.db import get_db, init_db
from app.seed import run_seed
from app.services import patient_service, record_service


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


@app.get("/api/v1/patients", response_model=schemas.Page[schemas.PatientOut])
def list_patients(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    items, total = patient_service.list_patients(db, limit, offset)
    return schemas.Page(items=items, total=total, limit=limit, offset=offset)


@app.get("/api/v1/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return patient_service.get_patient(db, patient_id)


@app.get(
    "/api/v1/patients/{patient_id}/records",
    response_model=schemas.Page[schemas.RecordOut],
)
def get_records(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    items, total = patient_service.list_records(db, patient_id, limit, offset)
    return schemas.Page(items=items, total=total, limit=limit, offset=offset)


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
    result, saved = record_service.create_record_from_text(
        db, patient_id, payload.text, payload.override, user["name"]
    )
    response.status_code = (
        status.HTTP_201_CREATED if saved else status.HTTP_200_OK
    )
    return schemas.RecordTextResult(**result)


@app.get("/api/v1/patients/{patient_id}/risks", response_model=schemas.RiskSummary)
def get_patient_risks(
    patient_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return patient_service.get_risks(db, patient_id)


@app.get(
    "/api/v1/patients/{patient_id}/family",
    response_model=schemas.Page[schemas.FamilyMemberOut],
)
def list_family(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    items, total = patient_service.list_family(db, patient_id, limit, offset)
    return schemas.Page(items=items, total=total, limit=limit, offset=offset)


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
    return patient_service.add_family_member(db, patient_id, payload)
