import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { LandingPage } from "./LandingPage";

describe("LandingPage", () => {
  it("presents the foresight-to-decision proposition and demo conversion path", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /turn uncertainty into accountable action/i })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /request a tailored demo|request a demo/i })[0]).toHaveAttribute("href", "/request-demo");
    expect(screen.getAllByRole("link", { name: "Sign in" })[0]).toHaveAttribute("href", "/login");
    expect(screen.getByText(/customer-owned records/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /missing connection between foresight and accountable decisions/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /move from emerging change to better judgement/i })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /signal sensing workflow/i })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /foresight-to-decision trace/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
    expect(screen.getByRole("link", { name: "Privacy enquiries" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));

    expect(screen.getByRole("tablist", { name: /workflow stages/i })).toHaveAttribute("aria-orientation", "horizontal");
    expect(screen.getByRole("tabpanel", { name: /sense/i })).toHaveAttribute("tabindex", "0");

    const senseTab = screen.getByRole("tab", { name: /sense/i });
    senseTab.focus();
    fireEvent.keyDown(senseTab, { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: /interpret/i })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("img", { name: /systems and scenario interpretation/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /connect signals, systems, stakeholders, and uncertainty/i })).toBeInTheDocument();
  });
});
