import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { fetchCurrentUser, logoutSession } from "../features/auth/api";
import { listNotifications } from "../features/notifications/api";
import { listOrganisations } from "../features/organisations/api";
import { AppShell } from "./AppShell";

vi.mock("../features/auth/api", () => ({ fetchCurrentUser: vi.fn(), logoutSession: vi.fn() }));
vi.mock("../features/notifications/api", () => ({ listNotifications: vi.fn() }));
vi.mock("../features/organisations/api", () => ({ listOrganisations: vi.fn() }));

describe("AppShell", () => {
  it("opens quick navigation with the keyboard shortcut", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({ id: "u1", email: "azeez@example.com", first_name: "Azeez", last_name: "Hamzat" });
    vi.mocked(logoutSession).mockResolvedValue(undefined);
    vi.mocked(listNotifications).mockResolvedValue({ unread_count: 2, notifications: [] });
    vi.mocked(listOrganisations).mockResolvedValue([{ id: "o1", name: "AgriNova", slug: "agrinova", description: "", website_url: "", brand_name: "", primary_colour: "#244A5A", invitation_policy: "owners_and_admins", default_invitation_role: "contributor", retention_days: null, status: "active", deactivated_at: null, current_user_role: "owner", created_at: "2026-07-20T10:00:00Z", updated_at: "2026-07-20T10:00:00Z" }]);

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/app"]}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/app" element={<p>Dashboard content</p>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText("Dashboard content")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(await screen.findByRole("dialog", { name: "Quick navigation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^AgriNovaowner · organisation workspace$/i })).toBeInTheDocument();
  });
});
