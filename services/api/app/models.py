from sqlalchemy import Boolean, Column, Date, Integer, String, Text

from app.db import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    blood_type = Column(String(5))
    allergies = Column(Text, default="")            # comma-separated
    chronic_conditions = Column(Text, default="")   # comma-separated


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True, nullable=False)
    record_type = Column(String(50))   # lab | prescription | report | scan
    title = Column(String(200))
    content = Column(Text)
    source = Column(String(50), default="manual")  # manual | ocr
    record_date = Column(Date)
    created_by = Column(String(120), nullable=True)  # audit: doctor name


class FamilyMember(Base):
    """A relative tracked for hereditary risk in the family medical tree."""

    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True, nullable=False)
    relation = Column(String(50), nullable=False)   # father | mother | sibling | ...
    name = Column(String(120), nullable=True)
    gender = Column(String(10))
    age = Column(Integer)
    deceased = Column(Boolean, default=False)
    conditions = Column(Text, default="")           # comma-separated conditions
