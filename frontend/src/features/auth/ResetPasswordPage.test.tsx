import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { ResetPasswordPage } from "./ResetPasswordPage";

afterEach(() => { window.location.hash = ""; });

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><MemoryRouter><ResetPasswordPage /></MemoryRouter></QueryClientProvider>);
}

describe("ResetPasswordPage", () => {
  it("rejects an incomplete reset link", () => {
    renderPage();
    expect(screen.getByText("This reset link is incomplete. Request a new link.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset password" })).toBeDisabled();
  });

  it("validates matching passwords", async () => {
    window.location.hash = "uid=abc&token=token";
    renderPage();
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "A-secure-password-123" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "different-password" } });
    fireEvent.click(screen.getByRole("button", { name: "Reset password" }));
    expect(await screen.findByText("Passwords do not match.")).toBeInTheDocument();
  });
});
