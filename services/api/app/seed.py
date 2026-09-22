"""Completely fictional seed data — for testing only."""
from datetime import date

from sqlalchemy.orm import Session

from app import models

# Allergies and chronic conditions are normalized lists (many-to-many).
PATIENTS = [
    {
        "name": "Ahmed Mohammed Al-Otaibi",
        "age": 54, "gender": "Male", "blood_type": "O+",
        "allergies": ["Penicillin"],
        "chronic_conditions": ["Type 2 Diabetes", "Hypertension"],
    },
    {
        "name": "Noura Saad Al-Qahtani",
        "age": 41, "gender": "Female", "blood_type": "A+",
        "allergies": [],
        "chronic_conditions": ["Asthma"],
    },
    {
        "name": "Khalid Abdullah Al-Dosari",
        "age": 67, "gender": "Male", "blood_type": "B+",
        "allergies": ["Aspirin", "Nuts"],
        "chronic_conditions": ["Heart Failure", "Type 2 Diabetes"],
    },
    {
        "name": "Sara Faisal Al-Harbi",
        "age": 29, "gender": "Female", "blood_type": "AB+",
        "allergies": [],
        "chronic_conditions": [],
    },
    {
        "name": "Mohammed Ali Al-Ghamdi",
        "age": 73, "gender": "Male", "blood_type": "O-",
        "allergies": ["NSAIDs"],
        "chronic_conditions": ["Hypertension", "Osteoarthritis"],
    },
]

# Records: patient name -> list of their records
RECORDS = {
    "Ahmed Mohammed Al-Otaibi": [
        {"record_type": "lab", "title": "HbA1c Glycated Hemoglobin",
         "content": (
             "Result: 8.4% — above the normal range (4-5.6%), indicating poor "
             "glycemic control."
         ),
         "source": "manual", "record_date": date(2026, 7, 15)},
        {"record_type": "prescription", "title": "Prescription: Metformin 850 mg",
         "content": "One tablet after lunch and dinner daily. Caution: monitor renal function.",
         "source": "manual", "record_date": date(2026, 7, 15)},
        {"record_type": "report", "title": "Chest X-Ray Report",
         "content": "No signs of pneumonia. Normal cardiac silhouette.",
         "source": "ocr", "record_date": date(2025, 11, 3)},
    ],
    "Khalid Abdullah Al-Dosari": [
        {"record_type": "prescription", "title": "Prescription: Warfarin 5 mg",
         "content": "One tablet daily in the evening. Anticoagulant — interacts with aspirin.",
         "source": "manual", "record_date": date(2026, 8, 2)},
        {"record_type": "report", "title": "Cardiology Report",
         "content": (
             "Mild cardiac muscle weakness, ejection fraction 45%. Follow-up "
             "recommended every 3 months."
         ),
         "source": "manual", "record_date": date(2026, 8, 2)},
        {"record_type": "lab", "title": "Renal Function Panel",
         "content": "Creatinine 1.3 mg/dL — borderline within normal limits.",
         "source": "manual", "record_date": date(2026, 5, 20)},
    ],
    "Noura Saad Al-Qahtani": [
        {"record_type": "prescription", "title": "Prescription: Salbutamol Inhaler",
         "content": "Use as needed for shortness of breath. Maximum 8 inhalations daily.",
         "source": "manual", "record_date": date(2026, 6, 10)},
    ],
    "Mohammed Ali Al-Ghamdi": [
        {"record_type": "prescription", "title": "Prescription: Amlodipine 5 mg",
         "content": "One tablet each morning for blood pressure.",
         "source": "manual", "record_date": date(2026, 8, 25)},
        {"record_type": "lab", "title": "Blood Pressure & Glucose Panel",
         "content": "Blood pressure 150/95 mmHg — above target. HbA1c 7.1%.",
         "source": "manual", "record_date": date(2026, 8, 25)},
    ],
}

# Family members: patient name -> list of relatives (for the medical family tree)
FAMILY = {
    "Ahmed Mohammed Al-Otaibi": [
        {"relation": "father", "name": "Mohammed Al-Otaibi", "gender": "Male",
         "age": 78, "deceased": True, "conditions": ["Type 2 Diabetes", "Coronary Artery Disease"]},
        {"relation": "mother", "name": "Fatimah Al-Otaibi", "gender": "Female",
         "age": 72, "deceased": False, "conditions": ["Hypertension"]},
    ],
    "Khalid Abdullah Al-Dosari": [
        {"relation": "father", "name": "Abdullah Al-Dosari", "gender": "Male",
         "age": 81, "deceased": True, "conditions": ["Heart Failure", "Coronary Artery Disease"]},
        {"relation": "brother", "name": "Fahad Al-Dosari", "gender": "Male",
         "age": 60, "deceased": False, "conditions": ["Type 2 Diabetes"]},
    ],
    "Noura Saad Al-Qahtani": [
        {"relation": "mother", "name": "Aisha Al-Qahtani", "gender": "Female",
         "age": 68, "deceased": False, "conditions": ["Asthma"]},
    ],
}


def _get_or_create(db: Session, model: type, name: str):
    obj = db.query(model).filter(model.name == name).first()
    if not obj:
        obj = model(name=name)
        db.add(obj)
        db.flush()
    return obj


def run_seed(db: Session) -> dict:
    if db.query(models.Patient).count() > 0:
        return {"message": "Demo data already exists", "seeded": False}

    for p in PATIENTS:
        patient = models.Patient(
            name=p["name"],
            age=p["age"],
            gender=p["gender"],
            blood_type=p["blood_type"],
        )
        db.add(patient)
        db.flush()

        for name in p["allergies"]:
            patient.allergies.append(_get_or_create(db, models.Allergy, name))
        for name in p["chronic_conditions"]:
            patient.chronic_conditions.append(_get_or_create(db, models.Condition, name))

        for r in RECORDS.get(p["name"], []):
            db.add(models.MedicalRecord(patient_id=patient.id, **r))
        for f in FAMILY.get(p["name"], []):
            member = models.FamilyMember(
                patient_id=patient.id,
                relation=f["relation"],
                name=f.get("name"),
                gender=f.get("gender"),
                age=f.get("age"),
                deceased=f.get("deceased", False),
            )
            db.add(member)
            db.flush()
            for name in f["conditions"]:
                member.conditions.append(_get_or_create(db, models.Condition, name))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Demo data generated (completely fictional)",
        "seeded": True,
        "patients": len(PATIENTS),
        "records": sum(len(v) for v in RECORDS.values()),
        "family_members": sum(len(v) for v in FAMILY.values()),
    }
