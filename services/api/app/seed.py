"""بيانات تجريبية وهمية بالكامل — للاختبار فقط."""
from datetime import date

from sqlalchemy.orm import Session

from app import models

PATIENTS = [
    {
        "name": "أحمد محمد العتيبي",
        "age": 54, "gender": "ذكر", "blood_type": "O+",
        "allergies": "بنسلين",
        "chronic_conditions": "سكري نوع 2, ضغط دم مرتفع",
    },
    {
        "name": "نورة سعد القحطاني",
        "age": 41, "gender": "أنثى", "blood_type": "A+",
        "allergies": "لا يوجد",
        "chronic_conditions": "ربو",
    },
    {
        "name": "خالد عبدالله الدوسري",
        "age": 67, "gender": "ذكر", "blood_type": "B+",
        "allergies": "أسبرين, مكسرات",
        "chronic_conditions": "قصور في القلب, سكري نوع 2",
    },
    {
        "name": "سارة فيصل الحربي",
        "age": 29, "gender": "أنثى", "blood_type": "AB+",
        "allergies": "لا يوجد",
        "chronic_conditions": "لا يوجد",
    },
    {
        "name": "محمد علي الغامدي",
        "age": 73, "gender": "ذكر", "blood_type": "O-",
        "allergies": "مضادات الالتهاب",
        "chronic_conditions": "ضغط دم مرتفع, خشونة مفاصل",
    },
]

# سجلات: اسم المريض -> قائمة سجلاته
RECORDS = {
    "أحمد محمد العتيبي": [
        {"record_type": "lab", "title": "تحليل سكر تراكمي HbA1c",
         "content": "النتيجة: 8.4% — أعلى من الطبيعي (4-5.6%)، يشير إلى ضعف السيطرة على السكري.",
         "source": "manual", "record_date": date(2026, 7, 15)},
        {"record_type": "prescription", "title": "وصفة: ميتفورمين 850 مجم",
         "content": "قرص بعد الغداء والعشاء يوميًا. تحذير: راقب وظائف الكلى.",
         "source": "manual", "record_date": date(2026, 7, 15)},
        {"record_type": "report", "title": "تقرير أشعة صدر",
         "content": "لا توجد مؤشرات التهاب رئوي. القلب بحجم طبيعي.",
         "source": "ocr", "record_date": date(2025, 11, 3)},
    ],
    "خالد عبدالله الدوسري": [
        {"record_type": "prescription", "title": "وصفة: وارفارين 5 مجم",
         "content": "قرص يوميًا مساءً. مضاد تجلط — يتعارض مع الأسبرين.",
         "source": "manual", "record_date": date(2026, 8, 2)},
        {"record_type": "report", "title": "تقرير قسم القلب",
         "content": "ضعف بسيط في عضلة القلب، الكسر القذفي 45%. يُنصح بمتابعة كل 3 أشهر.",
         "source": "manual", "record_date": date(2026, 8, 2)},
        {"record_type": "lab", "title": "تحليل وظائف كلى",
         "content": "الكرياتينين 1.3 ملغ/ديسيلتر — ضمن الحدود الحدّية.",
         "source": "manual", "record_date": date(2026, 5, 20)},
    ],
    "نورة سعد القحطاني": [
        {"record_type": "prescription", "title": "وصفة: سالبيوتامول بخاخ",
         "content": "عند الحاجة عند الشعور بضيق التنفس. بحد أقصى 8 مرات يوميًا.",
         "source": "manual", "record_date": date(2026, 6, 10)},
    ],
    "محمد علي الغامدي": [
        {"record_type": "prescription", "title": "وصفة: أملوديبين 5 مجم",
         "content": "قرص صباحًا يوميًا لضغط الدم.",
         "source": "manual", "record_date": date(2026, 8, 25)},
        {"record_type": "lab", "title": "تحليل ضغط وسكري",
         "content": "الضغط 150/95 ملم زئبق — أعلى من المستهدف. السكر التراكمي 7.1%.",
         "source": "manual", "record_date": date(2026, 8, 25)},
    ],
}


def run_seed(db: Session) -> dict:
    if db.query(models.Patient).count() > 0:
        return {"message": "البيانات التجريبية موجودة مسبقًا", "seeded": False}

    for p in PATIENTS:
        patient = models.Patient(**p)
        db.add(patient)
        db.flush()
        for r in RECORDS.get(p["name"], []):
            db.add(models.MedicalRecord(patient_id=patient.id, **r))

    db.commit()
    return {
        "message": "تم توليد بيانات تجريبية (وهمية بالكامل)",
        "seeded": True,
        "patients": len(PATIENTS),
        "records": sum(len(v) for v in RECORDS.values()),
    }
