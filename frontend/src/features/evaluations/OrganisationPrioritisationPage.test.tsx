import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { getOrganisation, listMemberships } from "../organisations/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import { listPrioritisations } from "./api";
import { OrganisationPrioritisationPage } from "./OrganisationPrioritisationPage";

vi.mock("../organisations/api", () => ({ getOrganisation: vi.fn(), listMemberships: vi.fn() }));
vi.mock("../portfolio/api", () => ({ getOrganisationPortfolio: vi.fn() }));
vi.mock("./api", () => ({
  addPortfolioCandidate: vi.fn(),
  addPortfolioCriterion: vi.fn(),
  createPrioritisation: vi.fn(),
  getPrioritisation: vi.fn(),
  listPrioritisations: vi.fn(),
  savePortfolioAssessment: vi.fn(),
  savePortfolioSelection: vi.fn(),
  updatePrioritisation: vi.fn(),
}));

describe("OrganisationPrioritisationPage", () => {
  it("frames prioritisation as constrained decision support", async () => {
    vi.mocked(getOrganisation).mockResolvedValue({ id: "organisation-1", name: "Regional Futures Lab" } as never);
    vi.mocked(listMemberships).mockResolvedValue([{ id: "membership-1", organisation_id: "organisation-1", role: "owner", status: "active", user: { id: "owner-1", email: "owner@example.com", first_name: "Azeez", last_name: "Hamzat" } }] as never);
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({ decisions: [] } as never);
    vi.mocked(listPrioritisations).mockResolvedValue([]);

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/organisations/organisation-1/prioritisation"]}>
          <Routes>
            <Route path="/organisations/:organisationId/prioritisation" element={<OrganisationPrioritisationPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Regional Futures Lab" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Define the decision envelope" })).toBeInTheDocument();
    expect(screen.getByLabelText("Budget limit")).toBeInTheDocument();
    expect(screen.getByLabelText("Capacity limit")).toBeInTheDocument();
    expect(screen.getByText(/never an automatic portfolio decision/i)).toBeInTheDocument();
  });
});
