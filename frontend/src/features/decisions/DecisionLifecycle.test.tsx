import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DecisionLifecycle } from "./DecisionLifecycle";

describe("DecisionLifecycle", () => {
  it("shows the complete required lifecycle without collapsing future states", () => {
    render(
      <DecisionLifecycle
        currentStatus="framing"
        nextTransition={{
          from_status: "framing",
          to_status: "open_for_contribution",
          enabled: true,
          blocked_reason: "",
          action: "transition",
        }}
      />,
    );

    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Framing")).toBeInTheDocument();
    expect(screen.getByText("Decision Finalised")).toBeInTheDocument();
    expect(screen.getByText("Lessons Learned")).toBeInTheDocument();
    expect(screen.getByText("Archived")).toBeInTheDocument();
  });

  it("makes a later-slice dependency visible instead of hiding the transition", () => {
    render(
      <DecisionLifecycle
        currentStatus="decision_finalised"
        nextTransition={{
          from_status: "decision_finalised",
          to_status: "commitment",
          enabled: false,
          blocked_reason: "Later records are required.",
          action: "transition",
        }}
      />,
    );

    expect(screen.getByText("Future phase required")).toBeInTheDocument();
    expect(screen.getByText("Ready for Decision")).toBeInTheDocument();
  });
});
