import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { setLocale } from "../../lib/i18n";
import { SignupPage } from "./SignupPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/signup"]}>
        <Routes>
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/organisations/:organisationId/sessions" element={<div>Sessions landed</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  setLocale("en");
});

describe("SignupPage", () => {
  it("validates required fields before sending a request", async () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: /start my commons/i }));

    expect(await screen.findByText("Enter your name.")).toBeInTheDocument();
    expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Use at least 8 characters.")).toBeInTheDocument();
    expect(screen.getByText("Give your commons a name.")).toBeInTheDocument();
  });

  it("creates an account and its first commons, then lands on the sessions page", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "CSRF cookie set." }), { status: 200, headers: { "content-type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        user: { id: "u1", email: "amara@example.com", first_name: "Amara", last_name: "Diallo" },
        organisation: { id: "org-1", name: "Riverside Climate Commons", slug: "riverside-climate-commons" },
      }), { status: 201, headers: { "content-type": "application/json" } }));

    renderPage();
    fireEvent.change(screen.getByLabelText("Your name"), { target: { value: "Amara Diallo" } });
    fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "amara@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "a-genuinely-long-passphrase" } });
    fireEvent.change(screen.getByLabelText("Name your commons"), { target: { value: "Riverside Climate Commons" } });
    fireEvent.click(screen.getByRole("button", { name: /start my commons/i }));

    expect(await screen.findByText("Sessions landed")).toBeInTheDocument();
  });

  it("surfaces a duplicate-email error from the server", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "CSRF cookie set." }), { status: 200, headers: { "content-type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ email: ["An account already exists for this email. Sign in instead."] }), { status: 400, headers: { "content-type": "application/json" } }));

    renderPage();
    fireEvent.change(screen.getByLabelText("Your name"), { target: { value: "Amara Diallo" } });
    fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "taken@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "a-genuinely-long-passphrase" } });
    fireEvent.change(screen.getByLabelText("Name your commons"), { target: { value: "Another Commons" } });
    fireEvent.click(screen.getByRole("button", { name: /start my commons/i }));

    await waitFor(() => expect(screen.getByText(/an account already exists/i)).toBeInTheDocument());
  });

  it("links back to sign in for people who already have an account", () => {
    renderPage();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/login");
  });
});
