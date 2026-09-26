import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
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
  it("submits a facilitation enquiry and shows its reference", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "CSRF cookie set." }), { status: 200, headers: { "content-type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Thank you. Your request has been received.", reference: "request-123" }), { status: 202, headers: { "content-type": "application/json" } }));

    renderPage();
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
    fireEvent.change(screen.getByLabelText("Full name *"), { target: { value: "Amina Yusuf" } });
    fireEvent.change(screen.getByLabelText("Work email *"), { target: { value: "AMINA@EXAMPLE.COM" } });
    fireEvent.change(screen.getByLabelText("Organisation *"), { target: { value: "Northstar Strategy" } });
    fireEvent.change(screen.getByLabelText("Role or job title"), { target: { value: "Strategy Director" } });
    fireEvent.change(screen.getByLabelText(/where is the decision getting difficult/i), { target: { value: "collective_intelligence" } });
    fireEvent.change(screen.getByLabelText(/what decision challenge/i), { target: { value: "We need to test options across uncertain futures." } });
    fireEvent.click(screen.getByLabelText(/I consent to being contacted/i));
    fireEvent.click(screen.getByRole("button", { name: /send decision enquiry/i }));

    expect(await screen.findByRole("heading", { name: /thank you/i })).toBeInTheDocument();
    expect(screen.getByText("request-123")).toBeInTheDocument();
    const requestBody = fetchMock.mock.calls[1]?.[1]?.body;
    expect(typeof requestBody).toBe("string");
    const submitted = JSON.parse(typeof requestBody === "string" ? requestBody : "{}") as Record<string, unknown>;
    expect(submitted.work_email).toBe("amina@example.com");
    expect(submitted.primary_need).toBe("collective_intelligence");
    expect(submitted.consent_to_contact).toBe(true);
  });

  it("requires a decision challenge and a problem area before submission", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    renderPage();

    fireEvent.change(screen.getByLabelText("Full name *"), { target: { value: "Amina Yusuf" } });
    fireEvent.change(screen.getByLabelText("Work email *"), { target: { value: "amina@example.com" } });
    fireEvent.change(screen.getByLabelText("Organisation *"), { target: { value: "Northstar Strategy" } });
    fireEvent.change(screen.getByLabelText(/what decision challenge/i), { target: { value: "Too little detail" } });
    fireEvent.click(screen.getByLabelText(/I consent to being contacted/i));
    fireEvent.click(screen.getByRole("button", { name: /send decision enquiry/i }));

    expect(await screen.findByText("Select the closest description of the decision challenge.")).toBeInTheDocument();
    expect(screen.getByText("Tell us enough about the decision to prepare a useful conversation.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
