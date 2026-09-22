from sqlalchemy import Column, Date, Integer, String, Text

from app.db import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    blood_type = Column(String(5))
    allergies = Column(Text, default="")            # مفصولة بفواصل
    chronic_conditions = Column(Text, default="")   # مفصولة بفواصل


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True, nullable=False)
    record_type = Column(String(50))   # lab | prescription | report | scan
    title = Column(String(200))
    content = Column(Text)
    source = Column(String(50), default="manual")  # manual | ocr
    record_date = Column(Date)
