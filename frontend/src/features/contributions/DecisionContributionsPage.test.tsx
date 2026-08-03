import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getDecision } from "../decisions/api";
import { listParticipants } from "../participants/api";
import {
  getDecisionContributions,
  listFacilitationSessions,
} from "./api";
import { DecisionContributionsPage } from "./DecisionContributionsPage";

vi.mock("../decisions/api", () => ({ getDecision: vi.fn() }));
vi.mock("../participants/api", () => ({ listParticipants: vi.fn() }));
vi.mock("./api", () => ({
  contributionAction: vi.fn(),
  createContributionRequest: vi.fn(),
  createFacilitationSession: vi.fn(),
  getDecisionContributions: vi.fn(),
  listFacilitationSessions: vi.fn(),
  reviewContribution: vi.fn(),
  saveContributionDraft: vi.fn(),
  submitContribution: vi.fn(),
  updateContributionRequest: vi.fn(),
  updateFacilitationSessionStatus: vi.fn(),
  updateSessionAttendance: vi.fn(),
}));

describe("DecisionContributionsPage", () => {
  it("shows governed requests and participation coverage", async () => {
    vi.mocked(getDecision).mockResolvedValue({
      id: "decision-1",
      organisation_id: "organisation-1",
      title: "Regional resilience decision",
      status_label: "Open for Contribution",
    } as never);
    vi.mocked(listParticipants).mockResolvedValue([]);
    vi.mocked(listFacilitationSessions).mockResolvedValue([]);
    vi.mocked(getDecisionContributions).mockResolvedValue({
      can_manage: true,
      participation: {
        participant_count: 3,
        assigned_count: 2,
        submitted_count: 1,
        coverage_percent: 67,
        unassigned_participants: [{ id: "person-3", email: "unassigned@example.com", role: "reviewer" }],
        role_counts: { contributor: 2, reviewer: 1 },
      },
      requests: [{
        id: "request-1",
        organisation_id: "organisation-1",
        organisation_name: "Resilience Lab",
        decision_id: "decision-1",
        decision_title: "Regional resilience decision",
        option_id: null,
        session_id: null,
        session_title: null,
        requested_by: { id: "owner", email: "owner@example.com", first_name: "", last_name: "" },
        assignee: { id: "person-1", email: "contributor@example.com", first_name: "", last_name: "" },
        reviewer: null,
        kind: "evidence",
        kind_label: "Evidence",
        title: "Validate implementation evidence",
        instructions: "Check the source, limits, and recency.",
        priority: "high",
        priority_label: "High",
        status: "open",
        status_label: "Open",
        due_at: null,
        opened_at: null,
        submitted_at: null,
        reviewed_at: null,
        completed_at: null,
        cancelled_at: null,
        submissions: [],
        reviews: [],
        can_work: false,
        can_review: false,
        can_manage: true,
        is_overdue: false,
        created_at: "2026-08-01T10:00:00Z",
        updated_at: "2026-08-01T10:00:00Z",
      }],
    });

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/decisions/decision-1/contributions"]}>
          <Routes><Route path="/decisions/:decisionId/contributions" element={<DecisionContributionsPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Regional resilience decision" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Validate implementation evidence" })).toBeInTheDocument();
    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getByText(/unassigned@example.com/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Create contribution request" })).toBeInTheDocument();
  });
});
