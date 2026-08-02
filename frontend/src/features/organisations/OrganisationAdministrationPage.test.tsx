import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import {
  getOrganisation,
  listMembershipHistory,
  listMemberships,
  listOrganisationDeletionRequests,
} from "./api";
import { OrganisationAdministrationPage } from "./OrganisationAdministrationPage";

vi.mock("./api", () => ({
  getOrganisation: vi.fn(), listMembershipHistory: vi.fn(), listMemberships: vi.fn(),
  listOrganisationDeletionRequests: vi.fn(), updateOrganisationAdministration: vi.fn(),
  transferOrganisationOwnership: vi.fn(), deactivateOrganisation: vi.fn(), reactivateOrganisation: vi.fn(),
  requestOrganisationDeletion: vi.fn(), cancelOrganisationDeletion: vi.fn(),
}));

describe("OrganisationAdministrationPage", () => {
  it("shows tenant policy, ownership, and attributable membership history", async () => {
    vi.mocked(getOrganisation).mockResolvedValue({
      id: "o1", name: "AgriNova", slug: "agrinova", description: "Decision intelligence team",
      website_url: "https://example.com", brand_name: "AgriNova", primary_colour: "#315c54",
      invitation_policy: "owners_only", default_invitation_role: "contributor", retention_days: 60,
      status: "active", deactivated_at: null, current_user_role: "owner",
      created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
    });
    vi.mocked(listMemberships).mockResolvedValue([{
      id: "m1", organisation_id: "o1", user: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
      role: "owner", status: "active", created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
    }]);
    vi.mocked(listMembershipHistory).mockResolvedValue([{
      id: "e1", user: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
      actor: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
      kind: "created", kind_label: "Created", previous_role: "", new_role: "owner",
      previous_status: "", new_status: "active", note: "Founding owner", created_at: "2026-08-01T10:00:00Z",
    }]);
    vi.mocked(listOrganisationDeletionRequests).mockResolvedValue([]);

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/organisations/o1/administration"]}>
          <Routes><Route path="/organisations/:organisationId/administration" element={<OrganisationAdministrationPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: /identity, policy and account safeguards/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /transfer accountable ownership/i })).toBeInTheDocument();
    expect(screen.getByText("Founding owner")).toBeInTheDocument();
    expect(screen.getByDisplayValue("60")).toBeInTheDocument();
  });
});
