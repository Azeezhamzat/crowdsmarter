import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import type { FacilitationSession } from "../../lib/types";
import { FacilitationSessionCard } from "./FacilitationSessionCard";

it("runs a timed agenda and links captured outputs to the live item", () => {
  const onAgendaAction = vi.fn();
  const onAgendaCreate = vi.fn();
  const onRecord = vi.fn();
  const user = { id: "owner-1", email: "facilitator@example.com", first_name: "", last_name: "" };
  const session = {
    id: "session-1",
    decision_id: "decision-1",
    title: "Criteria workshop",
    objective: "Agree the criteria.",
    agenda: "Frame, test, resolve.",
    participation_guidance: "Challenge claims, not people.",
    influence_boundary: "Decision criteria.",
    fixed_constraints: "Approved budget.",
    participation_channels: ["in_person"],
    missing_perspectives: "",
    accessibility_arrangements: "Provide accessible materials.",
    consent_boundary: "Ask before quoting input.",
    facilitator: user,
    starts_at: null,
    ends_at: null,
    status: "open",
    status_label: "Open",
    participants: [],
    agenda_items: [{
      id: "agenda-1",
      session_id: "session-1",
      title: "Frame the question",
      purpose: "Establish a shared boundary.",
      method: "Round robin",
      facilitator_prompt: "What must this decision resolve?",
      output_prompt: "Capture the agreed frame.",
      planned_minutes: 15,
      actual_minutes: 1,
      order: 1,
      status: "active",
      status_label: "Active",
      started_at: new Date(Date.now() - 60000).toISOString(),
      ended_at: null,
      record_count: 0,
      created_at: "2026-09-03T10:00:00Z",
      updated_at: "2026-09-03T10:01:00Z",
    }],
    records: [],
    authority_response: null,
    quality_review: null,
    can_manage: true,
    can_respond: true,
    closed_at: null,
    created_by: user,
    created_at: "2026-09-03T10:00:00Z",
    updated_at: "2026-09-03T10:01:00Z",
  } as FacilitationSession;

  render(
    <FacilitationSessionCard
      session={session}
      linkedOutputs={[]}
      busy={false}
      onAttendance={vi.fn()}
      onStatus={vi.fn()}
      onAgendaCreate={onAgendaCreate}
      onAgendaAction={onAgendaAction}
      onRecord={onRecord}
      onResponse={vi.fn()}
      onQualityReview={vi.fn()}
      onCreateFollowUp={vi.fn()}
      onDownloadReport={vi.fn()}
    />,
  );

  expect(screen.getByText("What must this decision resolve?", { exact: false })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Complete" }));
  expect(onAgendaAction).toHaveBeenCalledWith("agenda-1", "complete");

  fireEvent.click(screen.getByText("Capture a session record"));
  fireEvent.change(screen.getByLabelText("What was recorded"), {
    target: { value: "The group agreed the decision boundary." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Add to session record" }));
  expect(onRecord).toHaveBeenCalledWith(expect.objectContaining({
    agenda_item_id: "agenda-1",
    body: "The group agreed the decision boundary.",
  }));

  fireEvent.click(screen.getByText("Add an agenda item"));
  fireEvent.change(screen.getByLabelText("Activity"), { target: { value: "Test criteria" } });
  fireEvent.change(screen.getByLabelText("Minutes"), { target: { value: "25" } });
  fireEvent.click(screen.getByRole("button", { name: "Add to run of show" }));
  expect(onAgendaCreate).toHaveBeenCalledWith(expect.objectContaining({
    title: "Test criteria",
    planned_minutes: 25,
  }));
});
