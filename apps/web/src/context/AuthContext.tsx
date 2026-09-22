import { useState, type ReactNode } from "react";
import { AuthContext, SESSION_STORAGE_KEY, type User } from "./auth";

type Session = { user: User; token: string };

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(() => {
    try {
      const saved = localStorage.getItem(SESSION_STORAGE_KEY);
      return saved ? (JSON.parse(saved) as Session) : null;
    } catch {
      return null;
    }
  });

  const login = async (user: User) => {
    const r = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(user),
    });
    if (!r.ok) throw new Error("Login failed");
    const data = await r.json();
    const next: Session = {
      user: { name: data.name, role: data.role },
      token: data.access_token,
    };
    setSession(next);
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(next));
  };

  const logout = () => {
    setSession(null);
    localStorage.removeItem(SESSION_STORAGE_KEY);
  };

  return (
    <AuthContext.Provider
      value={{
        user: session?.user ?? null,
        token: session?.token ?? null,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
