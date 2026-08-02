import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { getPersonalContributions } from "./api";
import { MyContributionsPage } from "./MyContributionsPage";

vi.mock("./api", () => ({
  getContributionPreference: vi.fn(),
  getPersonalContributions: vi.fn(),
  updateContributionPreference: vi.fn(),
}));

describe("MyContributionsPage", () => {
  it("provides a cross-organisation contribution inbox", async () => {
    vi.mocked(getPersonalContributions).mockResolvedValue({
      summary: { total: 0, overdue: 0, returned: 0, submitted: 0, awaiting_review: 0 },
      requests: [],
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><MyContributionsPage /></MemoryRouter></QueryClientProvider>);
    expect(await screen.findByRole("heading", { name: "Your contribution work" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "No active contribution work" })).toBeInTheDocument();
  });
});
