import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { fetchCurrentUser } from "../auth/api";
import { listMemberships } from "../organisations/api";
import { listDecisionMethods } from "../organisations/methodology-api";
import { getWorkspace } from "../workspaces/api";
import { listDecisionTemplates } from "./api";
import { GuidedDecisionCreatePage } from "./GuidedDecisionCreatePage";

vi.mock("../auth/api", () => ({ fetchCurrentUser: vi.fn() }));
vi.mock("../organisations/api", () => ({ listMemberships: vi.fn() }));
vi.mock("../organisations/methodology-api", () => ({ listDecisionMethods: vi.fn() }));
vi.mock("../workspaces/api", () => ({ getWorkspace: vi.fn() }));
vi.mock("./api", () => ({ listDecisionTemplates: vi.fn(), createDecision: vi.fn() }));

describe("GuidedDecisionCreatePage", () => {
  it("presents human-editable templates and advances to framing prompts", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({ id: "11111111-1111-4111-8111-111111111111", email: "owner@example.com", first_name: "A", last_name: "Owner" });
    vi.mocked(getWorkspace).mockResolvedValue({
      id: "22222222-2222-4222-8222-222222222222", organisation_id: "33333333-3333-4333-8333-333333333333",
      name: "Decisions", slug: "decisions", description: "", is_default: true, can_manage: true,
      can_create_decisions: true, created_at: "2026-01-01", updated_at: "2026-01-01",
    });
    vi.mocked(listMemberships).mockResolvedValue([]);
    vi.mocked(listDecisionMethods).mockResolvedValue([]);
    vi.mocked(listDecisionTemplates).mockResolvedValue([{
      key: "technology_adoption", name: "Technology adoption", summary: "Evaluate a technology.",
      best_for: "Software and AI systems.", question_prompt: "Should we adopt or pilot it?",
      purpose_prompt: "Describe the problem.", context_prompt: "Describe the current process.",
      scope_prompt: "Define users and exclusions.", contribution_prompt: "Request security and cost evidence.",
      suggested_urgency: "high", checklist: ["Status quo option"], version: 1,
    }]);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/workspaces/22222222-2222-4222-8222-222222222222/decisions/new"]}>
          <Routes><Route path="/workspaces/:workspaceId/decisions/new" element={<GuidedDecisionCreatePage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: /start with a clear/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /technology adoption/i }));
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByRole("heading", { name: /frame the choice/i })).toBeInTheDocument();
    expect(screen.getByText("Should we adopt or pilot it?")).toBeInTheDocument();
  });

  it("relabels the wizard for the grant round template", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({ id: "11111111-1111-4111-8111-111111111111", email: "owner@example.com", first_name: "A", last_name: "Owner" });
    vi.mocked(getWorkspace).mockResolvedValue({
      id: "22222222-2222-4222-8222-222222222222", organisation_id: "33333333-3333-4333-8333-333333333333",
      name: "Decisions", slug: "decisions", description: "", is_default: true, can_manage: true,
      can_create_decisions: true, created_at: "2026-01-01", updated_at: "2026-01-01",
    });
    vi.mocked(listMemberships).mockResolvedValue([]);
    vi.mocked(listDecisionMethods).mockResolvedValue([]);
    vi.mocked(listDecisionTemplates).mockResolvedValue([{
      key: "grant_round", name: "Grant round", summary: "Run a participatory grant round.",
      best_for: "Foundations and grant committees.", question_prompt: "Which applications should this round fund?",
      purpose_prompt: "State what change this round enables.", context_prompt: "Describe the funding pool.",
      scope_prompt: "Define eligibility and timeline.", contribution_prompt: "Request applicant evidence.",
      suggested_urgency: "normal", checklist: ["Published eligibility criteria"], version: 1,
    }]);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/workspaces/22222222-2222-4222-8222-222222222222/decisions/new"]}>
          <Routes><Route path="/workspaces/:workspaceId/decisions/new" element={<GuidedDecisionCreatePage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await screen.findByRole("button", { name: /grant round/i });
    fireEvent.click(screen.getByRole("button", { name: /grant round/i }));
    expect(await screen.findByText("Guided grant round creation")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    await screen.findByRole("heading", { name: /frame the choice/i });
    fireEvent.change(screen.getByLabelText("Working title"), { target: { value: "2026 community grant round" } });
    fireEvent.change(screen.getByLabelText("Decision question"), {
      target: { value: "Which applications should this round fund, and at what amounts?" },
    });
    fireEvent.change(screen.getByLabelText("Purpose"), {
      target: { value: "Fund community-led projects that reduce post-harvest loss." },
    });
    fireEvent.change(screen.getByLabelText("Context"), {
      target: { value: "The annual community grant pool is open for applications this quarter." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    expect(await screen.findByRole("heading", { name: /make the grant round small enough to govern/i })).toBeInTheDocument();
  });
});
