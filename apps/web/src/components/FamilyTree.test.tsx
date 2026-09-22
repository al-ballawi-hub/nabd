import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../test/utils";
import FamilyTree from "./FamilyTree";

const { mockApiFetch } = vi.hoisted(() => ({ mockApiFetch: vi.fn() }));

vi.mock("../lib/api", () => ({
  apiFetch: mockApiFetch,
}));

const family = {
  items: [
    {
      id: 1,
      patientId: 1,
      relation: "father",
      name: "Mohammed",
      gender: "Male",
      age: 78,
      deceased: true,
      conditions: ["Type 2 Diabetes", "Coronary Artery Disease"],
    },
    {
      id: 2,
      patientId: 1,
      relation: "mother",
      name: "Fatimah",
      gender: "Female",
      age: 72,
      deceased: false,
      conditions: ["Hypertension"],
    },
  ],
  total: 2,
  limit: 20,
  offset: 0,
};

describe("FamilyTree", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
  });

  it("renders family members with relation and name", async () => {
    mockApiFetch.mockResolvedValue({ ok: true, json: async () => family });
    renderWithProviders(<FamilyTree patientId="1" />);
    expect(await screen.findByText(/Father/)).toBeInTheDocument();
    expect(screen.getByText(/Mohammed/)).toBeInTheDocument();
    expect(screen.getByText(/Mother/)).toBeInTheDocument();
  });

  it("renders a ⚠️ flag on hereditary conditions", async () => {
    mockApiFetch.mockResolvedValue({ ok: true, json: async () => family });
    renderWithProviders(<FamilyTree patientId="1" />);

    const diabetes = await screen.findByText(/Type 2 Diabetes/);
    expect(diabetes.textContent).toContain("⚠️");

    const hypertension = screen.getByText(/Hypertension/);
    expect(hypertension.textContent).toContain("⚠️");
  });

  it("does not flag non-hereditary conditions", async () => {
    mockApiFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          {
            id: 3,
            patientId: 1,
            relation: "uncle",
            name: "Ali",
            gender: "Male",
            age: 50,
            deceased: false,
            conditions: ["Migraine"],
          },
        ],
        total: 1,
        limit: 20,
        offset: 0,
      }),
    });
    renderWithProviders(<FamilyTree patientId="1" />);
    const migraine = await screen.findByText("Migraine");
    expect(migraine.textContent).not.toContain("⚠️");
  });
});
