import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import TopNav from "./components/TopNav";
import { useAuth } from "./context/auth";
import { apiFetch, type Page } from "./lib/api";

type Patient = {
  id: number;
  name: string;
  age: number | null;
  gender: string | null;
  bloodType: string | null;
  allergies: string[];
  chronicConditions: string[];
};

export default function App() {
  const { user } = useAuth();
  const isDoctor = user?.role === "doctor";
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["patients"],
    queryFn: async () => {
      const r = await apiFetch("/api/v1/patients");
      if (!r.ok) throw new Error("Failed to load patients");
      return (await r.json()) as Page<Patient>;
    },
  });

  const seedMutation = useMutation({
    mutationFn: async () => {
      const r = await apiFetch("/api/v1/seed", { method: "POST" });
      if (!r.ok) throw new Error("Failed to generate demo data");
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["patients"] }),
  });

  const patients = data?.items ?? [];

  return (
    <div className="min-h-screen">
      <TopNav />

      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white drop-shadow-lg">
              Patient Directory
            </h1>
            <p className="mt-1 font-medium text-teal-50">
              Review and manage your patients' medical records.
            </p>
          </div>
          {isDoctor && (
            <button
              className="rounded-2xl bg-white/90 px-6 py-3 font-semibold text-teal-700 shadow-xl shadow-teal-900/20 backdrop-blur transition-transform hover:-translate-y-0.5 active:scale-95 disabled:opacity-60"
              onClick={() => seedMutation.mutate()}
              disabled={seedMutation.isPending}
            >
              {seedMutation.isPending ? "Generating…" : "Generate Demo Data"}
            </button>
          )}
        </div>

        {isLoading && <p className="font-medium text-teal-50">Loading…</p>}
        {isError && (
          <p className="rounded-xl bg-red-500/20 px-4 py-3 text-red-100">
            {error instanceof Error ? error.message : "Something went wrong."}
          </p>
        )}
        {!isLoading && !isError && patients.length === 0 && (
          <p className="font-medium text-teal-50">
            No data yet — press "Generate Demo Data".
          </p>
        )}

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {patients.map((p) => (
            <Link
              className="block rounded-3xl border border-white/50 bg-white/80 p-6 text-inherit no-underline shadow-xl shadow-teal-900/5 backdrop-blur-md transition-all hover:-translate-y-1 hover:bg-white/90 hover:shadow-2xl hover:shadow-teal-900/10"
              to={`/patients/${p.id}`}
              key={p.id}
            >
              <h2 className="mb-1 text-lg font-bold text-slate-800">
                {p.name}
              </h2>
              <p className="text-sm text-slate-600">
                {p.age} yrs · {p.gender} · Blood {p.bloodType}
              </p>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-teal-700">
                  Allergies
                </span>
                {p.allergies.length === 0 ? (
                  <span className="text-xs text-slate-500">None</span>
                ) : (
                  p.allergies.map((a) => (
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
                  Conditions
                </span>
                {p.chronicConditions.length === 0 ? (
                  <span className="text-xs text-slate-500">None</span>
                ) : (
                  p.chronicConditions.map((c) => (
                    <span
                      className="rounded-full bg-teal-100 px-3 py-0.5 text-xs font-medium text-teal-800"
                      key={c}
                    >
                      {c}
                    </span>
                  ))
                )}
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
