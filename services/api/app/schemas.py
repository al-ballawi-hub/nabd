from datetime import date

from pydantic import BaseModel, ConfigDict, Field
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
    created_by: str | None = None


class RecordTextIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    override: bool = False
    created_by: str | None = Field(default=None, max_length=120)


class RecordTextResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    saved: bool
    warnings: list[str]
    record_type: str
    title: str
    content: str


class FamilyMemberOut(ORMModel):
    id: int
    patient_id: int
    relation: str
    name: str | None
    gender: str | None
    age: int | None
    deceased: bool
    conditions: str


class FamilyMemberIn(BaseModel):
    relation: str
    name: str | None = None
    gender: str | None = None
    age: int | None = None
    deceased: bool = False
    conditions: str = ""


class RiskItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str
    date: str | None = None
    detail: str = ""


class RiskSummary(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    chronic_conditions: list[str]
    allergies: list[str]
    abnormal_labs: list[RiskItem]
    hereditary_risks: list[str]
    risk_level: str
