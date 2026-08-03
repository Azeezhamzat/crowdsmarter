import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { LandingPage } from "./LandingPage";

describe("LandingPage", () => {
  it("presents the foresight-to-decision proposition and demo conversion path", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /turn uncertainty into accountable action/i })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /book a fit assessment/i })[0]).toHaveAttribute("href", "/request-demo");
    expect(screen.getAllByRole("link", { name: "Sign in" })[0]).toHaveAttribute("href", "/login");
    expect(screen.getByText(/customer-owned records/i)).toBeInTheDocument();
    expect(screen.getByText(/where this comes from/i)).toBeInTheDocument();
    expect(screen.getByText(/first cohort of founding-partner/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /missing connection between foresight and accountable decisions/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /move from emerging change to better judgement/i })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /signal sensing workflow/i })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /foresight-to-decision trace/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
    expect(screen.getByRole("link", { name: "Privacy enquiries" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));

    expect(screen.getByRole("tablist", { name: /workflow stages/i })).toHaveAttribute("aria-orientation", "horizontal");
    expect(screen.getByRole("tabpanel", { name: /anticipate/i })).toHaveAttribute("tabindex", "0");

    const senseTab = screen.getByRole("tab", { name: /anticipate/i });
    senseTab.focus();
    fireEvent.keyDown(senseTab, { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: /deliberate/i })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("img", { name: /systems and scenario interpretation/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /connect signals, systems, stakeholders, and uncertainty/i })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /designed for decisions where uncertainty and stakeholders both matter/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /investment and transformation/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /policy and programmes/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /resilience and scenarios/i })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /bring one real decision through a structured first engagement/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /fit assessment and demonstration/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /facilitated decision sprint/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /platform adoption and organisational scaling/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /frame the decision/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /decide and organise review/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /start with one real, important decision/i })).toBeInTheDocument();
    expect(screen.getByText(/founding partners run a first decision sprint/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /apply as a founding partner/i })).toHaveAttribute("href", "/request-demo");

    expect(screen.getByRole("heading", { name: /a concrete result, not just a workshop/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /a robustness analysis/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /a monitoring system/i })).toBeInTheDocument();

    expect(screen.getByText(/working with organisations across africa, europe, and the middle east/i)).toBeInTheDocument();
  });
});
