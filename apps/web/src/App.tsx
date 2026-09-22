import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

type Patient = {
  id: number;
  name: string;
  age: number | null;
  gender: string | null;
  bloodType: string | null;
  allergies: string;
  chronicConditions: string;
};

export default function App() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    fetch("/api/v1/patients")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Patient[]) => {
        setPatients(d);
        setError("");
        setLoading(false);
      })
      .catch(() => {
        setError("تعذر الاتصال بالخادم — تأكد أن الـ API يعمل على المنفذ 8000");
        setLoading(false);
      });
  };

  useEffect(load, []);

  const seed = () => {
    fetch("/api/v1/seed", { method: "POST" }).then(load);
  };

  const split = (s: string) =>
    s.split(",").map((x) => x.trim()).filter(Boolean);

  return (
    <div>
      <header className="header">
        <div>
          <h1>نَبْض</h1>
          <p className="tagline">منصة المراجعة الطبية الذكية — Smart Medical Review AI</p>
        </div>
        <button className="btn" onClick={seed}>توليد بيانات تجريبية</button>
      </header>

      <main className="container">
        {loading && <p className="muted">جارٍ التحميل...</p>}
        {error && <p className="error">{error}</p>}
        {!loading && !error && patients.length === 0 && (
          <p className="muted">لا توجد بيانات — اضغط زر "توليد بيانات تجريبية"</p>
        )}

        <div className="grid">
          {patients.map((p) => (
            <Link className="card card-link" to={`/patients/${p.id}`} key={p.id}>
              <h2>{p.name}</h2>
              <p className="muted">
                {p.age} سنة · {p.gender} · فصيلة الدم {p.bloodType}
              </p>
              <div className="section">
                <span className="label">الحساسية:</span>
                {split(p.allergies).map((a) => (
                  <span className="chip chip-danger" key={a}>{a}</span>
                ))}
              </div>
              <div className="section">
                <span className="label">أمراض مزمنة:</span>
                {split(p.chronicConditions).map((c) => (
                  <span className="chip" key={c}>{c}</span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      </main>

      <footer className="footer">
        مشروع تخرج — قسم هندسة البرمجيات، جامعة حائل · جميع البيانات تجريبية وهمية
      </footer>
    </div>
  );
}
