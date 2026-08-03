import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getOrganisation } from "../organisations/api";
import { searchOrganisation } from "./api";
import { OrganisationSearchPage } from "./OrganisationSearchPage";

vi.mock("../organisations/api", () => ({ getOrganisation: vi.fn() }));
vi.mock("./api", () => ({ searchOrganisation: vi.fn() }));

const organisationId = "00000000-0000-0000-0000-000000000001";

describe("OrganisationSearchPage", () => {
  it("shows tenant search results", async () => {
    vi.mocked(getOrganisation).mockResolvedValue({
      id: organisationId,
      name: "AgriNova",
      slug: "agrinova",
      description: "",
      website_url: "",
      brand_name: "",
      primary_colour: "#244A5A",
      invitation_policy: "owners_and_admins",
      default_invitation_role: "contributor",
      retention_days: null,
      status: "active",
      deactivated_at: null,
      current_user_role: "owner",
      created_at: "2026-07-26T10:00:00Z",
      updated_at: "2026-07-26T10:00:00Z",
    });
    vi.mocked(searchOrganisation).mockResolvedValue({
      query: "pest",
      count: 1,
      results: [{
        kind: "lesson",
        object_id: "00000000-0000-0000-0000-000000000002",
        decision_id: "00000000-0000-0000-0000-000000000003",
        title: "Capture a baseline",
        snippet: "Baseline evidence made the pest-monitoring outcome interpretable.",
        url: "/decisions/00000000-0000-0000-0000-000000000003/outcomes",
        rank: 0.8,
      }],
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[`/organisations/${organisationId}/search?q=pest`]}>
          <Routes><Route path="/organisations/:organisationId/search" element={<OrganisationSearchPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("heading", { name: /search agrinova/i })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Capture a baseline" })).toBeInTheDocument();
  });
});
