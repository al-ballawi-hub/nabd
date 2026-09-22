import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../context/auth";

type FamilyMember = {
  id: number;
  patientId: number;
  relation: string;
  name: string | null;
  gender: string | null;
  age: number | null;
  deceased: boolean;
  conditions: string;
};

const HEREDITARY_FLAGS = [
  "diabetes",
  "hypertension",
  "cancer",
  "heart",
  "cardiac",
  "coronary",
  "stroke",
  "asthma",
  "alzheimer",
  "parkinson",
  "thyroid",
];

const split = (s: string) =>
  s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean)
    .filter((x) => x.toLowerCase() !== "none");

export default function FamilyTree({ patientId }: { patientId: string }) {
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";

  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [error, setError] = useState("");
  const [relation, setRelation] = useState("");
  const [name, setName] = useState("");
  const [conditions, setConditions] = useState("");

  const load = useCallback(() => {
    fetch(`/api/v1/patients/${patientId}/family`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: FamilyMember[]) => setMembers(d))
      .catch(() => setError("Unable to load family history."));
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  const addMember = async (e: FormEvent) => {
    e.preventDefault();
    if (!relation.trim()) return;
    const r = await fetch(`/api/v1/patients/${patientId}/family`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ relation, name, conditions }),
    });
    if (r.ok) {
      setRelation("");
      setName("");
      setConditions("");
      load();
    }
  };

  return (
    <div className="rounded-3xl border border-white/50 bg-white/80 p-6 shadow-xl shadow-teal-900/5 backdrop-blur-md">
      <h2 className="text-lg font-bold text-slate-800">Family Medical History</h2>
      {error && <p className="mt-2 text-red-600">{error}</p>}

      {members.length === 0 && !error && (
        <p className="mt-2 text-slate-600">No family history recorded.</p>
      )}

      <div className="mt-3 space-y-3">
        {members.map((m) => {
          const flagged = split(m.conditions).filter((c) =>
            HEREDITARY_FLAGS.some((flag) => c.toLowerCase().includes(flag))
          );
          return (
            <div
              key={m.id}
              className="flex items-start justify-between gap-3 rounded-2xl border border-slate-100 bg-white/70 p-4"
            >
              <div>
                <p className="font-semibold text-slate-800">
                  {m.relation.charAt(0).toUpperCase() + m.relation.slice(1)}
                  {m.name ? ` — ${m.name}` : ""}
                </p>
                <p className="text-xs text-slate-500">
                  {m.gender ? `${m.gender}` : ""}
                  {m.age != null ? ` · ${m.age} yrs` : ""}
                  {m.deceased ? " · Deceased" : ""}
                </p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {split(m.conditions).length === 0 ? (
                    <span className="text-xs text-slate-500">No conditions</span>
                  ) : (
                    split(m.conditions).map((c) => (
                      <span
                        key={c}
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          HEREDITARY_FLAGS.some((f) => c.toLowerCase().includes(f))
                            ? "bg-red-100 text-red-700"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {flagged.length > 0 && HEREDITARY_FLAGS.some((f) =>
                          c.toLowerCase().includes(f)
                        )
                          ? "⚠️ "
                          : ""}
                        {c}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {isDoctor && (
        <form
          onSubmit={addMember}
          className="mt-4 rounded-2xl border border-teal-100 bg-teal-50/50 p-4"
        >
          <p className="text-sm font-semibold text-teal-700">
            Add Family Member
          </p>
          <div className="mt-2 grid gap-2 sm:grid-cols-3">
            <input
              className="rounded-xl border border-teal-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:outline-none"
              placeholder="Relation (e.g. father)"
              value={relation}
              onChange={(e) => setRelation(e.target.value)}
              maxLength={50}
            />
            <input
              className="rounded-xl border border-teal-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:outline-none"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={120}
            />
            <input
              className="rounded-xl border border-teal-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:outline-none"
              placeholder="Conditions (comma-separated)"
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              maxLength={500}
            />
          </div>
          <button
            type="submit"
            className="mt-3 rounded-2xl bg-teal-600 px-5 py-2 text-sm font-semibold text-white shadow transition hover:bg-teal-700 active:scale-95 disabled:opacity-60"
            disabled={!relation.trim()}
          >
            Add Member
          </button>
        </form>
      )}
    </div>
  );
}
