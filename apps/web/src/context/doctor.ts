import { createContext, useContext } from "react";

export type Doctor = {
  name: string;
  title: string;
  specialty: string;
  initials: string;
};

export const DoctorContext = createContext<Doctor | null>(null);

export function useDoctor(): Doctor {
  const ctx = useContext(DoctorContext);
  if (!ctx) {
    throw new Error("useDoctor must be used within a DoctorProvider");
  }
  return ctx;
}
