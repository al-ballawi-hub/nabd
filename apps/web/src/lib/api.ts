import { SESSION_STORAGE_KEY } from "../context/auth";

type Session = { user: { name: string; role: string }; token: string };

export function getToken(): string | null {
  try {
    const saved = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!saved) return null;
    return (JSON.parse(saved) as Session).token ?? null;
  } catch {
    return null;
  }
}

/** `fetch` wrapper that attaches the stored JWT and sets JSON content type. */
export function apiFetch(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(path, { ...init, headers });
}
