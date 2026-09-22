import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

type Patient = {
  id: number;
  name: string;
  age: number | null;
  gender: string | null;
  blood_type: string | null;
  allergies: string;
  chronic_conditions: string;
};

type MedicalRecord = {
  id: number;
  patient_id: number;
  record_type: string;
  title: string;
  content: string;
  source: string;
  record_date: string | null;
};

const RECORD_TYPES: Record<string, { label: string; className: string }> = {
  lab: { label: "تحليل مخبري", className: "chip" },
  prescription: { label: "وصفة طبية", className: "chip-info" },
  report: { label: "تقرير", className: "chip-warn" },
  scan: { label: "أشعة", className: "chip-danger" },
};

const split = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

export default function PatientDetail() {
  const { id } = useParams();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`/api/v1/patients/${id}`).then((r) =>
        r.ok ? r.json() : Promise.reject()
      ),
      fetch(`/api/v1/patients/${id}/records`).then((r) =>
        r.ok ? r.json() : Promise.reject()
      ),
    ])
      .then(([p, recs]) => {
        setPatient(p);
        setRecords(recs);
        setError("");
        setLoading(false);
      })
      .catch(() => {
        setError("تعذر تحميل بيانات المريض");
        setLoading(false);
      });
  }, [id]);

  return (
    <div>
      <header className="header">
        <div>
          <h1>نَبْض</h1>
          <p className="tagline">ملف المريض — Patient Profile</p>
        </div>
        <Link className="btn" to="/">
          العودة للقائمة
        </Link>
      </header>

      <main className="container">
        {loading && <p className="muted">جارٍ التحميل...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && patient && (
          <>
            <div className="card patient-card">
              <h2>{patient.name}</h2>
              <p className="muted">
                {patient.age} سنة · {patient.gender} · فصيلة الدم{" "}
                {patient.blood_type}
              </p>
              <div className="section">
                <span className="label">الحساسية:</span>
                {split(patient.allergies).map((a) => (
                  <span className="chip chip-danger" key={a}>
                    {a}
                  </span>
                ))}
              </div>
              <div className="section">
                <span className="label">أمراض مزمنة:</span>
                {split(patient.chronic_conditions).map((c) => (
                  <span className="chip" key={c}>
                    {c}
                  </span>
                ))}
              </div>
            </div>

            <h2 className="section-title">السجلات الطبية ({records.length})</h2>
            {records.length === 0 && (
              <p className="muted">لا توجد سجلات طبية لهذا المريض.</p>
            )}

            <div className="records">
              {records.map((r) => {
                const t = RECORD_TYPES[r.record_type] ?? {
                  label: r.record_type,
                  className: "chip",
                };
                return (
                  <div className="card record-card" key={r.id}>
                    <div className="record-head">
                      <span className={t.className}>{t.label}</span>
                      <h3>{r.title}</h3>
                    </div>
                    <p className="record-content">{r.content}</p>
                    <p className="muted record-meta">
                      {r.record_date ?? "بدون تاريخ"} · المصدر:{" "}
                      {r.source === "ocr" ? "مسح ضوئي (OCR)" : "إدخال يدوي"}
                    </p>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
