import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  consumeMagicLink,
  getMyApplications,
  getStoredApplicantToken,
  requestMagicLink,
  submitProgressReport,
} from "./api";
import { MyApplicationsPage } from "./MyApplicationsPage";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return {
    ...actual,
    getStoredApplicantToken: vi.fn(),
    requestMagicLink: vi.fn(),
    consumeMagicLink: vi.fn(),
    getMyApplications: vi.fn(),
    submitProgressReport: vi.fn(),
  };
});

function renderPage(initialPath = "/my-applications") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes><Route path="/my-applications" element={<MyApplicationsPage />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const fundedApplication = {
  id: "idea-1",
  title: "Well project",
  status: "promoted" as const,
  status_label: "Promoted",
  requested_amount: null,
  session_title: "Grants round",
  organisation_name: "AgriNova",
  created_at: "2026-01-01T00:00:00Z",
  outcome: {
    eligibility_status: "eligible" as const,
    eligibility_status_label: "Eligible",
    outcome_status: "funded" as const,
    outcome_status_label: "Funded",
    awarded_amount: "500.00",
    outcome_note: "",
  },
  can_submit_progress_report: true,
  progress_reports: [] as { id: string; body: string; created_at: string }[],
};

afterEach(() => vi.restoreAllMocks());

describe("MyApplicationsPage", () => {
  it("requests a magic link when no session exists", async () => {
    vi.mocked(getStoredApplicantToken).mockReturnValue(null);
    vi.mocked(requestMagicLink).mockResolvedValue(undefined);

    renderPage();

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "amina@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: /email me a link/i }));

    await waitFor(() => expect(requestMagicLink).toHaveBeenCalledWith({ email: "amina@example.com", name: "" }));
    expect(await screen.findByText(/sign-in link is on its way/i)).toBeInTheDocument();
  });

  it("consumes a magic-link token from the URL and lists applications", async () => {
    vi.mocked(getStoredApplicantToken).mockReturnValue(null);
    vi.mocked(consumeMagicLink).mockResolvedValue({ applicant_token: "tok-1", email: "amina@example.com", name: "Amina" });
    vi.mocked(getMyApplications).mockResolvedValue({
      email: "amina@example.com",
      name: "Amina",
      applications: [fundedApplication],
    });

    renderPage("/my-applications#token=abc123");

    await waitFor(() => expect(consumeMagicLink).toHaveBeenCalledWith("abc123"));
    expect(await screen.findByText("Well project")).toBeInTheDocument();
    expect(screen.getByText(/funded/i)).toBeInTheDocument();
  });

  it("submits a progress report for a funded application", async () => {
    vi.mocked(getStoredApplicantToken).mockReturnValue("tok-1");
    vi.mocked(getMyApplications).mockResolvedValue({
      email: "amina@example.com",
      name: "Amina",
      applications: [fundedApplication],
    });
    vi.mocked(submitProgressReport).mockResolvedValue({
      email: "amina@example.com",
      name: "Amina",
      applications: [
        {
          ...fundedApplication,
          progress_reports: [{ id: "report-1", body: "We drilled the well.", created_at: "2026-02-01T00:00:00Z" }],
        },
      ],
    });

    renderPage();
    expect(await screen.findByText("Well project")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/post a progress update/i), { target: { value: "We drilled the well." } });
    fireEvent.click(screen.getByRole("button", { name: /post update/i }));

    await waitFor(() => expect(submitProgressReport).toHaveBeenCalledWith("idea-1", "We drilled the well."));
    expect(await screen.findByText("We drilled the well.")).toBeInTheDocument();
  });
});
