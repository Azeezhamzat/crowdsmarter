import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getDecision } from "../decisions/api";
import { acknowledgeAIReview, dismissAIReview, listAIReviews, requestAIReview } from "./api";
import { DecisionAIReviewPage } from "./DecisionAIReviewPage";

vi.mock("../decisions/api", () => ({ getDecision: vi.fn() }));
vi.mock("./api", () => ({
  listAIReviews: vi.fn(), requestAIReview: vi.fn(), acknowledgeAIReview: vi.fn(), dismissAIReview: vi.fn(),
}));

const decisionId = "00000000-0000-0000-0000-000000000001";

describe("DecisionAIReviewPage", () => {
  it("keeps advisory output visibly separate from human authority", async () => {
    vi.mocked(getDecision).mockResolvedValue({
      id: decisionId, organisation_id: "o1", workspace_id: "w1", title: "Run a pilot", decision_question: "Should we run a pilot?",
      purpose: "Learn.", context: "", scope: "", contribution_guidance: "",
      source_template_key: "blank", source_template_version: null, contribution_deadline: null,
      status: "under_review", status_label: "Under Review", urgency: "normal", target_decision_date: null,
      status_changed_at: "2026-07-26T12:00:00Z", owner: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
      created_by: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" }, can_edit: true, can_transition: true,
      can_manage_participants: true, next_transition: null, can_contribute_reasoning: true,
      reasoning_summary: { active_options: 1, active_evidence: 0, active_assumptions: 0, invalidated_assumptions: 0, current_risks: 0, ready_for_decision: false, blockers: [] },
      can_submit_position: false, can_finalise: false, position_summary: { current_positions: 0, required_authorities: 1, submitted_authorities: 0, missing_authorities: [], ready_to_finalise: false },
      created_at: "2026-07-26T10:00:00Z", updated_at: "2026-07-26T12:00:00Z",
    });
    vi.mocked(listAIReviews).mockResolvedValue({
      can_request: true,
      reviews: [{
        id: "r1", decision_id: decisionId, status: "completed", status_label: "Completed", provider_key: "rules",
        provider_label: "Transparent rules review", model_identifier: "crowdsmarter-rules-v1", prompt_version: "decision-review-v1",
        input_fingerprint: "abcdef1234567890", requested_by: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
        output: { summary: "One point for human consideration.", missing_evidence: [{ severity: "high", title: "No evidence", detail: "Add evidence.", related_type: "", related_id: "" }], unsupported_assumptions: [], contradictory_evidence: [], missing_stakeholders: [], risk_highlights: [], similar_decisions: [], limitations: ["Humans decide."] },
        error_message: "", started_at: "2026-07-26T12:00:00Z", completed_at: "2026-07-26T12:00:01Z", is_reviewed: false,
        reviewed_by: null, reviewed_at: null, review_notes: "", is_dismissed: false, dismissed_by: null, dismissed_at: null,
        dismissal_reason: "", can_review: true, can_dismiss: true, created_at: "2026-07-26T12:00:00Z",
      }],
    });
    vi.mocked(requestAIReview).mockRejectedValue(new Error("not used"));
    vi.mocked(acknowledgeAIReview).mockRejectedValue(new Error("not used"));
    vi.mocked(dismissAIReview).mockRejectedValue(new Error("not used"));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[`/decisions/${decisionId}/ai-review`]}>
          <Routes><Route path="/decisions/:decisionId/ai-review" element={<DecisionAIReviewPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("heading", { name: "AI review" })).toBeInTheDocument();
    expect(screen.getByText(/AI advises; humans decide/i)).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "No evidence" })).toBeInTheDocument();
  });
});
