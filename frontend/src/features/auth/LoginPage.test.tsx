import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { setLocale } from "../../lib/i18n";
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

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  setLocale("en");
});

describe("LoginPage", () => {
  it("validates required credentials before sending a request", async () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(await screen.findByText("Enter your password.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Forgot password?" })).toHaveAttribute("href", "/forgot-password");
    expect(screen.getByRole("link", { name: "Start a commons" })).toHaveAttribute("href", "/signup");
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
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

  it("prompts for a second factor and completes sign-in after a valid code", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "CSRF cookie set." }), { status: 200, headers: { "content-type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ mfa_required: true }), { status: 200, headers: { "content-type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "u1", email: "person@example.com", first_name: "", last_name: "" }), { status: 200, headers: { "content-type": "application/json" } }));

    renderPage();
    fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "person@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "correct-password" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Enter your authentication code")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Authentication or backup code"), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: /verify and continue/i }));

    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(3));
    const verifyCall = vi.mocked(globalThis.fetch).mock.calls.at(2);
    const verifyTarget = verifyCall?.[0];
    const verifyUrl = typeof verifyTarget === "string"
      ? verifyTarget
      : verifyTarget instanceof URL
        ? verifyTarget.href
        : verifyTarget?.url;
    expect(verifyUrl).toContain("/auth/mfa/verify/");
  });

  it("keeps the dormant Arabic catalogue testable without exposing a selector", () => {
    setLocale("ar");
    renderPage();

    expect(screen.queryByRole("combobox", { name: "Language" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "تسجيل الدخول إلى CrowdSmarter" })).toBeInTheDocument();
    expect(screen.getByLabelText("عنوان البريد الإلكتروني")).toBeInTheDocument();
    expect(screen.getByLabelText("كلمة المرور")).toBeInTheDocument();
  });
});
