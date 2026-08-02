import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { fetchCurrentUser } from "../auth/api";
import { getPlatformOverview } from "./api";
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
});
