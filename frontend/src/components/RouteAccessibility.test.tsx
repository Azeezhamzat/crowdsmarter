import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { RouteAccessibility } from "./RouteAccessibility";

function NavigationFixture() {
  const navigate = useNavigate();
  return <button type="button" onClick={() => navigate("/login")}>Go to sign in</button>;
}

describe("RouteAccessibility", () => {
  it("provides a skip link, updates the title, announces routes, and focuses main content after navigation", async () => {
    vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<RouteAccessibility />}>
            <Route path="/" element={<><NavigationFixture /><main id="main-content" tabIndex={-1}>Home content</main></>} />
            <Route path="/login" element={<main id="main-content" tabIndex={-1}>Sign-in content</main>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /skip to main content/i })).toHaveAttribute("href", "#main-content");
    expect(document.title).toBe("Foresight-to-decision intelligence — The CrowdSmarter");

    fireEvent.click(screen.getByRole("button", { name: /go to sign in/i }));

    await waitFor(() => expect(document.title).toBe("Sign in — The CrowdSmarter"));
    await waitFor(() => expect(screen.getByText("Sign-in content")).toHaveFocus());
    expect(screen.getByText("Sign in", { selector: ".route-announcer" })).toBeInTheDocument();
  });
});
