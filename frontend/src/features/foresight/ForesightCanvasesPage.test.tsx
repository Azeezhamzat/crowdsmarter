import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { listMemberships } from "../organisations/api";
import { createForesightCanvas, listForesightCanvases } from "./api";
import { ForesightCanvasesPage } from "./ForesightCanvasesPage";

vi.mock("../organisations/api", () => ({
  listMemberships: vi.fn(),
}));

vi.mock("./api", () => ({
  createForesightCanvas: vi.fn(),
  listForesightCanvases: vi.fn(),
}));

describe("ForesightCanvasesPage", () => {
  it("shows bounded foresight inquiries and accountable ownership", async () => {
    vi.mocked(listForesightCanvases).mockResolvedValue([
      {
        id: "canvas-1",
        organisation_id: "organisation-1",
        title: "Future of regional food systems",
        focal_question: "How might climate and finance reshape the system?",
        scope: "Regional agricultural production and finance",
        horizon_year: 2035,
        owner: {
          id: "user-1",
          email: "owner@example.com",
          first_name: "Azeez",
          last_name: "Hamzat",
        },
        created_by: {
          id: "user-1",
          email: "owner@example.com",
          first_name: "Azeez",
          last_name: "Hamzat",
        },
        status: "active",
        status_label: "Active",
        driver_count: 4,
        implication_count: 2,
        can_edit: true,
        created_at: "2026-07-31T10:00:00Z",
        updated_at: "2026-07-31T11:00:00Z",
      },
    ]);
    vi.mocked(listMemberships).mockResolvedValue([
      {
        id: "membership-1",
        organisation_id: "organisation-1",
        user: {
          id: "user-1",
          email: "owner@example.com",
          first_name: "Azeez",
          last_name: "Hamzat",
        },
        role: "owner",
        status: "active",
        created_at: "2026-07-30T10:00:00Z",
        updated_at: "2026-07-30T10:00:00Z",
      },
    ]);

    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter
          initialEntries={["/organisations/organisation-1/foresight/canvases"]}
        >
          <Routes>
            <Route
              element={<ForesightCanvasesPage />}
              path="/organisations/:organisationId/foresight/canvases"
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Foresight canvases" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Future of regional food systems" }),
    ).toBeInTheDocument();
    expect(screen.getByText("4 drivers")).toBeInTheDocument();
    expect(screen.getByText("2 implications")).toBeInTheDocument();
    expect(screen.getByText("Azeez Hamzat")).toBeInTheDocument();
    expect(createForesightCanvas).not.toHaveBeenCalled();
  });
});
