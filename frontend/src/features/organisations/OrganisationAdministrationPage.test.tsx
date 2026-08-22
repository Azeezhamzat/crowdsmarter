import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getOrganisationSubscription, listPlans } from "../billing/api";
import { getDisbursementConfiguration } from "../disbursements/api";
import { getLookupConfiguration } from "../org-enrichment/api";
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

vi.mock("../billing/api", () => ({
  getOrganisationSubscription: vi.fn(), listPlans: vi.fn(),
  changeOrganisationPlan: vi.fn(), setOrganisationBillingContact: vi.fn(),
}));

vi.mock("../disbursements/api", () => ({
  getDisbursementConfiguration: vi.fn(),
  setDisbursementProvider: vi.fn(),
  setDisbursementApiKey: vi.fn(),
  clearDisbursementApiKey: vi.fn(),
  testDisbursementConnection: vi.fn(),
}));

vi.mock("../org-enrichment/api", () => ({
  getLookupConfiguration: vi.fn(),
  setLookupProvider: vi.fn(),
  setLookupApiKey: vi.fn(),
  clearLookupApiKey: vi.fn(),
  testLookupConnection: vi.fn(),
}));

vi.mock("../ai-assistance/api", () => ({ getAIReviewQualityMetrics: vi.fn().mockRejectedValue(new Error("not mocked")) }));

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
    vi.mocked(getOrganisationSubscription).mockResolvedValue({
      id: "s1", organisation_id: "o1",
      plan: {
        id: "p1", key: "team", name: "Team", description: "For a single team.", trial_days: 14,
        max_active_decisions: 25, max_active_members: 15, includes_advanced_foresight: true,
        includes_ai_assistance: true, support_level: "community", support_level_label: "Community",
      },
      status: "trialing", status_label: "Trialing", trial_ends_at: "2026-08-15T10:00:00Z",
      is_trial_expired: false, billing_contact: null, started_at: "2026-08-01T10:00:00Z",
      active_decision_count: 2, active_member_count: 1,
      created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
    });
    vi.mocked(listPlans).mockResolvedValue([
      { id: "p1", key: "team", name: "Team", description: "", trial_days: 14, max_active_decisions: 25, max_active_members: 15, includes_advanced_foresight: true, includes_ai_assistance: true, support_level: "community", support_level_label: "Community" },
      { id: "p2", key: "professional", name: "Professional", description: "", trial_days: 14, max_active_decisions: null, max_active_members: 50, includes_advanced_foresight: true, includes_ai_assistance: true, support_level: "standard", support_level_label: "Standard" },
    ]);
    vi.mocked(getDisbursementConfiguration).mockResolvedValue({
      id: "d1", organisation_id: "o1", provider_key: "manual", provider_key_label: "Manual ledger",
      stripe_account_id: "", api_key_is_set: false, created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
    });
    vi.mocked(getLookupConfiguration).mockResolvedValue({
      id: "l1", organisation_id: "o1", provider_key: "manual", provider_key_label: "Manual verification",
      api_key_is_set: false, created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
    });

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
    expect(await screen.findByRole("heading", { name: /packaging tier and usage/i })).toBeInTheDocument();
    expect(screen.getAllByText("Team").length).toBeGreaterThan(0);
    expect(screen.getByText(/2 \/ 25/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /change plan/i })).toBeInTheDocument();

    expect(await screen.findByRole("heading", { name: /disbursement provider/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue("Manual ledger")).toBeInTheDocument();

    expect(await screen.findByRole("heading", { name: /organisation lookup/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue("Manual verification")).toBeInTheDocument();
  });
});
