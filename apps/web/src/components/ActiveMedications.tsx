import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useAuth } from "../context/auth";
import { apiFetch } from "../lib/api";

type Medication = {
  id: number;
  name: string;
  status: string;
  dosage: string | null;
  startedOn: string | null;
};

export default function ActiveMedications({ patientId }: { patientId: string }) {
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [dosage, setDosage] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["medications", patientId],
    queryFn: async () => {
      const r = await apiFetch(`/api/v1/patients/${patientId}/medications`);
      if (!r.ok) throw new Error("Failed to load medications");
      return (await r.json()) as Medication[];
    },
  });

  const addMutation = useMutation({
    mutationFn: async (vars: { name: string; dosage: string }) => {
      const r = await apiFetch(`/api/v1/patients/${patientId}/medications`, {
        method: "POST",
        body: JSON.stringify(vars),
      });
      if (!r.ok) throw new Error("Failed to add medication");
    },
    onSuccess: () => {
      setName("");
      setDosage("");
      queryClient.invalidateQueries({ queryKey: ["medications", patientId] });
      queryClient.invalidateQueries({ queryKey: ["risks", patientId] });
    },
  });

  const stopMutation = useMutation({
    mutationFn: async (medId: number) => {
      const r = await apiFetch(
        `/api/v1/patients/${patientId}/medications/${medId}/stop`,
        { method: "POST" }
      );
      if (!r.ok) throw new Error("Failed to stop medication");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["medications", patientId] });
      queryClient.invalidateQueries({ queryKey: ["risks", patientId] });
    },
  });

  const add = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    addMutation.mutate({ name, dosage });
  };

  const medications = data ?? [];
  const active = medications.filter((m) => m.status === "active");

  return (
    <div className="rounded-3xl border border-white/50 bg-white/80 p-6 shadow-xl shadow-teal-900/5 backdrop-blur-md">
      <h2 className="text-lg font-bold text-slate-800">Active Medications</h2>
      {isError && (
        <p className="mt-2 text-red-600">Unable to load medications.</p>
      )}
      {isLoading && <p className="mt-2 text-slate-600">Loading…</p>}

      {!isLoading && !isError && active.length === 0 && (
        <p className="mt-2 text-slate-600">No active medications.</p>
      )}

      <div className="mt-3 space-y-2">
        {active.map((m) => (
          <div
            key={m.id}
            className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white/70 p-3"
          >
            <div>
              <p className="font-semibold text-slate-800">{m.name}</p>
              <p className="text-xs text-slate-500">{m.dosage ?? "No dosage"}</p>
            </div>
            {isDoctor && (
              <button
                onClick={() => stopMutation.mutate(m.id)}
                className="rounded-xl bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-200 active:scale-95"
              >
                Stop
              </button>
            )}
          </div>
        ))}
      </div>

      {isDoctor && (
        <form onSubmit={add} className="mt-4 flex flex-wrap items-end gap-2">
          <div className="min-w-40 flex-1">
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Medication name
            </label>
            <input
              className="w-full rounded-xl border border-teal-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:outline-none"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={120}
              placeholder="e.g. Metformin"
            />
          </div>
          <div className="w-32">
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Dosage
            </label>
            <input
              className="w-full rounded-xl border border-teal-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:outline-none"
              value={dosage}
              onChange={(e) => setDosage(e.target.value)}
              maxLength={100}
              placeholder="850 mg"
            />
          </div>
          <button
            type="submit"
            disabled={!name.trim() || addMutation.isPending}
            className="rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-teal-700 active:scale-95 disabled:opacity-60"
          >
            {addMutation.isPending ? "Adding…" : "Add"}
          </button>
        </form>
      )}
    </div>
  );
}
