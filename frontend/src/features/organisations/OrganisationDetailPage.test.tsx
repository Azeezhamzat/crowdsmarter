import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getOrganisation, listMemberships } from "./api";
import { listInvitations } from "../invitations/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import { listWorkspaces } from "../workspaces/api";
import { OrganisationDetailPage } from "./OrganisationDetailPage";

vi.mock("./api", () => ({
  getOrganisation: vi.fn(), listMemberships: vi.fn(),
  changeMembershipRole: vi.fn(), removeMembership: vi.fn(),
}));
vi.mock("../invitations/api", () => ({
  createInvitation: vi.fn(), listInvitations: vi.fn(), resendInvitation: vi.fn(), revokeInvitation: vi.fn(),
}));
vi.mock("../portfolio/api", () => ({ getOrganisationPortfolio: vi.fn() }));
vi.mock("../workspaces/api", () => ({ listWorkspaces: vi.fn() }));

const organisation = {
  id: "o1", name: "AgriNova", slug: "agrinova", description: "Decision intelligence team",
  website_url: "https://example.com", brand_name: "AgriNova", primary_colour: "#315c54",
  invitation_policy: "owners_only" as const, default_invitation_role: "contributor" as const, retention_days: 60,
  status: "active" as const, deactivated_at: null, current_user_role: "owner" as const,
  created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
};

const membership = {
  id: "m1", organisation_id: "o1", user: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
  role: "owner" as const, status: "active" as const, created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
};

const workspace = {
  id: "w1", organisation_id: "o1", name: "Default workspace", slug: "default", description: "",
  is_default: true, can_manage: true, can_create_decisions: true,
  created_at: "2026-08-01T10:00:00Z", updated_at: "2026-08-01T10:00:00Z",
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/organisations/o1"]}>
        <Routes><Route path="/organisations/:organisationId" element={<OrganisationDetailPage />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OrganisationDetailPage", () => {
  it("prompts a fresh organisation to frame its first decision", async () => {
    vi.mocked(getOrganisation).mockResolvedValue(organisation);
    vi.mocked(listMemberships).mockResolvedValue([membership]);
    vi.mocked(listInvitations).mockResolvedValue([]);
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({
      organisation, summary: { total: 0, active: 0, overdue: 0, unresolved_discussion: 0, status_counts: {} }, decisions: [],
    });
    vi.mocked(listWorkspaces).mockResolvedValue([workspace]);

    renderPage();

    expect(await screen.findByRole("heading", { name: "Frame your first decision" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start a guided decision" })).toHaveAttribute(
      "href",
      "/workspaces/w1/decisions/new",
    );
  });

  it("does not prompt an organisation that already has decisions", async () => {
    vi.mocked(getOrganisation).mockResolvedValue(organisation);
    vi.mocked(listMemberships).mockResolvedValue([membership]);
    vi.mocked(listInvitations).mockResolvedValue([]);
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({
      organisation, summary: { total: 3, active: 2, overdue: 0, unresolved_discussion: 0, status_counts: {} }, decisions: [],
    });
    vi.mocked(listWorkspaces).mockResolvedValue([workspace]);

    renderPage();

    expect(await screen.findByRole("heading", { name: "AgriNova" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Frame your first decision" })).not.toBeInTheDocument();
  });
});
