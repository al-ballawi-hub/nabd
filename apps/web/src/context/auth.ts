import { createContext, useContext } from "react";

export type Role = "doctor" | "patient";

export type User = {
  role: Role;
  name: string;
};

export type AuthState = {
  user: User | null;
  login: (user: User) => void;
  logout: () => void;
};

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
