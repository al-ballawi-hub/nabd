import { Link } from "react-router-dom";
import { useDoctor } from "../context/doctor";

export default function TopNav() {
  const doctor = useDoctor();

  return (
    <nav className="sticky top-0 z-50 border-b border-white/20 bg-white/10 backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-3 no-underline">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 text-xl font-bold text-white shadow-lg shadow-teal-900/30">
            N
          </span>
          <div>
            <p className="text-lg font-bold leading-tight text-white">Nabd</p>
            <p className="text-xs text-white/70">Smart Medical Review</p>
          </div>
        </Link>

        <div className="flex items-center gap-3 rounded-2xl border border-white/20 bg-white/10 px-4 py-2 shadow-lg shadow-teal-900/10 backdrop-blur-md">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-teal-600 text-sm font-bold text-white shadow-md">
            {doctor.initials}
          </span>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold leading-tight text-white">
              {doctor.name}
            </p>
            <p className="text-xs text-white/70">
              {doctor.title} · {doctor.specialty}
            </p>
          </div>
        </div>
      </div>
    </nav>
  );
}
