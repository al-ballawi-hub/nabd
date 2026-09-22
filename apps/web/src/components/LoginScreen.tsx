import { useState, type FormEvent } from "react";
import { useAuth, type Role } from "../context/auth";

export default function LoginScreen() {
  const { login } = useAuth();
  const [role, setRole] = useState<Role>("doctor");
  const [name, setName] = useState("Dr. Ahmad Alshomar");

  const handleRole = (r: Role) => {
    setRole(r);
    setName(r === "doctor" ? "Dr. Ahmad Alshomar" : "");
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    login({ role, name: name.trim() });
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <form
        onSubmit={submit}
        className="w-full max-w-md rounded-3xl border border-white/50 bg-white/85 p-8 shadow-2xl shadow-teal-900/20 backdrop-blur-md"
      >
        <div className="mb-6 text-center">
          <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 text-2xl font-bold text-white shadow-lg">
            N
          </span>
          <h1 className="mt-3 text-3xl font-bold text-teal-700">Nabd</h1>
          <p className="mt-1 text-slate-600">
            Sign in to the smart medical review platform
          </p>
        </div>

        <div className="mb-4 grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => handleRole("doctor")}
            className={`rounded-2xl px-4 py-3 text-sm font-semibold transition active:scale-95 ${
              role === "doctor"
                ? "bg-teal-600 text-white shadow-lg"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Doctor
          </button>
          <button
            type="button"
            onClick={() => handleRole("patient")}
            className={`rounded-2xl px-4 py-3 text-sm font-semibold transition active:scale-95 ${
              role === "patient"
                ? "bg-teal-600 text-white shadow-lg"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Patient
          </button>
        </div>

        <label className="mb-1 block text-sm font-semibold text-slate-700">
          Full name
        </label>
        <input
          className="w-full rounded-2xl border border-teal-200 bg-white px-4 py-3 text-slate-800 focus:border-teal-500 focus:outline-none"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter your name"
          maxLength={120}
        />

        <button
          type="submit"
          className="mt-6 w-full rounded-2xl bg-gradient-to-br from-teal-600 to-emerald-600 px-6 py-3 font-semibold text-white shadow-lg shadow-teal-900/20 transition hover:-translate-y-0.5 active:scale-95"
        >
          Sign In
        </button>

        <p className="mt-4 text-center text-xs text-slate-500">
          Simulated session — role-based access for demonstration purposes.
        </p>
      </form>
    </div>
  );
}
