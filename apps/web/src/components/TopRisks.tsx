import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type RiskItem = {
  title: string;
  date: string | null;
  detail: string;
};

type RiskSummary = {
  chronicConditions: string[];
  allergies: string[];
  abnormalLabs: RiskItem[];
  hereditaryRisks: string[];
  riskLevel: string;
};

const LEVEL_STYLES: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  moderate: "bg-amber-100 text-amber-700",
  low: "bg-emerald-100 text-emerald-700",
};

export default function TopRisks({ patientId }: { patientId: string }) {
  const [risks, setRisks] = useState<RiskSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch(`/api/v1/patients/${patientId}/risks`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: RiskSummary) => setRisks(d))
      .catch(() => setError("Unable to load risk summary."));
  }, [patientId]);

  if (error) {
    return (
      <div className="rounded-3xl border border-white/50 bg-white/80 p-6 backdrop-blur-md">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }
  if (!risks) {
    return (
      <div className="rounded-3xl border border-white/50 bg-white/80 p-6 backdrop-blur-md">
        <p className="text-slate-600">Loading risk summary…</p>
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-white/50 bg-white/80 p-6 shadow-xl shadow-teal-900/5 backdrop-blur-md">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-slate-800">Top Risks</h2>
        <span
          className={`rounded-full px-3 py-0.5 text-sm font-bold uppercase ${
            LEVEL_STYLES[risks.riskLevel] ?? "bg-slate-100 text-slate-700"
          }`}
        >
          {risks.riskLevel}
        </span>
      </div>

      <div className="mt-4 space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
            Chronic Conditions
          </p>
          <div className="mt-1.5 flex flex-wrap gap-2">
            {risks.chronicConditions.length === 0 ? (
              <span className="text-sm text-slate-500">None reported</span>
            ) : (
              risks.chronicConditions.map((c) => (
                <span
                  key={c}
                  className="rounded-full bg-teal-100 px-3 py-0.5 text-xs font-medium text-teal-800"
                >
                  {c}
                </span>
              ))
            )}
          </div>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
            Allergies
          </p>
          <div className="mt-1.5 flex flex-wrap gap-2">
            {risks.allergies.length === 0 ? (
              <span className="text-sm text-slate-500">None reported</span>
            ) : (
              risks.allergies.map((a) => (
                <span
                  key={a}
                  className="rounded-full bg-red-100 px-3 py-0.5 text-xs font-medium text-red-700"
                >
                  {a}
                </span>
              ))
            )}
          </div>
        </div>

        {risks.abnormalLabs.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
              Recent Abnormal Findings
            </p>
            <ul className="mt-1.5 space-y-1">
              {risks.abnormalLabs.map((lab) => (
                <li key={lab.title + lab.date} className="text-sm text-slate-700">
                  <span className="font-semibold">{lab.title}</span>
                  {lab.date && (
                    <span className="text-slate-500"> · {lab.date}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {risks.hereditaryRisks.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
              Hereditary Risks
            </p>
            <ul className="mt-1.5 space-y-1">
              {risks.hereditaryRisks.map((r) => (
                <li key={r} className="text-sm text-slate-700">
                  ⚠️ {r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
