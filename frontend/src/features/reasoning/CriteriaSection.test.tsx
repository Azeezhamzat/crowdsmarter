import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CriteriaSection } from "./CriteriaSection";

function renderSection() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <CriteriaSection
        decisionId="00000000-0000-0000-0000-000000000001"
        canContribute
        memberships={[]}
      />
    </QueryClientProvider>,
  );
}

describe("CriteriaSection", () => {
  it("requires a meaningful title and description", async () => {
    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "Add criterion" }));

    expect(await screen.findByText("Enter a concise criterion title.")).toBeInTheDocument();
    expect(
      screen.getByText("Explain what this criterion measures and why it matters."),
    ).toBeInTheDocument();
  });

  it("requires a threshold when marked must-have", async () => {
    renderSection();
    fireEvent.click(screen.getByLabelText(/must-have/i));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Budget ceiling" } });
    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "The option must fit within the approved budget envelope." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add criterion" }));

    expect(
      await screen.findByText("A must-have criterion requires a stated threshold."),
    ).toBeInTheDocument();
  });
});
