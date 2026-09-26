import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { VerifyEmailChangePage } from "./VerifyEmailChangePage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><VerifyEmailChangePage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  window.history.replaceState(null, "", "/");
});

describe("VerifyEmailChangePage", () => {
  it("requires an explicit click before consuming the token", async () => {
    window.history.replaceState(null, "", "/verify-email-change#token=abc123");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "CSRF cookie set." }), { status: 200, headers: { "content-type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Email address changed successfully.", email: "new@example.com" }), { status: 200, headers: { "content-type": "application/json" } }));

    renderPage();
    expect(fetchMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirm new email address" }));

    expect(await screen.findByText(/sign-in email is now new@example.com/i)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const body = fetchMock.mock.calls[1]?.[1]?.body;
    expect(typeof body).toBe("string");
    expect(JSON.parse(typeof body === "string" ? body : "{}")).toEqual({ token: "abc123" });
  });

  it("does not enable confirmation when the token is missing", () => {
    window.history.replaceState(null, "", "/verify-email-change");
    renderPage();
    expect(screen.getByRole("button", { name: "Confirm new email address" })).toBeDisabled();
    expect(screen.getByText(/verification link is incomplete/i)).toBeInTheDocument();
  });
});
