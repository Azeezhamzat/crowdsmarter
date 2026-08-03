import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getDecision } from "../decisions/api";
import { listMemberships } from "../organisations/api";
import { listDecisionActivity, listDiscussion } from "./api";
import { DecisionCollaborationPage } from "./DecisionCollaborationPage";

vi.mock("../decisions/api", () => ({ getDecision: vi.fn() }));
vi.mock("../organisations/api", () => ({ listMemberships: vi.fn() }));
vi.mock("./api", () => ({
  listDiscussion: vi.fn(),
  createDiscussionEntry: vi.fn(),
  resolveDiscussionEntry: vi.fn(),
  listDecisionActivity: vi.fn(),
}));

describe("DecisionCollaborationPage", () => {
  it("shows attributable discussion and resolution records", async () => {
    vi.mocked(getDecision).mockResolvedValue({
      id: "d1", organisation_id: "o1", workspace_id: "w1", title: "Run a pilot",
      decision_question: "Should we run a pilot?", purpose: "", context: "", scope: "",
      contribution_guidance: "", urgency: "normal", target_decision_date: null,
      source_template_key: "blank", source_template_version: null,
      contribution_deadline: null, status: "under_review", status_label: "Under Review",
      status_changed_at: "2026-07-26T10:00:00Z",
      owner: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
      created_by: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
      can_edit: true, can_transition: true, can_manage_participants: true,
      next_transition: null, can_contribute_reasoning: true,
      reasoning_summary: { active_options: 2, active_evidence: 1, active_assumptions: 1, invalidated_assumptions: 0, current_risks: 1, ready_for_decision: true, blockers: [] },
      can_submit_position: false, can_finalise: false,
      position_summary: { current_positions: 0, required_authorities: 1, submitted_authorities: 0, missing_authorities: [], ready_to_finalise: false },
      created_at: "2026-07-26T10:00:00Z", updated_at: "2026-07-26T10:00:00Z",
    });
    vi.mocked(listMemberships).mockResolvedValue([]);
    vi.mocked(listDiscussion).mockResolvedValue({
      can_contribute: true,
      entries: [{
        id: "e1", decision_id: "d1",
        author: { id: "u2", email: "reviewer@example.com", first_name: "", last_name: "" },
        kind: "concern", kind_label: "Concern", body: "Connectivity remains unresolved.",
        reply_to_id: null, reply_to_summary: null, mentioned_users: [], is_resolved: true,
        resolved_at: "2026-07-26T12:00:00Z",
        resolved_by: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
        resolution_note: "Offline capture will be tested before launch.", can_resolve: true,
        created_at: "2026-07-26T11:00:00Z",
      }],
    });
    vi.mocked(listDecisionActivity).mockResolvedValue([]);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/decisions/d1/collaboration"]}>
          <Routes>
            <Route path="/decisions/:decisionId/collaboration" element={<DecisionCollaborationPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByText("Connectivity remains unresolved.")).toBeInTheDocument();
    expect(screen.getByText("Offline capture will be tested before launch.")).toBeInTheDocument();
    expect(screen.getByText("Resolved")).toBeInTheDocument();
  });
});
