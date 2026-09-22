import { createContext, useContext } from "react";

export type Role = "doctor" | "patient";

export type User = {
  role: Role;
  name: string;
};

export type AuthState = {
  user: User | null;
  token: string | null;
  login: (user: User) => Promise<void>;
  logout: () => void;
};

export const SESSION_STORAGE_KEY = "nabd.session";

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
