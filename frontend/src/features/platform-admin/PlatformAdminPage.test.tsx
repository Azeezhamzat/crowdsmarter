import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { fetchCurrentUser } from "../auth/api";
import { getPlatformConfiguration, getPlatformOverview, testAIProviderConnection } from "./api";
import { PlatformAdminPage } from "./PlatformAdminPage";

vi.mock("../auth/api", () => ({ fetchCurrentUser: vi.fn() }));
vi.mock("./api", () => ({
  getPlatformOverview: vi.fn(),
  listPlatformOrganisations: vi.fn(),
  listPlatformUsers: vi.fn(),
  listPlatformDemoRequests: vi.fn(),
  getPlatformConfiguration: vi.fn(),
  listPlatformAudit: vi.fn(),
  changePlatformUserState: vi.fn(),
  changePlatformAdministrator: vi.fn(),
  updatePlatformDemoRequestStatus: vi.fn(),
  updatePlatformConfiguration: vi.fn(),
  setAIProvider: vi.fn(),
  setAIProviderAPIKey: vi.fn(),
  clearAIProviderAPIKey: vi.fn(),
  testAIProviderConnection: vi.fn(),
}));

describe("PlatformAdminPage", () => {
  it("presents tenant governance without treating platform authority as membership", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      id: "admin-1",
      email: "hello@crowdsmarter.com",
      first_name: "Azeez",
      last_name: "Hamzat",
      is_platform_administrator: true,
    });
    vi.mocked(getPlatformOverview).mockResolvedValue({
      counts: {
        users: 12,
        active_users: 11,
        platform_administrators: 1,
        organisations: 4,
        active_organisations: 4,
        deactivated_organisations: 0,
        active_decisions: 9,
        pending_invitations: 2,
        new_demo_requests: 3,
        active_support_access: 0,
      },
      recent_audit_events: [],
      recent_demo_requests: [],
      active_support_access: [],
    });

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter><PlatformAdminPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: /tenant governance and operational control/i })).toBeInTheDocument();
    expect(await screen.findByText("4")).toBeInTheDocument();
    expect(screen.getByText(/tenant detail access is reasoned, time-bounded and audited/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Organisations" })).toBeInTheDocument();
  });

  it("shows the AI provider panel with no key configured by default", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      id: "admin-1",
      email: "hello@crowdsmarter.com",
      first_name: "Azeez",
      last_name: "Hamzat",
      is_platform_administrator: true,
    });
    vi.mocked(getPlatformOverview).mockResolvedValue({
      counts: {
        users: 12, active_users: 11, platform_administrators: 1, organisations: 4,
        active_organisations: 4, deactivated_organisations: 0, active_decisions: 9,
        pending_invitations: 2, new_demo_requests: 3, active_support_access: 0,
      },
      recent_audit_events: [], recent_demo_requests: [], active_support_access: [],
    });
    vi.mocked(getPlatformConfiguration).mockResolvedValue({
      public_contact_email: "hello@crowdsmarter.com", demo_email: "hello@crowdsmarter.com",
      support_email: "hello@crowdsmarter.com", privacy_email: "hello@crowdsmarter.com",
      security_email: "hello@crowdsmarter.com", notification_sender_email: "hello@crowdsmarter.com",
      support_access_max_hours: 8,
      ai_provider_key: "rules", ai_provider_key_label: "Transparent rules (no external service)",
      ai_provider_model: "claude-sonnet-5", ai_provider_api_key_is_set: false,
      updated_at: "2026-08-01T10:00:00Z",
    });

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter><PlatformAdminPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "Platform settings" }));

    expect(await screen.findByRole("heading", { name: /ai provider/i })).toBeInTheDocument();
    expect(screen.getAllByText("Transparent rules (no external service)").length).toBeGreaterThan(0);
    expect(screen.getByText("Not set")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /set api key/i })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /remove api key/i })).not.toBeInTheDocument();

    const providerSelect = screen.getByLabelText(/^provider$/i) as HTMLSelectElement;
    const optionLabels = [...providerSelect.options].map((option) => option.textContent);
    expect(optionLabels).toEqual([
      "Transparent rules (no external service)",
      "Anthropic Claude",
      "OpenAI ChatGPT",
      "Google Gemini",
    ]);

    fireEvent.change(providerSelect, { target: { value: "gemini" } });
    expect(screen.getByPlaceholderText("gemini-2.0-flash")).toBeInTheDocument();
    expect(screen.getByText(/set a google gemini api key below/i)).toBeInTheDocument();

    vi.mocked(testAIProviderConnection).mockResolvedValue({
      ok: true,
      detail: "Runs locally with no external API call, so there is nothing to connect to.",
      provider_key: "rules",
      provider_label: "Transparent rules review",
    });
    fireEvent.click(screen.getByRole("button", { name: /test connection/i }));
    expect(await screen.findByText(/runs locally with no external api call/i)).toBeInTheDocument();
  });
});
