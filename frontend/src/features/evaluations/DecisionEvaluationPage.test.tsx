import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getDecision } from "../decisions/api";
import { listOptions } from "../reasoning/api";
import { getEvaluation, listEvaluations } from "./api";
import { DecisionEvaluationPage } from "./DecisionEvaluationPage";

vi.mock("../decisions/api", () => ({ getDecision: vi.fn() }));
vi.mock("../reasoning/api", () => ({ listOptions: vi.fn() }));
vi.mock("./api", () => ({
  addEvaluationCriterion: vi.fn(),
  createEvaluation: vi.fn(),
  createEvaluationRound: vi.fn(),
  createMinorityReport: vi.fn(),
  getEvaluation: vi.fn(),
  listEvaluations: vi.fn(),
  saveEvaluationSubmission: vi.fn(),
  transitionEvaluationRound: vi.fn(),
}));

describe("DecisionEvaluationPage", () => {
  it("presents independent collective evaluation methods", async () => {
    vi.mocked(getDecision).mockResolvedValue({
      id: "decision-1",
      title: "Regional adaptation programme",
      owner: { id: "owner-1", email: "owner@example.com", first_name: "Azeez", last_name: "Hamzat" },
    } as never);
    vi.mocked(listOptions).mockResolvedValue([]);
    vi.mocked(listEvaluations).mockResolvedValue([]);
    vi.mocked(getEvaluation).mockRejectedValue(new Error("not requested"));

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/decisions/decision-1/evaluations"]}>
          <Routes>
            <Route path="/decisions/:decisionId/evaluations" element={<DecisionEvaluationPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Regional adaptation programme" })).toBeInTheDocument();
    expect(screen.getByText("Multi-criteria scorecard")).toBeInTheDocument();
    expect(screen.getByText("Approval voting")).toBeInTheDocument();
    expect(screen.getByText("Consent and objections")).toBeInTheDocument();
    expect(screen.getByText("Delphi rounds")).toBeInTheDocument();
    expect(screen.getByText("Anonymous to peers")).toBeInTheDocument();
  });
});
