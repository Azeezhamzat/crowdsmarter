import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getDecision } from "../decisions/api";
import { listOptions } from "../reasoning/api";
import { DecisionGovernancePage } from "./DecisionGovernancePage";
import {
  getFinalisation,
  listCurrentPositions,
  listPositionHistory,
} from "./api";

vi.mock("../decisions/api", () => ({ getDecision: vi.fn() }));
vi.mock("../reasoning/api", () => ({ listOptions: vi.fn() }));
vi.mock("./api", () => ({
  getFinalisation: vi.fn(),
  listCurrentPositions: vi.fn(),
  listPositionHistory: vi.fn(),
  submitPosition: vi.fn(),
  finaliseDecision: vi.fn(),
}));

const decisionId = "00000000-0000-0000-0000-000000000001";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/decisions/${decisionId}/governance`]}>
        <Routes>
          <Route
            path="/decisions/:decisionId/governance"
            element={<DecisionGovernancePage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DecisionGovernancePage", () => {
  beforeEach(() => {
    vi.mocked(getDecision).mockResolvedValue({
      id: decisionId,
      organisation_id: "00000000-0000-0000-0000-000000000002",
      workspace_id: "00000000-0000-0000-0000-000000000003",
      title: "Run a monitored pilot",
      decision_question: "Should the organisation run a pilot?",
      purpose: "Learn before wider commitment.",
      context: "A controlled trial is available.",
      scope: "Three sites.",
      contribution_guidance: "Use relevant evidence.",
      source_template_key: "blank", source_template_version: null,
      contribution_deadline: null,
      status: "ready_for_decision",
      status_label: "Ready for Decision",
      urgency: "normal",
      target_decision_date: null,
      status_changed_at: "2026-07-26T12:00:00Z",
      owner: {
        id: "00000000-0000-0000-0000-000000000004",
        email: "owner@example.com",
        first_name: "",
        last_name: "",
      },
      created_by: {
        id: "00000000-0000-0000-0000-000000000004",
        email: "owner@example.com",
        first_name: "",
        last_name: "",
      },
      can_edit: false,
      can_transition: true,
      can_manage_participants: false,
      next_transition: {
        from_status: "ready_for_decision",
        to_status: "decision_finalised",
        enabled: true,
        blocked_reason: "",
        action: "finalise",
      },
      can_contribute_reasoning: false,
      reasoning_summary: {
        active_options: 2,
        active_evidence: 1,
        active_assumptions: 1,
        invalidated_assumptions: 0,
        current_risks: 1,
        active_criteria: 0,
        ready_for_decision: true,
        blockers: [],
      },
      can_submit_position: true,
      can_finalise: true,
      position_summary: {
        current_positions: 0,
        required_authorities: 1,
        submitted_authorities: 0,
        missing_authorities: [
          {
            participant_id: "00000000-0000-0000-0000-000000000005",
            email: "owner@example.com",
            role: "decision_owner",
            role_label: "Decision Owner",
          },
        ],
        ready_to_finalise: false,
      },
      created_at: "2026-07-26T10:00:00Z",
      updated_at: "2026-07-26T12:00:00Z",
    });
    vi.mocked(listOptions).mockResolvedValue([]);
    vi.mocked(listCurrentPositions).mockResolvedValue([]);
    vi.mocked(listPositionHistory).mockResolvedValue([]);
    vi.mocked(getFinalisation).mockResolvedValue({ finalisation: null });
  });

  it("keeps finalisation blocked until required human authorities submit positions", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "Positions and final decision" })).toBeInTheDocument();
    expect(screen.getByText(/owner@example.com.*must submit a position/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Finalise decision" })).toBeDisabled();
  });
});
