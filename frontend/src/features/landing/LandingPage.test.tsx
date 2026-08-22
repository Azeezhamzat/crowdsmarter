import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { LandingPage } from "./LandingPage";

describe("LandingPage", () => {
  it("presents a coherent participatory-grantmaking proposition and demo conversion path", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /grantmaking your/i })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /book a fit assessment/i })[0]).toHaveAttribute("href", "/request-demo");
    expect(screen.getAllByRole("link", { name: "Sign in" })[0]).toHaveAttribute("href", "/login");
    expect(screen.getByText(/funder-owned records/i)).toBeInTheDocument();
    expect(screen.getByText(/where this comes from/i)).toBeInTheDocument();
    expect(screen.getByText(/participatory grantmaking and collective-intelligence research/i)).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /a grant round as a connected decision system/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Anticipate" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Deliberate" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Decide" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Act" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Learn" })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /learn the approach by running one real round/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Fit assessment" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Grant Round Sprint" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Adoption" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /start with one real, funded round/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /apply as a charter programme/i })).toHaveAttribute("href", "/request-demo");

    expect(screen.getByRole("heading", { name: /the distinction is continuity, not more software/i })).toBeInTheDocument();
    expect(screen.getByText(/when the process is fragmented/i)).toBeInTheDocument();
    expect(screen.getByText(/when the reasoning stays connected/i)).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /a funded round.*capability that remains/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Documented decision history" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /reusable round template/i })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /three disciplines shape how the round is designed/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Systems thinking" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Futures thinking" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Collective intelligence" })).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: /designed to support scrutiny, not obscure it/i })).toBeInTheDocument();
    expect(screen.getByText(/reviewer conflicts stay visible/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "hello@crowdsmarter.com" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));
    expect(screen.getByRole("link", { name: "Privacy enquiries" })).toHaveAttribute("href", expect.stringContaining("mailto:hello@crowdsmarter.com"));

    expect(screen.getByRole("heading", { name: /see whether crowdsmarter fits your next round/i })).toBeInTheDocument();
    expect(screen.getByText(/working with organisations across africa, europe, and the middle east/i)).toBeInTheDocument();
  });
});
