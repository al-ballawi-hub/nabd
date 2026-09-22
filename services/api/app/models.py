from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base

# Many-to-many association tables (normalized — no comma-separated strings).
patient_allergies = Table(
    "patient_allergies",
    Base.metadata,
    Column(
        "patient_id",
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "allergy_id",
        Integer,
        ForeignKey("allergies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

patient_conditions = Table(
    "patient_conditions",
    Base.metadata,
    Column(
        "patient_id",
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "condition_id",
        Integer,
        ForeignKey("conditions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    blood_type = Column(String(5))

    allergies = relationship(
        "Allergy", secondary=patient_allergies, back_populates="patients"
    )
    chronic_conditions = relationship(
        "Condition", secondary=patient_conditions, back_populates="patients"
    )


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)

    patients = relationship(
        "Patient", secondary=patient_allergies, back_populates="allergies"
    )


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)

    patients = relationship(
        "Patient", secondary=patient_conditions, back_populates="chronic_conditions"
    )


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    record_type = Column(String(50))   # lab | prescription | report | scan
    title = Column(String(200))
    content = Column(Text)
    source = Column(String(50), default="manual")  # manual | ocr
    record_date = Column(Date)
    created_by = Column(String(120), nullable=True)  # audit: doctor name (from JWT)


class FamilyMember(Base):
    """A relative tracked for hereditary risk in the family medical tree."""

    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    relation = Column(String(50), nullable=False)
    name = Column(String(120), nullable=True)
    gender = Column(String(10))
    age = Column(Integer)
    deceased = Column(Boolean, default=False)
    conditions = Column(Text, default="")
