import type { ReactNode } from "react";
import { DoctorContext, type Doctor } from "./doctor";

const ACTIVE_DOCTOR: Doctor = {
  name: "Dr. Ahmad Alshomar",
  title: "Attending Physician",
  specialty: "Internal Medicine",
  initials: "AA",
};

export function DoctorProvider({ children }: { children: ReactNode }) {
  return (
    <DoctorContext.Provider value={ACTIVE_DOCTOR}>
      {children}
    </DoctorContext.Provider>
  );
}
