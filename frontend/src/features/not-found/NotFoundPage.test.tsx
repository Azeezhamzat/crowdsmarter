import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { NotFoundPage } from "./NotFoundPage";

describe("NotFoundPage", () => {
  it("offers clear recovery destinations", () => {
    render(<MemoryRouter><NotFoundPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /destination is not part of this workspace/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /return to the public site/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /open my work/i })).toHaveAttribute("href", "/app");
  });
});
