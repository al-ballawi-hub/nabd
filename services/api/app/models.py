from datetime import date

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

# Many-to-many association tables (fully normalized — no comma-separated strings).
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

family_member_conditions = Table(
    "family_member_conditions",
    Base.metadata,
    Column(
        "family_member_id",
        Integer,
        ForeignKey("family_members.id", ondelete="CASCADE"),
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
    medications = relationship(
        "PatientMedication",
        back_populates="patient",
        cascade="all, delete-orphan",
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
    family_members = relationship(
        "FamilyMember",
        secondary=family_member_conditions,
        back_populates="conditions",
    )


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)


class PatientMedication(Base):
    """A medication a patient is (or was) taking — mutable current state."""

    __tablename__ = "patient_medications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    medication_id = Column(
        Integer,
        ForeignKey("medications.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(20), default="active", nullable=False)  # active | stopped
    dosage = Column(String(100), nullable=True)
    started_on = Column(Date, nullable=True)

    patient = relationship("Patient", back_populates="medications")
    medication = relationship("Medication")

    @property
    def name(self) -> str:
        return self.medication.name


class DrugWarning(Base):
    """An ongoing (persisted) drug-interaction warning for a patient."""

    __tablename__ = "drug_warnings"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    severity = Column(String(20), nullable=False)  # high | moderate | low
    type = Column(String(30), nullable=False)  # drug-drug | drug-disease | allergy
    message = Column(String(300), nullable=False)
    created_on = Column(Date, default=date.today)


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

    conditions = relationship(
        "Condition",
        secondary=family_member_conditions,
        back_populates="family_members",
    )
