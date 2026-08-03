import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getOrganisation } from "../organisations/api";
import { getOrganisationAnalytics } from "./api";
import { OrganisationAnalyticsPage } from "./OrganisationAnalyticsPage";

vi.mock("../organisations/api", () => ({ getOrganisation: vi.fn() }));
vi.mock("./api", () => ({ getOrganisationAnalytics: vi.fn() }));

const organisationId = "00000000-0000-0000-0000-000000000001";

describe("OrganisationAnalyticsPage", () => {
  it("shows a small explainable scorecard", async () => {
    vi.mocked(getOrganisation).mockResolvedValue({ id: organisationId, name: "AgriNova", slug: "agrinova", description: "", website_url: "", brand_name: "", primary_colour: "#244A5A", invitation_policy: "owners_and_admins", default_invitation_role: "contributor", retention_days: null, status: "active", deactivated_at: null, current_user_role: "owner", created_at: "2026-07-26T10:00:00Z", updated_at: "2026-07-26T10:00:00Z" });
    vi.mocked(getOrganisationAnalytics).mockResolvedValue({
      generated_at: "2026-07-26T12:00:00Z",
      totals: { decisions: 4, open_decisions: 2, finalised_decisions: 2, archived_decisions: 1, active_lessons: 3 },
      flow: { status_counts: [{ status: "under_review", label: "Under Review", count: 2 }], created_last_90_days: 4, finalised_last_90_days: 2, median_days_to_finalise: 12, overdue_target_decisions: 1, contribution_coverage_percent: 50 },
      learning: { outcome_reviews_completed: 1, outcome_success_percent: 100, outcome_assessment_counts: [{ assessment: "met", label: "Met expectations", count: 1 }], reviews_due_or_overdue: 0, active_lessons: 3 },
      definitions: { median_days_to_finalise: "Median calendar days." },
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[`/organisations/${organisationId}/analytics`]}>
          <Routes><Route path="/organisations/:organisationId/analytics" element={<OrganisationAnalyticsPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("heading", { name: /agrinova analytics/i })).toBeInTheDocument();
    expect(screen.getByText("Decision movement")).toBeInTheDocument();
    expect(screen.getByText("Median calendar days.")).toBeInTheDocument();
  });
});
