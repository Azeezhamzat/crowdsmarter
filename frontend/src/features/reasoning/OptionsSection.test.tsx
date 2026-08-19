import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OptionsSection } from "./OptionsSection";

function renderSection(templateKey?: string | null) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <OptionsSection
        decisionId="00000000-0000-0000-0000-000000000001"
        canContribute
        templateKey={templateKey}
      />
    </QueryClientProvider>,
  );
}

describe("OptionsSection", () => {
  it("requires a meaningful title and description", async () => {
    renderSection();
    fireEvent.click(screen.getByRole("button", { name: "Add option" }));

    expect(await screen.findByText("Enter a clear option title.")).toBeInTheDocument();
    expect(screen.getByText("Describe what this option involves.")).toBeInTheDocument();
  });

  it("requires experiment scope when marked as an experiment", async () => {
    renderSection();
    fireEvent.click(screen.getByLabelText(/minimum-viable experiment/i));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Run a pilot" } });
    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "Test the approach with a limited group before wider rollout." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add option" }));

    expect(
      await screen.findByText("Describe the bounded experiment this option represents."),
    ).toBeInTheDocument();
  });

  it("renders grant-round terminology when linked to a grant round", async () => {
    renderSection("grant_round");
    expect(await screen.findByRole("heading", { name: "Applications" })).toBeInTheDocument();
    expect(screen.getByLabelText("Requested amount")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add application" })).toBeInTheDocument();
  });
});
