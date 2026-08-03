import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getPersonalWork } from "./api";
import { MyWorkPanel } from "./MyWorkPanel";

vi.mock("./api", () => ({
  getPersonalWork: vi.fn(),
  getOrganisationPortfolio: vi.fn(),
}));

describe("MyWorkPanel", () => {
  it("shows accountable next actions and overdue work", async () => {
    vi.mocked(getPersonalWork).mockResolvedValue({
      unread_notifications: 2,
      overdue_count: 1,
      decision_count: 1,
      decisions: [{
        id: "d1",
        workspace_id: "w1",
        organisation_id: "o1",
        organisation_name: "AgriNova",
        workspace: { id: "w1", name: "Decisions" },
        title: "Run a pilot",
        decision_question: "Should we run a pilot?",
        status: "under_review",
        status_label: "Under Review",
        urgency: "high",
        target_decision_date: "2026-07-20",
        owner: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
        participant_role: "decision_owner",
        unresolved_discussion_count: 1,
        next_action: "Review reasoning and unresolved concerns",
        due_date: "2026-07-20",
        is_overdue: true,
        updated_at: "2026-07-26T10:00:00Z",
      }],
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter><MyWorkPanel /></MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("heading", { name: "Run a pilot" })).toBeInTheDocument();
    expect(screen.getByText("Review reasoning and unresolved concerns")).toBeInTheDocument();
    expect(screen.getByText("2 unread notifications")).toBeInTheDocument();
  });
});
