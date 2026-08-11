import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getOrganisationPortfolio } from "../portfolio/api";
import { getOrganiserSession, promoteIdea, setSessionState, shortlistIdea } from "./api";
import { OpenSessionOrganiserPage } from "./OpenSessionOrganiserPage";

vi.mock("../portfolio/api", () => ({ getOrganisationPortfolio: vi.fn() }));
vi.mock("./api", () => ({
  getOrganiserSession: vi.fn(),
  setSessionState: vi.fn(),
  shortlistIdea: vi.fn(),
  promoteIdea: vi.fn(),
}));

const organisationId = "00000000-0000-0000-0000-000000000001";
const sessionId = "00000000-0000-0000-0000-000000000002";

const baseSession = {
  id: sessionId, title: "Q3 ideathon", prompt: "How do we cut onboarding time in half?", status: "open" as const,
  status_label: "Open", public_slug: "abc123", decision_id: null, decision_title: null, voting_enabled: true,
  idea_count: 1, created_by: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
  created_at: "2026-08-01T10:00:00Z", description: "",
  ideas: [{
    id: "idea-1", title: "Promising idea", description: "Worth trying.", status: "submitted" as const,
    status_label: "Submitted", submitted_by_participant: { name: "Ada" }, submitted_by_user: null,
    vote_count: 3, voted_by_me: false, created_at: "2026-08-01T10:00:00Z",
  }],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/organisations/${organisationId}/sessions/${sessionId}`]}>
        <Routes>
          <Route path="/organisations/:organisationId/sessions/:sessionId" element={<OpenSessionOrganiserPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OpenSessionOrganiserPage", () => {
  it("shortlists and promotes an idea into a real decision option", async () => {
    vi.mocked(getOrganiserSession).mockResolvedValue(baseSession);
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({
      organisation: { id: organisationId } as never,
      summary: { total: 0, active: 0, overdue: 0, unresolved_discussion: 0, status_counts: {} },
      decisions: [{ id: "d1", title: "Choose the pilot region" } as never],
      watchlist: {} as never,
    });
    vi.mocked(shortlistIdea).mockResolvedValue({
      ...baseSession,
      ideas: [{ ...baseSession.ideas[0]!, status: "shortlisted", status_label: "Shortlisted" }],
    });
    vi.mocked(promoteIdea).mockResolvedValue({
      ...baseSession,
      ideas: [{ ...baseSession.ideas[0]!, status: "promoted", status_label: "Promoted" }],
    });

    renderPage();
    expect(await screen.findByRole("heading", { name: "Q3 ideathon" })).toBeInTheDocument();
    expect(screen.getByText("Promising idea")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^shortlist$/i }));
    expect(await screen.findByText(/ada · shortlisted/i)).toBeInTheDocument();

    await screen.findByRole("option", { name: "Choose the pilot region" });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "d1" } });
    fireEvent.click(screen.getByRole("button", { name: /promote to option/i }));

    await waitFor(() => expect(promoteIdea).toHaveBeenCalledWith(sessionId, "idea-1", "d1"));
    expect(await screen.findByText(/ada · promoted/i)).toBeInTheDocument();
  });

  it("closes and reopens a session", async () => {
    vi.mocked(getOrganiserSession).mockResolvedValue({ ...baseSession, ideas: [] });
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({
      organisation: { id: organisationId } as never,
      summary: { total: 0, active: 0, overdue: 0, unresolved_discussion: 0, status_counts: {} },
      decisions: [],
      watchlist: {} as never,
    });
    vi.mocked(setSessionState).mockResolvedValue({ ...baseSession, ideas: [], status: "closed", status_label: "Closed" });

    renderPage();
    const closeBtn = await screen.findByRole("button", { name: /close session/i });
    fireEvent.click(closeBtn);
    await waitFor(() => expect(setSessionState).toHaveBeenCalledWith(sessionId, "close"));
    expect(await screen.findByRole("button", { name: /reopen session/i })).toBeInTheDocument();
  });
});
