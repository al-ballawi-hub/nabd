import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { AuthContext, type AuthState } from "../context/auth";

export const doctorAuth: AuthState = {
  user: { role: "doctor", name: "Dr. Test" },
  token: "test-token",
  login: async () => {},
  logout: () => {},
};

/** Render a component wrapped in the providers it needs (auth + react-query). */
export function renderWithProviders(
  ui: ReactElement,
  auth: AuthState = doctorAuth,
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <AuthContext.Provider value={auth}>
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    </AuthContext.Provider>,
  );
}
