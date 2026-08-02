import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "./LoginPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("LoginPage", () => {
  it("validates required credentials before sending a request", async () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(await screen.findByText("Enter your password.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Forgot password?" })).toHaveAttribute("href", "/forgot-password");
    expect(screen.getByRole("link", { name: "Request demo" })).toHaveAttribute("href", "/request-demo");
  });

  it("turns generic invalid credentials into actionable recovery guidance", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "CSRF cookie set." }), { status: 200, headers: { "content-type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Invalid email or password." }), { status: 400, headers: { "content-type": "application/json" } }));

    renderPage();
    fireEvent.change(screen.getByLabelText("Email address"), { target: { value: " PERSON@example.com " } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText(/we could not sign you in/i)).toBeInTheDocument();
    expect(screen.getByText(/email matching is case-insensitive/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /reset your password securely/i })).toHaveAttribute("href", "/forgot-password");
  });
});
