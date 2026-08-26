import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Idea } from "../../lib/types";
import { getPublicSession, getStoredParticipantToken, joinSession, submitIdea, voteIdea } from "./api";
import { OpenSessionPublicPage } from "./OpenSessionPublicPage";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return {
    ...actual,
    getPublicSession: vi.fn(),
    getStoredParticipantToken: vi.fn(),
    joinSession: vi.fn(),
    submitIdea: vi.fn(),
    voteIdea: vi.fn(),
    removeVote: vi.fn(),
  };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/s/abc123"]}>
        <Routes><Route path="/s/:publicSlug" element={<OpenSessionPublicPage />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const baseSession = {
  id: "session-1",
  organisation_name: "AgriNova",
  title: "Farm resilience ideathon",
  prompt: "How should we cut post-harvest loss in half by 2028?",
  description: "Open to anyone with the link.",
  status: "open" as const,
  status_label: "Open",
  voting_enabled: true,
  submission_deadline: null,
  requires_guardian_consent: false,
  team_submissions_enabled: false,
  decision_template_key: null,
  ideas: [],
};

function baseIdea(overrides: Partial<Idea> = {}): Idea {
  return {
    id: "idea-1",
    title: "Existing idea",
    description: "",
    category: "",
    requested_amount: null,
    team_name: "",
    team_members: [],
    status: "submitted",
    status_label: "Submitted",
    submitted_by_participant: { name: "Kwame" },
    submitted_by_user: null,
    vote_count: 0,
    voted_by_me: false,
    application_status: null,
    comments: [],
    created_at: "2026-08-01T10:00:00Z",
    ...overrides,
  };
}

afterEach(() => vi.restoreAllMocks());

describe("OpenSessionPublicPage", () => {
  it("lets a new visitor join and submit an idea", async () => {
    vi.mocked(getStoredParticipantToken).mockReturnValue(null);
    vi.mocked(getPublicSession).mockResolvedValue(baseSession);
    vi.mocked(joinSession).mockResolvedValue({ participant_token: "tok-1", name: "Amaka Obi" });
    vi.mocked(submitIdea).mockResolvedValue({
      ...baseSession,
      ideas: [baseIdea({
        title: "Solar-powered cold storage", description: "Shared cold storage.",
        submitted_by_participant: { name: "Amaka Obi" },
      })],
    });

    renderPage();
    expect(await screen.findByRole("heading", { name: "Farm resilience ideathon" })).toBeInTheDocument();
    expect(screen.getByText(/how should we cut post-harvest loss/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Amaka Obi" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "amaka@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: /join session/i }));

    await waitFor(() => expect(joinSession).toHaveBeenCalled());
    expect(await screen.findByRole("heading", { name: /submit an idea/i })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Solar-powered cold storage" } });
    fireEvent.click(screen.getByRole("button", { name: /submit idea/i }));

    expect(await screen.findByText("Solar-powered cold storage")).toBeInTheDocument();
    expect(screen.getByText(/amaka obi/i)).toBeInTheDocument();
  });

  it("lets a returning participant vote for an idea", async () => {
    vi.mocked(getStoredParticipantToken).mockReturnValue("existing-token");
    vi.mocked(getPublicSession).mockResolvedValue({
      ...baseSession,
      ideas: [baseIdea({ vote_count: 2 })],
    });
    vi.mocked(voteIdea).mockResolvedValue({
      ...baseSession,
      ideas: [baseIdea({ vote_count: 3, voted_by_me: true })],
    });

    renderPage();
    expect(await screen.findByText("Existing idea")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /vote \(2\)/i }));
    expect(await screen.findByRole("button", { name: /voted \(3\)/i })).toBeInTheDocument();
  });

  it("uses grant-round terminology and shows a requested-amount field when linked to a grant round", async () => {
    vi.mocked(getStoredParticipantToken).mockReturnValue("existing-token");
    vi.mocked(getPublicSession).mockResolvedValue({
      ...baseSession,
      decision_template_key: "grant_round",
      ideas: [baseIdea({
        title: "Community garden expansion", requested_amount: "15000.00",
        submitted_by_participant: { name: "Ada" },
      })],
    });

    renderPage();
    expect(await screen.findByRole("heading", { name: /submit an application/i })).toBeInTheDocument();
    expect(screen.getByLabelText("Requested amount")).toBeInTheDocument();
    expect(await screen.findByText("Community garden expansion")).toBeInTheDocument();
    expect(screen.getByText(/requested amount:/i)).toBeInTheDocument();
    expect(screen.getByText("15000.00")).toBeInTheDocument();
  });

  it("shows a not-found message for an invalid or unopened session link", async () => {
    vi.mocked(getStoredParticipantToken).mockReturnValue(null);
    const { ApiError } = await import("../../lib/api");
    vi.mocked(getPublicSession).mockRejectedValue(new ApiError("Not found.", 404, {}));

    renderPage();
    expect(await screen.findByText(/invalid, or the session hasn't opened yet/i)).toBeInTheDocument();
  });

  it("requires guardian consent before a declared minor can join a session that requests it", async () => {
    vi.mocked(getStoredParticipantToken).mockReturnValue(null);
    vi.mocked(getPublicSession).mockResolvedValue({ ...baseSession, requires_guardian_consent: true });
    vi.mocked(joinSession).mockResolvedValue({ participant_token: "tok-1", name: "Ngozi" });

    renderPage();
    expect(await screen.findByRole("heading", { name: "Farm resilience ideathon" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Ngozi" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ngozi@example.com" } });
    fireEvent.change(screen.getByLabelText("Age"), { target: { value: "age_13_17" } });

    expect(await screen.findByText(/parent or guardian consent/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /join session/i }));

    // Guardian fields are required for a declared minor, so submission is blocked with a validation error.
    expect(await screen.findByText(/enter a parent or guardian's name/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Parent or guardian name"), { target: { value: "Uche Eze" } });
    fireEvent.change(screen.getByLabelText("Parent or guardian email"), { target: { value: "uche@example.com" } });
    fireEvent.click(screen.getByLabelText(/i am this participant's parent or guardian/i));
    fireEvent.click(screen.getByRole("button", { name: /join session/i }));

    await waitFor(() => expect(joinSession).toHaveBeenLastCalledWith(
      "abc123",
      expect.objectContaining({
        name: "Ngozi",
        email: "ngozi@example.com",
        guardian_consent_given: true,
        age_bracket: "age_13_17",
        guardian_name: "Uche Eze",
        guardian_email: "uche@example.com",
      }),
    ));
  });

  it("lets a submitter name a team and roster when team submissions are enabled", async () => {
    vi.mocked(getStoredParticipantToken).mockReturnValue("existing-token");
    vi.mocked(getPublicSession).mockResolvedValue({ ...baseSession, team_submissions_enabled: true, ideas: [] });
    vi.mocked(submitIdea).mockResolvedValue({
      ...baseSession,
      team_submissions_enabled: true,
      ideas: [baseIdea({
        title: "StudyBuddy matcher",
        team_name: "The Night Owls",
        team_members: [{ id: "m1", name: "Femi", role: "Team lead" }, { id: "m2", name: "Aisha", role: "" }],
        submitted_by_participant: { name: "Femi" },
      })],
    });

    renderPage();
    expect(await screen.findByLabelText("Team name (optional)")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "StudyBuddy matcher" } });
    fireEvent.change(screen.getByLabelText("Team name (optional)"), { target: { value: "The Night Owls" } });
    fireEvent.click(screen.getByRole("button", { name: /add teammate/i }));
    fireEvent.change(screen.getByLabelText("Teammate name"), { target: { value: "Aisha" } });
    fireEvent.click(screen.getByRole("button", { name: /submit idea/i }));

    await waitFor(() => expect(submitIdea).toHaveBeenCalledWith(
      "abc123",
      expect.objectContaining({
        team_name: "The Night Owls",
        team_members: [{ name: "Aisha", role: undefined }],
      }),
    ));
    expect(await screen.findByText(/the night owls/i)).toBeInTheDocument();
  });
});
