import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AccountSettingsPage } from "./AccountSettingsPage";

vi.mock("./api", () => ({
  fetchCurrentUser: vi.fn().mockResolvedValue({ id: "user-1", email: "person@example.com", first_name: "Amina", last_name: "Yusuf" }),
  updateProfile: vi.fn(),
  changePassword: vi.fn(),
}));

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><AccountSettingsPage /></QueryClientProvider>);
}

describe("AccountSettingsPage", () => {
  it("keeps email read-only and validates password confirmation", async () => {
    renderPage();
    expect(await screen.findByDisplayValue("person@example.com")).toHaveAttribute("readonly");
    fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "Current-password-123" } });
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "A-new-secure-password-456" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "different" } });
    fireEvent.click(screen.getByRole("button", { name: "Change password" }));
    expect(await screen.findByText("Passwords do not match.")).toBeInTheDocument();
  });
});
