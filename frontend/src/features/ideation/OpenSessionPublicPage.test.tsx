import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

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
  ideas: [],
};

afterEach(() => vi.restoreAllMocks());

describe("OpenSessionPublicPage", () => {
  it("lets a new visitor join and submit an idea", async () => {
    vi.mocked(getStoredParticipantToken).mockReturnValue(null);
    vi.mocked(getPublicSession).mockResolvedValue(baseSession);
    vi.mocked(joinSession).mockResolvedValue({ participant_token: "tok-1", name: "Amaka Obi" });
    vi.mocked(submitIdea).mockResolvedValue({
      ...baseSession,
      ideas: [{
        id: "idea-1", title: "Solar-powered cold storage", description: "Shared cold storage.",
        status: "submitted", status_label: "Submitted",
        submitted_by_participant: { name: "Amaka Obi" }, submitted_by_user: null,
        vote_count: 0, voted_by_me: false, created_at: "2026-08-01T10:00:00Z",
      }],
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
      ideas: [{
        id: "idea-1", title: "Existing idea", description: "",
        status: "submitted", status_label: "Submitted",
        submitted_by_participant: { name: "Kwame" }, submitted_by_user: null,
        vote_count: 2, voted_by_me: false, created_at: "2026-08-01T10:00:00Z",
      }],
    });
    vi.mocked(voteIdea).mockResolvedValue({
      ...baseSession,
      ideas: [{
        id: "idea-1", title: "Existing idea", description: "",
        status: "submitted", status_label: "Submitted",
        submitted_by_participant: { name: "Kwame" }, submitted_by_user: null,
        vote_count: 3, voted_by_me: true, created_at: "2026-08-01T10:00:00Z",
      }],
    });

    renderPage();
    expect(await screen.findByText("Existing idea")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /vote \(2\)/i }));
    expect(await screen.findByRole("button", { name: /voted \(3\)/i })).toBeInTheDocument();
  });

  it("shows a not-found message for an invalid or unopened session link", async () => {
    vi.mocked(getStoredParticipantToken).mockReturnValue(null);
    const { ApiError } = await import("../../lib/api");
    vi.mocked(getPublicSession).mockRejectedValue(new ApiError("Not found.", 404, {}));

    renderPage();
    expect(await screen.findByText(/invalid, or the session hasn't opened yet/i)).toBeInTheDocument();
  });
});
