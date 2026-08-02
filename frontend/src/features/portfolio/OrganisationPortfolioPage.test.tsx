import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { getOrganisationPortfolio } from "./api";
import { OrganisationPortfolioPage } from "./OrganisationPortfolioPage";

vi.mock("./api", () => ({
  getPersonalWork: vi.fn(),
  getOrganisationPortfolio: vi.fn(),
}));

describe("OrganisationPortfolioPage", () => {
  it("shows portfolio measures and unresolved work", async () => {
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({
      organisation: {
        id: "o1", name: "AgriNova", slug: "agrinova", description: "", website_url: "", brand_name: "", primary_colour: "#244A5A", invitation_policy: "owners_and_admins", default_invitation_role: "contributor", retention_days: null, status: "active", deactivated_at: null, current_user_role: "owner",
        created_at: "2026-07-20T10:00:00Z", updated_at: "2026-07-20T10:00:00Z",
      },
      summary: { total: 1, active: 1, overdue: 1, unresolved_discussion: 2, status_counts: { under_review: 1 } },
      decisions: [{
        id: "d1", workspace_id: "w1", organisation_id: "o1", organisation_name: "AgriNova",
        workspace: { id: "w1", name: "Decisions" }, title: "Run a pilot",
        decision_question: "Should we run a pilot?", status: "under_review", status_label: "Under Review",
        urgency: "high", target_decision_date: "2026-07-20",
        owner: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
        participant_role: "decision_owner", unresolved_discussion_count: 2,
        next_action: "Review reasoning and unresolved concerns", due_date: "2026-07-20",
        is_overdue: true, updated_at: "2026-07-26T10:00:00Z",
      }],
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/organisations/o1/portfolio"]}>
          <Routes>
            <Route path="/organisations/:organisationId/portfolio" element={<OrganisationPortfolioPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("heading", { name: "AgriNova" })).toBeInTheDocument();
    expect(screen.getByText("2 unresolved discussion items")).toBeInTheDocument();
    expect(screen.getByText("Review reasoning and unresolved concerns")).toBeInTheDocument();
  });
});
