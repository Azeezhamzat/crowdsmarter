import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { fetchCurrentUser } from "../auth/api";
import { getPlatformOrganisation, listPlatformOrganisations } from "./api";
import { PlatformOrganisationSupportPage } from "./PlatformOrganisationSupportPage";

vi.mock("../auth/api", () => ({ fetchCurrentUser: vi.fn() }));
vi.mock("./api", () => ({
  getPlatformOrganisation: vi.fn(),
  listPlatformOrganisations: vi.fn(),
  createSupportAccess: vi.fn(),
  revokeSupportAccess: vi.fn(),
  transferPlatformOwnership: vi.fn(),
  changePlatformOrganisationState: vi.fn(),
  changePlatformInvitation: vi.fn(),
}));

describe("PlatformOrganisationSupportPage", () => {
  it("requires a reasoned expiring grant before tenant detail is displayed", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      id: "admin-1",
      email: "hello@crowdsmarter.com",
      first_name: "Azeez",
      last_name: "Hamzat",
      is_platform_administrator: true,
    });
    vi.mocked(listPlatformOrganisations).mockResolvedValue([{
      id: "org-1",
      name: "NorthStar Grid Services",
      slug: "northstar-grid-services-sim",
      description: "Simulated client",
      brand_name: "NorthStar Grid",
      website_url: "",
      primary_colour: "#185c4f",
      status: "active",
      retention_days: 365,
      created_at: "2026-08-01T10:00:00Z",
      updated_at: "2026-08-01T10:00:00Z",
      member_count: 4,
      active_owner_count: 1,
      workspace_count: 1,
      decision_count: 1,
      active_decision_count: 1,
      pending_invitation_count: 0,
      owners: [],
    }]);
    vi.mocked(getPlatformOrganisation).mockRejectedValue(
      new ApiError("Create a time-bounded support-access grant.", 403, { detail: "Access required" }),
    );

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/platform-admin/organisations/org-1"]}>
          <Routes><Route path="/platform-admin/organisations/:organisationId" element={<PlatformOrganisationSupportPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: /record access before opening northstar grid services/i })).toBeInTheDocument();
    expect(screen.getByText(/not invisible tenant membership/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Specific reason")).toBeInTheDocument();
  });
});
