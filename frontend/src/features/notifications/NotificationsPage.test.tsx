import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { listNotifications, markAllNotificationsRead, markNotificationRead } from "./api";
import { NotificationsPage } from "./NotificationsPage";

vi.mock("./api", () => ({
  listNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}));

describe("NotificationsPage", () => {
  it("shows attributable workflow notifications", async () => {
    vi.mocked(listNotifications).mockResolvedValue({
      unread_count: 1,
      notifications: [{
        id: "n1", organisation_id: "o1", decision_id: "d1", kind: "assignment", kind_label: "Assignment",
        title: "You own a risk", message: "Review the mitigation plan.", url: "/decisions/d1/reasoning/risks",
        metadata: {}, is_read: false, read_at: null, created_at: "2026-07-26T12:00:00Z",
      }],
    });
    vi.mocked(markNotificationRead).mockResolvedValue({
      id: "n1", organisation_id: "o1", decision_id: "d1", kind: "assignment", kind_label: "Assignment",
      title: "You own a risk", message: "Review the mitigation plan.", url: "/decisions/d1/reasoning/risks",
      metadata: {}, is_read: true, read_at: "2026-07-26T12:05:00Z", created_at: "2026-07-26T12:00:00Z",
    });
    vi.mocked(markAllNotificationsRead).mockResolvedValue({ marked_read: 1 });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/notifications"]}>
          <Routes><Route path="/notifications" element={<NotificationsPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(await screen.findByRole("heading", { name: "You own a risk" })).toBeInTheDocument();
    expect(screen.getByText("Review the mitigation plan.")).toBeInTheDocument();
  });
});
