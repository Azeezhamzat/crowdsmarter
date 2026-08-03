import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AccountSettingsPage } from "./AccountSettingsPage";
import { beginMfaEnrollment, confirmMfaEnrollment, getMfaStatus } from "./api";

vi.mock("./api", () => ({
  fetchCurrentUser: vi.fn().mockResolvedValue({ id: "user-1", email: "person@example.com", first_name: "Amina", last_name: "Yusuf", is_staff: true }),
  updateProfile: vi.fn(),
  changePassword: vi.fn(),
  getMfaStatus: vi.fn().mockResolvedValue({ is_enabled: false }),
  beginMfaEnrollment: vi.fn(),
  confirmMfaEnrollment: vi.fn(),
  disableMfa: vi.fn(),
}));

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><AccountSettingsPage /></QueryClientProvider>);
}

describe("AccountSettingsPage", () => {
  it("keeps email read-only and validates password confirmation", async () => {
    renderPage();
    expect(await screen.findByDisplayValue("person@example.com")).toHaveAttribute("readonly");
    expect(screen.getByRole("link", { name: /open system administration/i })).toHaveAttribute("href", "http://localhost:8000/admin/");
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
    fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "Current-password-123" } });
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "A-new-secure-password-456" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "different" } });
    fireEvent.click(screen.getByRole("button", { name: "Change password" }));
    expect(await screen.findByText("Passwords do not match.")).toBeInTheDocument();
  });

  it("walks through enrolling two-factor authentication", async () => {
    vi.mocked(getMfaStatus).mockResolvedValue({ is_enabled: false });
    vi.mocked(beginMfaEnrollment).mockResolvedValue({
      secret: "JBSWY3DPEHPK3PXP",
      provisioning_uri: "otpauth://totp/CrowdSmarter:person@example.com?secret=JBSWY3DPEHPK3PXP",
    });
    vi.mocked(confirmMfaEnrollment).mockResolvedValue({
      backup_codes: ["ABCD-1234", "EFGH-5678"],
    });

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Enable two-factor authentication" }));
    expect(await screen.findByText("JBSWY3DPEHPK3PXP")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Enter the 6-digit code it shows"), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirm and enable" }));

    expect(await screen.findByText(/save these backup codes now/i)).toBeInTheDocument();
    expect(screen.getByText("ABCD-1234")).toBeInTheDocument();
    expect(screen.getByText("EFGH-5678")).toBeInTheDocument();
    expect(confirmMfaEnrollment).toHaveBeenCalledWith("123456");
  });
});
