import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { getOrganisation } from "../organisations/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import { createOrganisationSession, listOrganisationSessions } from "./api";
import { OrganisationSessionsPage } from "./OrganisationSessionsPage";

vi.mock("../organisations/api", () => ({ getOrganisation: vi.fn() }));
vi.mock("../portfolio/api", () => ({ getOrganisationPortfolio: vi.fn() }));
vi.mock("./api", () => ({ listOrganisationSessions: vi.fn(), createOrganisationSession: vi.fn() }));

const organisationId = "00000000-0000-0000-0000-000000000001";

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/organisations/${organisationId}/sessions`]}>
        <Routes><Route path="/organisations/:organisationId/sessions" element={<OrganisationSessionsPage />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OrganisationSessionsPage", () => {
  it("lists existing sessions and creates a new one", async () => {
    vi.mocked(getOrganisation).mockResolvedValue({
      id: organisationId, name: "AgriNova", slug: "agrinova", description: "", website_url: "", brand_name: "",
      primary_colour: "#244A5A", invitation_policy: "owners_and_admins", default_invitation_role: "contributor",
      retention_days: null, status: "active", deactivated_at: null, current_user_role: "owner",
      created_at: "2026-07-20T10:00:00Z", updated_at: "2026-07-20T10:00:00Z",
    });
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({
      organisation: { id: organisationId } as never,
      summary: { total: 0, active: 0, overdue: 0, unresolved_discussion: 0, status_counts: {} },
      decisions: [{ id: "d1", title: "Choose the pilot region" } as never],
      watchlist: {} as never,
    });
    vi.mocked(listOrganisationSessions).mockResolvedValue([
      {
        id: "s1", title: "Q3 ideathon", prompt: "How do we cut onboarding time in half?", status: "open",
        status_label: "Open", public_slug: "abc123", decision_id: null, decision_title: null,
        decision_template_key: null,
        requires_guardian_consent: false, team_submissions_enabled: false,
        voting_enabled: true, idea_count: 4, created_by: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" },
        created_at: "2026-08-01T10:00:00Z",
      },
    ]);
    vi.mocked(createOrganisationSession).mockResolvedValue({
      id: "s2", title: "New session", prompt: "What should we try?", status: "draft", status_label: "Draft",
      public_slug: "xyz789", decision_id: null, decision_title: null, decision_template_key: null,
      requires_guardian_consent: false, team_submissions_enabled: false,
      voting_enabled: true, idea_count: 0,
      created_by: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" }, created_at: "2026-08-02T10:00:00Z",
    });

    renderPage();
    expect(await screen.findByRole("heading", { name: /agrinova open sessions/i })).toBeInTheDocument();
    expect(await screen.findByText("Q3 ideathon")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /new session/i }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "New session" } });
    fireEvent.change(screen.getByLabelText("Prompt"), { target: { value: "What should we try?" } });
    fireEvent.click(screen.getByRole("button", { name: /^create session$/i }));

    await waitFor(() =>
      expect(createOrganisationSession).toHaveBeenCalledWith(
        organisationId,
        expect.objectContaining({ title: "New session", prompt: "What should we try?" }),
      ),
    );
  });

  it("creates a session with student safeguards turned on", async () => {
    vi.mocked(getOrganisation).mockResolvedValue({
      id: organisationId, name: "AgriNova", slug: "agrinova", description: "", website_url: "", brand_name: "",
      primary_colour: "#244A5A", invitation_policy: "owners_and_admins", default_invitation_role: "contributor",
      retention_days: null, status: "active", deactivated_at: null, current_user_role: "owner",
      created_at: "2026-07-20T10:00:00Z", updated_at: "2026-07-20T10:00:00Z",
    });
    vi.mocked(getOrganisationPortfolio).mockResolvedValue({
      organisation: { id: organisationId } as never,
      summary: { total: 0, active: 0, overdue: 0, unresolved_discussion: 0, status_counts: {} },
      decisions: [],
      watchlist: {} as never,
    });
    vi.mocked(listOrganisationSessions).mockResolvedValue([]);
    vi.mocked(createOrganisationSession).mockResolvedValue({
      id: "s3", title: "State science fair", prompt: "Present a project.", status: "draft", status_label: "Draft",
      public_slug: "sci123", decision_id: null, decision_title: null, decision_template_key: null,
      requires_guardian_consent: true, team_submissions_enabled: true,
      voting_enabled: true, idea_count: 0,
      created_by: { id: "u1", email: "owner@example.com", first_name: "", last_name: "" }, created_at: "2026-08-02T10:00:00Z",
    });

    renderPage();
    expect(await screen.findByRole("heading", { name: /agrinova open sessions/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /new session/i }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "State science fair" } });
    fireEvent.change(screen.getByLabelText("Prompt"), { target: { value: "Present a project." } });
    fireEvent.click(screen.getByLabelText(/team submissions/i));
    fireEvent.click(screen.getByLabelText(/requires parent or guardian consent/i));
    fireEvent.click(screen.getByRole("button", { name: /^create session$/i }));

    await waitFor(() =>
      expect(createOrganisationSession).toHaveBeenCalledWith(
        organisationId,
        expect.objectContaining({ requires_guardian_consent: true, team_submissions_enabled: true }),
      ),
    );
  });
});
