import { useCallback, useEffect, useState } from "react";
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

  const load = useCallback(() => {
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
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const seed = () => {
    fetch("/api/v1/seed", { method: "POST" }).then(load);
  };

  const split = (s: string) =>
    s.split(",").map((x) => x.trim()).filter(Boolean);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex flex-wrap items-center justify-between gap-4 bg-gradient-to-br from-teal-600 to-teal-800 px-10 py-8 text-white">
        <div>
          <h1 className="text-4xl font-bold tracking-wide">نَبْض</h1>
          <p className="mt-1 opacity-90">
            منصة المراجعة الطبية الذكية — Smart Medical Review AI
          </p>
        </div>
        <button
          className="rounded-xl bg-white px-6 py-3 font-semibold text-teal-800 transition-transform hover:-translate-y-0.5"
          onClick={seed}
        >
          توليد بيانات تجريبية
        </button>
      </header>

      <main className="mx-auto my-8 w-full max-w-5xl flex-1 px-6">
        {loading && <p className="text-slate-500">جارٍ التحميل...</p>}
        {error && (
          <p className="rounded-xl bg-red-100 px-4 py-3 text-red-700">{error}</p>
        )}
        {!loading && !error && patients.length === 0 && (
          <p className="text-slate-500">
            لا توجد بيانات — اضغط زر "توليد بيانات تجريبية"
          </p>
        )}

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {patients.map((p) => (
            <Link
              className="block rounded-2xl border border-teal-100 bg-white p-5 text-inherit no-underline shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg"
              to={`/patients/${p.id}`}
              key={p.id}
            >
              <h2 className="mb-1 text-lg font-semibold">{p.name}</h2>
              <p className="text-slate-500">
                {p.age} سنة · {p.gender} · فصيلة الدم {p.bloodType}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-teal-700">
                  الحساسية:
                </span>
                {split(p.allergies).map((a) => (
                  <span
                    className="rounded-full bg-red-100 px-3 py-0.5 text-sm text-red-800"
                    key={a}
                  >
                    {a}
                  </span>
                ))}
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-teal-700">
                  أمراض مزمنة:
                </span>
                {split(p.chronicConditions).map((c) => (
                  <span
                    className="rounded-full bg-teal-100 px-3 py-0.5 text-sm text-teal-900"
                    key={c}
                  >
                    {c}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      </main>

      <footer className="py-8 text-center text-sm text-slate-500">
        مشروع تخرج — قسم هندسة البرمجيات، جامعة حائل · جميع البيانات تجريبية وهمية
      </footer>
    </div>
  );
}
