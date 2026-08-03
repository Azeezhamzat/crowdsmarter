import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getDecision } from "../decisions/api";
import { listMemberships } from "../organisations/api";
import { DecisionOutcomesPage } from "./DecisionOutcomesPage";
import { getDecisionReview, listLessons } from "./api";

vi.mock("../decisions/api", () => ({ getDecision: vi.fn() }));
vi.mock("../organisations/api", () => ({ listMemberships: vi.fn() }));
vi.mock("./api", () => ({
  getDecisionReview: vi.fn(), listLessons: vi.fn(), recordCommitment: vi.fn(),
  changeImplementationOwner: vi.fn(), startImplementation: vi.fn(), openOutcomeReview: vi.fn(), completeOutcomeReview: vi.fn(),
  createLesson: vi.fn(), retireLesson: vi.fn(), archiveDecision: vi.fn(),
}));

const decisionId = "00000000-0000-0000-0000-000000000001";

describe("DecisionOutcomesPage", () => {
  it("offers commitment after finalisation", async () => {
    vi.mocked(getDecision).mockResolvedValue({
      id: decisionId,
      organisation_id: "00000000-0000-0000-0000-000000000002",
      workspace_id: "00000000-0000-0000-0000-000000000003",
      title: "Run a monitored pilot",
      decision_question: "Should we run a pilot?",
      purpose: "Learn before scaling.", context: "", scope: "", contribution_guidance: "",
      source_template_key: "blank", source_template_version: null,
      contribution_deadline: null, status: "decision_finalised", status_label: "Decision Finalised",
      urgency: "normal", target_decision_date: null, status_changed_at: "2026-07-26T12:00:00Z",
      owner: { id: "o", email: "owner@example.com", first_name: "", last_name: "" },
      created_by: { id: "o", email: "owner@example.com", first_name: "", last_name: "" },
      can_edit: false, can_transition: true, can_manage_participants: false,
      next_transition: { from_status: "decision_finalised", to_status: "commitment", enabled: true, blocked_reason: "", action: "outcome_workflow" },
      can_contribute_reasoning: false,
      reasoning_summary: { active_options: 2, active_evidence: 1, active_assumptions: 1, invalidated_assumptions: 0, current_risks: 1, active_criteria: 0, ready_for_decision: true, blockers: [] },
      can_submit_position: false, can_finalise: false,
      position_summary: { current_positions: 1, required_authorities: 1, submitted_authorities: 1, missing_authorities: [], ready_to_finalise: false },
      created_at: "2026-07-26T10:00:00Z", updated_at: "2026-07-26T12:00:00Z",
    });
    vi.mocked(getDecisionReview).mockResolvedValue({ review: null });
    vi.mocked(listLessons).mockResolvedValue([]);
    vi.mocked(listMemberships).mockResolvedValue([]);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[`/decisions/${decisionId}/outcomes`]}>
          <Routes><Route path="/decisions/:decisionId/outcomes" element={<DecisionOutcomesPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("heading", { name: "Run a monitored pilot" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Record commitment" })).toBeInTheDocument();
  });
});
