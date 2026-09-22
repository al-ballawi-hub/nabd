from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class Page[T](BaseModel):
    """Offset/limit pagination envelope for list endpoints."""

    items: list[T]
    total: int
    limit: int
    offset: int


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
    allergies: list[str]
    chronic_conditions: list[str]

    @field_validator("allergies", "chronic_conditions", mode="before")
    @classmethod
    def _to_names(cls, value):
        if isinstance(value, list):
            return [getattr(x, "name", x) for x in value]
        return value


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


class RecordTextResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    saved: bool
    warnings: list[str]
    record_type: str
    title: str
    content: str


class LoginIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: Literal["doctor", "patient"]


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    name: str
    role: str


class FamilyMemberOut(ORMModel):
    id: int
    patient_id: int
    relation: str
    name: str | None
    gender: str | None
    age: int | None
    deceased: bool
    conditions: list[str]

    @field_validator("conditions", mode="before")
    @classmethod
    def _to_names(cls, value):
        if isinstance(value, list):
            return [getattr(x, "name", x) for x in value]
        return value


class FamilyMemberIn(BaseModel):
    relation: str = Field(min_length=1, max_length=50)
    name: str | None = Field(default=None, max_length=120)
    gender: str | None = Field(default=None, max_length=10)
    age: int | None = None
    deceased: bool = False
    conditions: list[str] = Field(default_factory=list)


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
