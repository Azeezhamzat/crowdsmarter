import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { ForgotPasswordPage } from "./ForgotPasswordPage";

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><MemoryRouter><ForgotPasswordPage /></MemoryRouter></QueryClientProvider>);
}

describe("ForgotPasswordPage", () => {
  it("validates the email address before requesting recovery", async () => {
    renderPage();
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
    fireEvent.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
  });
});
