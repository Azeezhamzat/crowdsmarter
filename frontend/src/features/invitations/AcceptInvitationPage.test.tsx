import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AcceptInvitationPage } from "./AcceptInvitationPage";
import { getInvitation } from "./api";

vi.mock("./api", () => ({
  getInvitation: vi.fn(),
  acceptInvitation: vi.fn(),
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/accept-invitation#token=test-secret"]}>
        <AcceptInvitationPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AcceptInvitationPage", () => {
  beforeEach(() => {
    vi.mocked(getInvitation).mockResolvedValue({
      organisation_id: "00000000-0000-0000-0000-000000000001",
      organisation_name: "Acme",
      email: "person@example.com",
      role: "contributor",
      role_label: "Contributor",
      status: "pending",
      expires_at: "2026-08-02T12:00:00Z",
      account_exists: false,
      current_user_email: null,
    });
  });

  it("requires matching passwords before creating an invited account", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "Join Acme" });

    fireEvent.change(screen.getByLabelText("Create password"), {
      target: { value: "first-password" },
    });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "different-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account and accept" }));

    expect(await screen.findByText("The passwords do not match.")).toBeInTheDocument();
  });
});
