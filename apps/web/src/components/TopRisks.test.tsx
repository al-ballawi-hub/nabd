import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../test/utils";
import TopRisks from "./TopRisks";

const { mockApiFetch } = vi.hoisted(() => ({ mockApiFetch: vi.fn() }));

vi.mock("../lib/api", () => ({
  apiFetch: mockApiFetch,
}));

const highRisk = {
  chronicConditions: ["Type 2 Diabetes", "Hypertension"],
  allergies: ["Penicillin"],
  abnormalLabs: [{ title: "HbA1c", date: "2026-07-15", detail: "8.4%" }],
  hereditaryRisks: ["Father: Type 2 Diabetes (deceased)"],
  riskLevel: "high",
};

describe("TopRisks", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
  });

  it("renders the risk level badge", async () => {
    mockApiFetch.mockResolvedValue({ ok: true, json: async () => highRisk });
    renderWithProviders(<TopRisks patientId="1" />);
    expect(await screen.findByText("high")).toBeInTheDocument();
  });

  it("renders chronic conditions and allergies", async () => {
    mockApiFetch.mockResolvedValue({ ok: true, json: async () => highRisk });
    renderWithProviders(<TopRisks patientId="1" />);
    expect(await screen.findByText("Type 2 Diabetes")).toBeInTheDocument();
    expect(screen.getByText("Penicillin")).toBeInTheDocument();
  });

  it("renders hereditary risks with a ⚠️ warning flag", async () => {
    mockApiFetch.mockResolvedValue({ ok: true, json: async () => highRisk });
    renderWithProviders(<TopRisks patientId="1" />);
    const el = await screen.findByText(/Father: Type 2 Diabetes/);
    expect(el.textContent).toContain("⚠️");
  });

  it("renders recent abnormal findings", async () => {
    mockApiFetch.mockResolvedValue({ ok: true, json: async () => highRisk });
    renderWithProviders(<TopRisks patientId="1" />);
    expect(await screen.findByText("HbA1c")).toBeInTheDocument();
  });

  it("shows 'None reported' for empty allergies and conditions", async () => {
    mockApiFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        chronicConditions: [],
        allergies: [],
        abnormalLabs: [],
        hereditaryRisks: [],
        riskLevel: "low",
      }),
    });
    renderWithProviders(<TopRisks patientId="1" />);
    expect(await screen.findAllByText("None reported")).toHaveLength(2);
  });
});
