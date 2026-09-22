import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type ChangeEvent } from "react";
import { Link, useParams } from "react-router-dom";
import ActiveMedications from "./components/ActiveMedications";
import FamilyTree from "./components/FamilyTree";
import TopNav from "./components/TopNav";
import TopRisks from "./components/TopRisks";
import { useAuth } from "./context/auth";
import { apiFetch, type ConflictItem, type Page } from "./lib/api";

type Patient = {
  id: number;
  name: string;
  age: number | null;
  gender: string | null;
  bloodType: string | null;
  allergies: string[];
  chronicConditions: string[];
};

type MedicalRecord = {
  id: number;
  patientId: number;
  recordType: string;
  title: string;
  content: string;
  source: string;
  recordDate: string | null;
  createdBy: string | null;
};

type AnalysisResult = {
  saved: boolean;
  conflicts: ConflictItem[];
  recordType: string;
  title: string;
  content: string;
};

const RECORD_TYPES: Record<string, { label: string; className: string }> = {
  lab: { label: "Lab Test", className: "bg-teal-100 text-teal-800" },
  prescription: { label: "Prescription", className: "bg-blue-100 text-blue-800" },
  report: { label: "Report", className: "bg-amber-100 text-amber-800" },
  scan: { label: "Imaging / Scan", className: "bg-red-100 text-red-800" },
};

const SEVERITY_STYLES: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  moderate: "bg-amber-100 text-amber-700",
  low: "bg-emerald-100 text-emerald-700",
};

const CONFLICT_TYPE_LABELS: Record<string, string> = {
  "drug-drug": "Drug-Drug",
  "drug-disease": "Drug-Disease",
  allergy: "Allergy",
  duplicate: "Duplicate",
};

const MAX_TEXT_LENGTH = 5000;

export default function PatientDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";
  const queryClient = useQueryClient();

  const [text, setText] = useState("");
  const [safetyWarnings, setSafetyWarnings] = useState<ConflictItem[]>([]);
  const [ocrUploading, setOcrUploading] = useState(false);
  const [ocrError, setOcrError] = useState("");
  const [ocrFileName, setOcrFileName] = useState<string | null>(null);

  const patientQuery = useQuery({
    queryKey: ["patient", id],
    queryFn: async () => {
      const r = await apiFetch(`/api/v1/patients/${id}`);
      if (!r.ok) throw new Error("Failed to load patient");
      return (await r.json()) as Patient;
    },
  });

  const recordsQuery = useQuery({
    queryKey: ["records", id],
    queryFn: async () => {
      const r = await apiFetch(`/api/v1/patients/${id}/records`);
      if (!r.ok) throw new Error("Failed to load records");
      return (await r.json()) as Page<MedicalRecord>;
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: async (vars: { text: string; override: boolean }) => {
      const r = await apiFetch(`/api/v1/patients/${id}/records/text`, {
        method: "POST",
        body: JSON.stringify(vars),
      });
      if (!r.ok) throw new Error("Analysis failed");
      return (await r.json()) as AnalysisResult;
    },
    onSuccess: (result) => {
      if (result.saved) {
        setText("");
        setSafetyWarnings([]);
        queryClient.invalidateQueries({ queryKey: ["records", id] });
        queryClient.invalidateQueries({ queryKey: ["medications", id] });
        queryClient.invalidateQueries({ queryKey: ["risks", id] });
      } else {
        setSafetyWarnings(result.conflicts ?? []);
      }
    },
  });

  const handleAnalyze = (override = false) => {
    if (!text.trim()) return;
    analyzeMutation.mutate({ text, override });
  };

  const handleOcrUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!["image/png", "image/jpeg"].includes(file.type)) {
      setOcrError("Only PNG and JPEG images are supported.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setOcrError("File exceeds the 10 MB limit.");
      return;
    }
    setOcrUploading(true);
    setOcrError("");
    setOcrFileName(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const r = await apiFetch(`/api/v1/patients/${id}/records/ocr`, {
        method: "POST",
        body: formData,
      });
      if (!r.ok) throw new Error("OCR failed");
      const data = (await r.json()) as { extractedText: string };
      setText(data.extractedText);
      setOcrFileName(file.name);
    } catch {
      setOcrError("Failed to extract text from the image.");
    } finally {
      setOcrUploading(false);
    }
  };

  const patient = patientQuery.data;
  const records = recordsQuery.data?.items ?? [];
  const loading = patientQuery.isLoading || recordsQuery.isLoading;
  const error = patientQuery.error ?? recordsQuery.error;

  return (
    <div className="min-h-screen">
      <TopNav />

      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        {loading && <p className="font-medium text-teal-50">Loading…</p>}
        {error && (
          <p className="rounded-xl bg-red-500/20 px-4 py-3 text-red-100">
            {error instanceof Error ? error.message : "Unable to load patient data."}
          </p>
        )}

        {!loading && !error && patient && (
          <>
            <div className="mb-8 rounded-3xl border border-white/50 bg-white/80 p-6 shadow-xl shadow-teal-900/5 backdrop-blur-md">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-slate-800">
                    {patient.name}
                  </h1>
                  <p className="mt-1 text-slate-600">
                    {patient.age} yrs · {patient.gender} · Blood Type{" "}
                    {patient.bloodType}
                  </p>
                </div>
                <Link
                  to="/"
                  className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-teal-700 no-underline shadow transition-transform hover:-translate-y-0.5 active:scale-95"
                >
                  ← Back to patients
                </Link>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-teal-700">
                  Allergies
                </span>
                {patient.allergies.length === 0 ? (
                  <span className="text-xs text-slate-500">None</span>
                ) : (
                  patient.allergies.map((a) => (
                    <span
                      className="rounded-full bg-red-100 px-3 py-0.5 text-xs font-medium text-red-700"
                      key={a}
                    >
                      {a}
                    </span>
                  ))
                )}
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-teal-700">
                  Chronic Conditions
                </span>
                {patient.chronicConditions.length === 0 ? (
                  <span className="text-xs text-slate-500">None</span>
                ) : (
                  patient.chronicConditions.map((c) => (
                    <span
                      className="rounded-full bg-teal-100 px-3 py-0.5 text-xs font-medium text-teal-800"
                      key={c}
                    >
                      {c}
                    </span>
                  ))
                )}
              </div>
            </div>

            <div className="mb-8">
              <TopRisks patientId={id!} />
            </div>

            <div className="mb-8">
              <ActiveMedications patientId={id!} />
            </div>

            {safetyWarnings.length > 0 && (
              <div className="warning-glow mb-8 rounded-3xl border border-red-300/60 bg-red-50/95 p-6 backdrop-blur-md">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">⚠️</span>
                  <h2 className="text-lg font-bold text-red-700">
                    AI Safety Alert — Review Required
                  </h2>
                </div>
                <p className="mt-1 text-sm text-red-600">
                  This record triggers the following concerns against the
                  patient's profile:
                </p>
                <ul className="mt-3 space-y-2">
                  {safetyWarnings.map((w) => (
                    <li
                      key={w.type + w.message}
                      className="flex items-start gap-2 text-sm text-red-700"
                    >
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-bold uppercase ${
                          SEVERITY_STYLES[w.severity] ??
                          "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {w.severity}
                      </span>
                      <span>
                        <span className="font-semibold">
                          {CONFLICT_TYPE_LABELS[w.type] ?? w.type}:
                        </span>{" "}
                        {w.message}
                      </span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    className="rounded-2xl bg-red-600 px-5 py-2.5 font-semibold text-white shadow-lg shadow-red-600/30 transition-transform hover:-translate-y-0.5 active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
                    onClick={() => handleAnalyze(true)}
                    disabled={analyzeMutation.isPending}
                  >
                    {analyzeMutation.isPending ? "Saving…" : "Override & Approve"}
                  </button>
                  <button
                    className="rounded-2xl bg-white px-5 py-2.5 font-semibold text-slate-600 shadow transition-transform hover:-translate-y-0.5 active:scale-95"
                    onClick={() => setSafetyWarnings([])}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {isDoctor && (
              <div className="mb-8 rounded-3xl border border-white/50 bg-white/80 p-6 shadow-xl shadow-teal-900/5 backdrop-blur-md">
                <h2 className="text-lg font-bold text-teal-700">
                  AI Record Analysis
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                  Upload a scanned record (PNG/JPEG) to extract its text, then
                  review and edit it before submitting for AI analysis.
                </p>

                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <label className="inline-flex cursor-pointer items-center gap-2 rounded-2xl border border-teal-200 bg-white px-4 py-2 text-sm font-semibold text-teal-700 shadow-sm transition hover:bg-teal-50 active:scale-95">
                    {ocrUploading ? "Extracting…" : "Upload Scanned Record"}
                    <input
                      type="file"
                      accept="image/png,image/jpeg"
                      className="hidden"
                      onChange={handleOcrUpload}
                      disabled={ocrUploading}
                    />
                  </label>
                  {ocrFileName && (
                    <span className="text-sm text-slate-600">
                      Extracted from{" "}
                      <span className="font-semibold">{ocrFileName}</span>
                    </span>
                  )}
                </div>
                {ocrError && (
                  <p className="mt-2 text-sm text-red-600">{ocrError}</p>
                )}

                <textarea
                  className="mt-3 w-full rounded-2xl border border-teal-200 bg-white/70 p-3 text-slate-800 focus:border-teal-500 focus:outline-none"
                  rows={4}
                  placeholder="Extracted text appears here for review and editing…"
                  value={text}
                  maxLength={MAX_TEXT_LENGTH}
                  onChange={(e) => setText(e.target.value)}
                />
                <div className="mt-1 text-right text-xs text-slate-500">
                  {text.length} / {MAX_TEXT_LENGTH}
                </div>
                <button
                  className="mt-3 rounded-2xl bg-gradient-to-br from-teal-600 to-emerald-600 px-6 py-2.5 font-semibold text-white shadow-lg shadow-teal-900/20 transition-transform hover:-translate-y-0.5 active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
                  onClick={() => handleAnalyze(false)}
                  disabled={analyzeMutation.isPending || !text.trim()}
                >
                  {analyzeMutation.isPending ? "Analyzing…" : "Analyze Text"}
                </button>
                {analyzeMutation.isError && (
                  <p className="mt-2 text-sm text-red-600">
                    Text analysis failed — please ensure the server is running.
                  </p>
                )}
              </div>
            )}

            <div className="mb-8">
              <FamilyTree patientId={id!} />
            </div>

            <h2 className="mb-4 text-xl font-bold text-white drop-shadow">
              Medical Records ({records.length})
            </h2>
            {records.length === 0 && (
              <p className="font-medium text-teal-50">
                No medical records for this patient.
              </p>
            )}

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {records.map((r) => {
                const t = RECORD_TYPES[r.recordType] ?? {
                  label: r.recordType,
                  className: "bg-teal-100 text-teal-800",
                };
                return (
                  <div
                    className="flex flex-col gap-2 rounded-3xl border border-white/50 bg-white/80 p-6 shadow-xl shadow-teal-900/5 backdrop-blur-md"
                    key={r.id}
                  >
                    <div className="flex flex-col items-start gap-1">
                      <span
                        className={`rounded-full px-3 py-0.5 text-xs font-medium ${t.className}`}
                      >
                        {t.label}
                      </span>
                      <h3 className="text-base font-semibold text-slate-800">
                        {r.title}
                      </h3>
                    </div>
                    <p className="leading-relaxed text-slate-700">{r.content}</p>
                    <p className="text-xs text-slate-500">
                      {r.recordDate ?? "No date"} · Source:{" "}
                      {r.source === "ocr" ? "OCR Scan" : "Manual Entry"}
                      {r.createdBy ? ` · By ${r.createdBy}` : ""}
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
