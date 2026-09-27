import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it } from "vitest";

import { setLocale } from "../../lib/i18n";
import { LandingPage } from "./LandingPage";

afterEach(() => {
  cleanup();
  setLocale("en");
});

describe("LandingPage", () => {
  it("presents facilitation first and the platform as supporting infrastructure", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /make difficult decisions together/i })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Set up a commons" })[0]).toHaveAttribute("href", "/signup");
    expect(screen.getAllByRole("link", { name: "Discuss a decision" })[0]).toHaveAttribute("href", "/request-demo");
    expect(screen.getAllByRole("link", { name: "Sign in" })[0]).toHaveAttribute("href", "/login");
    expect(screen.getByText(/facilitation shapes the process/i)).toBeInTheDocument();
    expect(screen.getByText(/where this comes from/i)).toBeInTheDocument();
    expect(screen.getByText(/commons governance, participatory grantmaking/i)).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /a facilitated decision, supported by a connected system/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Anticipate" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Deliberate" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Decide" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Act" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Learn" })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /facilitation comes first/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Frame the decision" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Convene the right people" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Reach an accountable decision" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /run a facilitated charter grant round/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /apply as a charter programme/i })).toHaveAttribute("href", "/request-demo");

    expect(screen.getByRole("heading", { name: /the distinction is facilitated continuity/i })).toBeInTheDocument();
    expect(screen.getByText(/when the process is fragmented/i)).toBeInTheDocument();
    expect(screen.getByText(/when the reasoning stays connected/i)).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /a decision, and capability that remains/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Documented decision history" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /reusable decision template/i })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /three disciplines shape how the decision is designed/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Systems thinking" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Futures thinking" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Collective intelligence" })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /designed to support scrutiny, not obscure it/i })).toBeInTheDocument();
    expect(screen.getByText(/reviewer conflicts stay visible/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
    expect(screen.getByRole("link", { name: "Privacy enquiries" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));

    expect(screen.getByRole("heading", { name: /bring a decision that needs better participation/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Trust and security posture" })).toHaveAttribute("href", "/trust");
    expect(screen.queryByText(/\bfree\b/i)).not.toBeInTheDocument();
  });

  it("does not expose the incomplete language selector", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);

    expect(screen.queryByRole("combobox", { name: "Language" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Sign in" })[0]).toBeInTheDocument();
    expect(document.documentElement).toHaveAttribute("lang", "en");
    expect(document.documentElement).toHaveAttribute("dir", "ltr");
  });
});
