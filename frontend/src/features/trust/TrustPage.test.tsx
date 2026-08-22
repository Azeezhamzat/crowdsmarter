import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { TrustPage } from "./TrustPage";

describe("TrustPage", () => {
  it("states what's in place and what isn't, without claiming certification", () => {
    render(<MemoryRouter><TrustPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /what's actually true today/i })).toBeInTheDocument();
    expect(screen.getByText(/csrf-protected, session-authenticated everywhere/i)).toBeInTheDocument();
    expect(screen.getByText(/reviewer conflicts stay visible/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Not yet true." })).toBeInTheDocument();
    expect(screen.getByText(/no formal third-party certification/i)).toBeInTheDocument();
    expect(screen.getByText(/not something code alone can produce/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Privacy enquiries" })).toHaveAttribute("href", expect.stringContaining("mailto:"));
  });
});
