import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RequestDemoPage } from "./RequestDemoPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><RequestDemoPage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("RequestDemoPage", () => {
  it("submits a tailored demo request and shows its reference", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "CSRF cookie set." }), { status: 200, headers: { "content-type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Thank you. Your request has been received.", reference: "request-123" }), { status: 202, headers: { "content-type": "application/json" } }));

    renderPage();
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
    fireEvent.change(screen.getByLabelText("Full name *"), { target: { value: "Amina Yusuf" } });
    fireEvent.change(screen.getByLabelText("Work email *"), { target: { value: "AMINA@EXAMPLE.COM" } });
    fireEvent.change(screen.getByLabelText("Organisation *"), { target: { value: "Northstar Strategy" } });
    fireEvent.change(screen.getByLabelText("Role or job title"), { target: { value: "Strategy Director" } });
    fireEvent.change(screen.getByLabelText(/what decision challenge/i), { target: { value: "We need to test options across uncertain futures." } });
    fireEvent.click(screen.getByLabelText(/I consent to being contacted/i));
    fireEvent.click(screen.getByRole("button", { name: /request demonstration/i }));

    expect(await screen.findByRole("heading", { name: /thank you/i })).toBeInTheDocument();
    expect(screen.getByText("request-123")).toBeInTheDocument();
    const submitted = JSON.parse(String(fetchMock.mock.calls[1]?.[1]?.body));
    expect(submitted.work_email).toBe("amina@example.com");
    expect(submitted.consent_to_contact).toBe(true);
  });
});
