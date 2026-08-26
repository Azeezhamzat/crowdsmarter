import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it } from "vitest";

import { setLocale } from "../../lib/i18n";
import { LandingPage } from "./LandingPage";

afterEach(() => setLocale("en"));

describe("LandingPage", () => {
  it("presents a free, self-serve commons proposition ahead of the institutional demo path", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /decide together/i })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /start my commons, free/i })[0]).toHaveAttribute("href", "/signup");
    expect(screen.getAllByRole("link", { name: /book a fit assessment/i })[0]).toHaveAttribute("href", "/request-demo");
    expect(screen.getAllByRole("link", { name: "Sign in" })[0]).toHaveAttribute("href", "/login");
    expect(screen.getByText(/free to start, no card required/i)).toBeInTheDocument();
    expect(screen.getByText(/where this comes from/i)).toBeInTheDocument();
    expect(screen.getByText(/commons governance, participatory grantmaking/i)).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /any group's decision, as a connected system/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Anticipate" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Deliberate" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Decide" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Act" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Learn" })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /free to start, no institution required/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sign up free" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Bring your group" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Decide, together" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /prefer a guided rollout/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /apply as a charter programme/i })).toHaveAttribute("href", "/request-demo");

    expect(screen.getByRole("heading", { name: /the distinction is continuity, not more software/i })).toBeInTheDocument();
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

    expect(screen.getByRole("heading", { name: /start free, or bring us a real round/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Trust and security posture" })).toHaveAttribute("href", "/trust");
  });

  it("switches the visible copy to French and Portuguese and persists the choice", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);

    act(() => {
      fireEvent.change(screen.getByRole("combobox", { name: "Language" }), { target: { value: "fr" } });
    });
    expect(screen.getAllByRole("link", { name: "Se connecter" })[0]).toHaveAttribute("href", "/login");
    expect(screen.getAllByText(/plateforme/i).length).toBeGreaterThan(0);

    act(() => {
      fireEvent.change(screen.getByRole("combobox", { name: "Language" }), { target: { value: "pt" } });
    });
    expect(screen.getAllByRole("link", { name: "Entrar" })[0]).toHaveAttribute("href", "/login");
    expect(screen.getAllByText(/plataforma/i).length).toBeGreaterThan(0);

    expect(window.localStorage.getItem("crowdsmarter:locale")).toBe("pt");
  });
});
