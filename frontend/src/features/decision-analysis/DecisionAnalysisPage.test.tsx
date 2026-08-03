import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getDecision } from "../decisions/api";
import { listMemberships } from "../organisations/api";
import {
  getDecisionAnalysis,
  listDecisionIssues,
  listExecutiveSummaries,
  listQualityReviews,
} from "./api";
import { DecisionAnalysisPage } from "./DecisionAnalysisPage";

vi.mock("../decisions/api", () => ({ getDecision: vi.fn() }));
vi.mock("../organisations/api", () => ({ listMemberships: vi.fn() }));
vi.mock("./api", () => ({
  createDecisionIssue: vi.fn(),
  createExecutiveSummary: vi.fn(),
  createQualityReview: vi.fn(),
  getDecisionAnalysis: vi.fn(),
  listDecisionIssues: vi.fn(),
  listExecutiveSummaries: vi.fn(),
  listQualityReviews: vi.fn(),
  updateDecisionIssue: vi.fn(),
  updateExecutiveSummary: vi.fn(),
  updateQualityReview: vi.fn(),
}));

describe("DecisionAnalysisPage", () => {
  it("presents an option-centred, traceable decision picture", async () => {
    vi.mocked(getDecision).mockResolvedValue({
      id: "decision-1",
      organisation_id: "organisation-1",
      title: "Regional adaptation programme",
      owner: { id: "owner-1", email: "owner@example.com", first_name: "Azeez", last_name: "Hamzat" },
      can_transition: true,
    } as never);
    vi.mocked(listMemberships).mockResolvedValue([]);
    vi.mocked(listDecisionIssues).mockResolvedValue([]);
    vi.mocked(listQualityReviews).mockResolvedValue([]);
    vi.mocked(listExecutiveSummaries).mockResolvedValue([]);
    vi.mocked(getDecisionAnalysis).mockResolvedValue({
      decision: { id: "decision-1", title: "Regional adaptation programme", question: "Which adaptation option remains robust?", status: "under_review", status_label: "Under Review" },
      options: [{
        id: "option-1", title: "Distributed resilience hubs", description: "Build local response capacity.", expected_benefits: "Faster response.", tradeoffs: "Coordination overhead.", is_status_quo: false,
        evidence: { supporting: 4, challenging: 2, mixed: 1, context: 0, high_strength: 3, structured_sources: 5, high_credibility_sources: 2, unassessed_sources: 1, superseded_sources: 0, withdrawn_sources: 0, dated_sources: 4 },
        assumptions: { total: 3, unverified: 1, invalidated: 0, low_confidence: 1, overdue_review: 0 },
        risks: { total: 2, exposure: 18, highest_score: 12, without_mitigation: 0, overdue_review: 1 },
        stakeholders: { support: 5, conditional: 2, high_confidence: 3 },
        scenarios: { assessment_count: 4, average_robustness: 4.1, minimum_robustness: 3.4, vulnerability_count: 1, mitigation_count: 2 },
        evaluations: [{ exercise_id: "evaluation-1", exercise_title: "Independent scorecard", method: "scorecard", weighted_score: 78.5 }],
        issues: { open: 1, critical: 0 },
      }],
      cross_cutting: { evidence: 2, assumptions: 1, risks: 1, open_issues: 0, do_not_support_any: 1, abstentions: 0 },
      foresight: { linked_signals: [], implications: [] },
      quality_review: null,
      executive_summary: null,
      minority_reports: [],
      issue_summary: { total: 1, open: 1, critical: 0 },
      capabilities: { can_manage: true, can_contribute: true },
      principle: "This workspace organises traceable human judgement. It does not select an option or advance the decision lifecycle.",
    });

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/decisions/decision-1/analysis"]}>
          <Routes><Route path="/decisions/:decisionId/analysis" element={<DecisionAnalysisPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Regional adaptation programme" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Distributed resilience hubs" })).toBeInTheDocument();
    expect(screen.getByText("4 support · 2 challenge")).toBeInTheDocument();
    expect(screen.getByText(/78\.5 weighted score/)).toBeInTheDocument();
    expect(screen.getByText(/does not select an option/i)).toBeInTheDocument();
  });
});
