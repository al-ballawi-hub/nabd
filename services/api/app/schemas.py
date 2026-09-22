from datetime import date

from pydantic import BaseModel


class PatientOut(BaseModel):
    id: int
    name: str
    age: int | None
    gender: str | None
    blood_type: str | None
    allergies: str
    chronic_conditions: str

    model_config = {"from_attributes": True}


class RecordOut(BaseModel):
    id: int
    patient_id: int
    record_type: str
    title: str
    content: str
    source: str
    record_date: date | None

    model_config = {"from_attributes": True}
