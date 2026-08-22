import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getOrganisationBudgetRollup, getOrganisationPortfolio } from "./api";
import { OrganisationPortfolioPage } from "./OrganisationPortfolioPage";

vi.mock("./api", () => ({
  getPersonalWork: vi.fn(),
  getOrganisationPortfolio: vi.fn(),
  getOrganisationBudgetRollup: vi.fn(),
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
      watchlist: {
        stalled_decisions: [
          { id: "sd1", title: "Stalled pilot decision", status: "under_review", status_label: "Under Review", days_stalled: 25 },
        ],
        open_high_risks: [
          { id: "r1", title: "Severe supplier risk", decision_id: "d1", decision_title: "Run a pilot", likelihood: 5, impact: 5 },
        ],
        assumptions_at_risk: [
          { id: "a1", statement: "Demand keeps growing.", decision_id: "d1", decision_title: "Run a pilot", verification_status: "invalidated", verification_status_label: "Invalidated" },
        ],
        triggered_signposts: [
          { id: "so1", signpost_id: "sp1", signpost_title: "Adoption signpost", scenario_set_id: "ss1", canvas_id: "c1", assessment: "strong", assessment_label: "Strong movement", observed_on: "2026-07-25" },
        ],
        benefits_realization: { exceeded: 0, met: 2, partially_met: 1, not_met: 0, inconclusive: 0, total_reviewed: 3 },
        risk_heatmap: {
          cells: [
            { likelihood: 5, impact: 5, count: 1, risks: [{ id: "r1", title: "Severe supplier risk", decision_id: "d1", decision_title: "Run a pilot" }] },
            { likelihood: 1, impact: 1, count: 0, risks: [] },
          ],
          total_open_risks: 1,
        },
      },
    });
    vi.mocked(getOrganisationBudgetRollup).mockResolvedValue({
      round_count: 2,
      requested_total: "3500.00",
      awarded_total: "2300.00",
      funded_count: 2,
      declined_count: 1,
      pending_outcome_count: 0,
      monthly_trend: [{ month: "2026-07-01", label: "Jul 2026", awarded_total: "2300.00" }],
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

    expect(screen.getByRole("link", { name: "Stalled pilot decision" })).toHaveAttribute(
      "href",
      "/decisions/sd1",
    );
    expect(screen.getByRole("link", { name: "Severe supplier risk" })).toHaveAttribute(
      "href",
      "/decisions/d1",
    );
    expect(screen.getByText(/likelihood 5\/5, impact 5\/5/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Demand keeps growing." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Adoption signpost" })).toHaveAttribute(
      "href",
      "/organisations/o1/foresight/canvases/c1/scenarios/ss1?tab=signposts",
    );
    expect(screen.getByText("Partially met")).toBeInTheDocument();

    expect(screen.getByText("Decisions by lifecycle stage")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /decisions by lifecycle stage/i })).toBeInTheDocument();
    expect(screen.getByText("Risk heatmap")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /risk heatmap by likelihood and impact/i })).toBeInTheDocument();
    expect(screen.getByText("1 open or monitored risk plotted")).toBeInTheDocument();

    expect(screen.getByText("Budget across every round")).toBeInTheDocument();
    expect(screen.getByText(/2 rounds · 2300\.00 awarded of 3500\.00 requested/i)).toBeInTheDocument();
  });
});
