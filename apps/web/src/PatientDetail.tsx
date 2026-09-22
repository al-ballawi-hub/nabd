import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

type Patient = {
  id: number;
  name: string;
  age: number | null;
  gender: string | null;
  bloodType: string | null;
  allergies: string;
  chronicConditions: string;
};

type MedicalRecord = {
  id: number;
  patientId: number;
  recordType: string;
  title: string;
  content: string;
  source: string;
  recordDate: string | null;
};

const RECORD_TYPES: Record<string, { label: string; className: string }> = {
  lab: { label: "تحليل مخبري", className: "bg-teal-100 text-teal-900" },
  prescription: { label: "وصفة طبية", className: "bg-blue-100 text-blue-800" },
  report: { label: "تقرير", className: "bg-amber-100 text-amber-800" },
  scan: { label: "أشعة", className: "bg-red-100 text-red-800" },
};

const split = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

export default function PatientDetail() {
  const { id } = useParams();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [text, setText] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");

  const loadRecords = useCallback(async () => {
    const r = await fetch(`/api/v1/patients/${id}/records`);
    if (!r.ok) throw new Error("failed to load records");
    return (await r.json()) as MedicalRecord[];
  }, [id]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`/api/v1/patients/${id}`).then((r) =>
        r.ok ? r.json() : Promise.reject()
      ),
      loadRecords(),
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
  }, [id, loadRecords]);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setAnalyzing(true);
    setAnalyzeError("");
    try {
      const r = await fetch(`/api/v1/patients/${id}/records/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!r.ok) throw new Error("analysis failed");
      const recs = await loadRecords();
      setRecords(recs);
      setText("");
    } catch {
      setAnalyzeError("تعذر تحليل النص — تأكد من تشغيل الخادم");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex flex-wrap items-center justify-between gap-4 bg-gradient-to-br from-teal-600 to-teal-800 px-10 py-8 text-white">
        <div>
          <h1 className="text-4xl font-bold tracking-wide">نَبْض</h1>
          <p className="mt-1 opacity-90">ملف المريض — Patient Profile</p>
        </div>
        <Link className="rounded-xl bg-white px-6 py-3 font-semibold text-teal-800 no-underline transition-transform hover:-translate-y-0.5" to="/">
          العودة للقائمة
        </Link>
      </header>

      <main className="mx-auto my-8 w-full max-w-5xl flex-1 px-6">
        {loading && <p className="text-slate-500">جارٍ التحميل...</p>}
        {error && (
          <p className="rounded-xl bg-red-100 px-4 py-3 text-red-700">{error}</p>
        )}

        {!loading && !error && patient && (
          <>
            <div className="mb-8 rounded-2xl border border-teal-100 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold">{patient.name}</h2>
              <p className="mt-1 text-slate-500">
                {patient.age} سنة · {patient.gender} · فصيلة الدم{" "}
                {patient.bloodType}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-teal-700">
                  الحساسية:
                </span>
                {split(patient.allergies).map((a) => (
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
                {split(patient.chronicConditions).map((c) => (
                  <span
                    className="rounded-full bg-teal-100 px-3 py-0.5 text-sm text-teal-900"
                    key={c}
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>

            <div className="mb-8 rounded-2xl border border-teal-100 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-teal-700">
                تحليل نص طبي بالذكاء الاصطناعي
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                الصق ملاحظات التقرير الطبي وسيقوم النظام بتحليلها وحفظها كسجل
                منظم.
              </p>
              <textarea
                className="mt-3 w-full rounded-xl border border-teal-200 p-3 text-slate-800 focus:border-teal-500 focus:outline-none"
                rows={4}
                placeholder="الصق نص التقرير الطبي هنا..."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              <button
                className="mt-3 rounded-xl bg-teal-600 px-6 py-2.5 font-semibold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={handleAnalyze}
                disabled={analyzing || !text.trim()}
              >
                {analyzing ? "جارٍ التحليل..." : "تحليل النص"}
              </button>
              {analyzeError && (
                <p className="mt-2 text-sm text-red-700">{analyzeError}</p>
              )}
            </div>

            <h2 className="mb-4 text-xl font-semibold text-teal-700">
              السجلات الطبية ({records.length})
            </h2>
            {records.length === 0 && (
              <p className="text-slate-500">لا توجد سجلات طبية لهذا المريض.</p>
            )}

            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {records.map((r) => {
                const t = RECORD_TYPES[r.recordType] ?? {
                  label: r.recordType,
                  className: "bg-teal-100 text-teal-900",
                };
                return (
                  <div
                    className="flex flex-col gap-2 rounded-2xl border border-teal-100 bg-white p-5 shadow-sm"
                    key={r.id}
                  >
                    <div className="flex flex-col items-start gap-1">
                      <span
                        className={`rounded-full px-3 py-0.5 text-sm ${t.className}`}
                      >
                        {t.label}
                      </span>
                      <h3 className="text-base font-semibold">{r.title}</h3>
                    </div>
                    <p className="leading-relaxed text-slate-800">{r.content}</p>
                    <p className="text-xs text-slate-500">
                      {r.recordDate ?? "بدون تاريخ"} · المصدر:{" "}
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
