from datetime import date

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ORMModel(BaseModel):
    """Base schema that maps SQLAlchemy attributes to camelCase JSON."""

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class PatientOut(ORMModel):
    id: int
    name: str
    age: int | None
    gender: str | None
    blood_type: str | None
    allergies: str
    chronic_conditions: str


class RecordOut(ORMModel):
    id: int
    patient_id: int
    record_type: str
    title: str
    content: str
    source: str
    record_date: date | None


class RecordTextIn(BaseModel):
    text: str
    override: bool = False


class RecordTextResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    saved: bool
    warnings: list[str]
    record_type: str
    title: str
    content: str
