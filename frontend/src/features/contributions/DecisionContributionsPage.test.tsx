import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { getDecision } from "../decisions/api";
import { listParticipants } from "../participants/api";
import {
  createFacilitationRecord,
  createFacilitationSession,
  getDecisionContributions,
  listFacilitationSessions,
  saveFacilitationAuthorityResponse,
  saveFacilitationQualityReview,
} from "./api";
import { DecisionContributionsPage } from "./DecisionContributionsPage";

vi.mock("../decisions/api", () => ({ getDecision: vi.fn() }));
vi.mock("../participants/api", () => ({ listParticipants: vi.fn() }));
vi.mock("./api", () => ({
  contributionAction: vi.fn(),
  createContributionRequest: vi.fn(),
  createFacilitationAgendaItem: vi.fn(),
  createFacilitationSession: vi.fn(),
  createFacilitationRecord: vi.fn(),
  downloadFacilitationReport: vi.fn(),
  facilitationAgendaItemAction: vi.fn(),
  getDecisionContributions: vi.fn(),
  listFacilitationSessions: vi.fn(),
  reviewContribution: vi.fn(),
  saveContributionDraft: vi.fn(),
  saveFacilitationAuthorityResponse: vi.fn(),
  saveFacilitationQualityReview: vi.fn(),
  submitContribution: vi.fn(),
  updateContributionRequest: vi.fn(),
  updateFacilitationSessionStatus: vi.fn(),
  updateSessionAttendance: vi.fn(),
}));

describe("DecisionContributionsPage", () => {
  afterEach(() => vi.clearAllMocks());

  it("shows governed requests and participation coverage", async () => {
    vi.mocked(getDecision).mockResolvedValue({
      id: "decision-1",
      organisation_id: "organisation-1",
      title: "Regional resilience decision",
      status_label: "Open for Contribution",
    } as never);
    vi.mocked(listParticipants).mockResolvedValue([]);
    vi.mocked(listFacilitationSessions).mockResolvedValue([]);
    vi.mocked(getDecisionContributions).mockResolvedValue({
      can_manage: true,
      participation: {
        participant_count: 3,
        assigned_count: 2,
        submitted_count: 1,
        coverage_percent: 67,
        unassigned_participants: [{ id: "person-3", email: "unassigned@example.com", role: "reviewer" }],
        role_counts: { contributor: 2, reviewer: 1 },
      },
      requests: [{
        id: "request-1",
        organisation_id: "organisation-1",
        organisation_name: "Resilience Lab",
        decision_id: "decision-1",
        decision_title: "Regional resilience decision",
        option_id: null,
        session_id: null,
        session_title: null,
        requested_by: { id: "owner", email: "owner@example.com", first_name: "", last_name: "" },
        assignee: { id: "person-1", email: "contributor@example.com", first_name: "", last_name: "" },
        reviewer: null,
        kind: "evidence",
        kind_label: "Evidence",
        title: "Validate implementation evidence",
        instructions: "Check the source, limits, and recency.",
        priority: "high",
        priority_label: "High",
        status: "open",
        status_label: "Open",
        due_at: null,
        opened_at: null,
        submitted_at: null,
        reviewed_at: null,
        completed_at: null,
        cancelled_at: null,
        submissions: [],
        reviews: [],
        can_work: false,
        can_review: false,
        can_manage: true,
        is_overdue: false,
        created_at: "2026-08-01T10:00:00Z",
        updated_at: "2026-08-01T10:00:00Z",
      }],
    });

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/decisions/decision-1/contributions"]}>
          <Routes><Route path="/decisions/:decisionId/contributions" element={<DecisionContributionsPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Regional resilience decision" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Validate implementation evidence" })).toBeInTheDocument();
    expect(screen.getByText("67%")).toBeInTheDocument();
    expect(screen.getByText(/unassigned@example.com/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Create contribution request" })).toBeInTheDocument();
  });

  it("turns a facilitation brief into role-aware sessions and accountable follow-up", async () => {
    const facilitator = { id: "facilitator-1", email: "facilitator@example.com", first_name: "", last_name: "" };
    const contributor = { id: "contributor-1", email: "contributor@example.com", first_name: "", last_name: "" };
    const observer = { id: "observer-1", email: "observer@example.com", first_name: "", last_name: "" };
    const session = {
      id: "session-1",
      decision_id: "decision-1",
      title: "Evidence workshop",
      objective: "Identify the evidence that can change the decision.",
      agenda: "Review the frame, test the evidence, and name the gaps.",
      participation_guidance: "Read the evidence first. Challenge claims, not people, and state uncertainty.",
      influence_boundary: "Evidence weighting and implementation conditions.",
      fixed_constraints: "The approved budget and statutory duties.",
      participation_channels: ["in_person"],
      missing_perspectives: "People unable to attend in person.",
      accessibility_arrangements: "Telephone participation and accessible materials.",
      consent_boundary: "Ask before attributing or quoting input.",
      facilitator,
      starts_at: "2026-09-15T09:00:00Z",
      ends_at: "2026-09-15T10:30:00Z",
      status: "closed",
      status_label: "Closed",
      participants: [{
        id: "session-participant-1",
        user: observer,
        display_label: "observer@example.com",
        external_label: "",
        stakeholder_group: "",
        role: "observer",
        role_label: "Observer",
        attendance: "attended",
        attendance_label: "Attended",
        created_at: "2026-09-01T10:00:00Z",
        updated_at: "2026-09-01T10:00:00Z",
      }],
      agenda_items: [],
      records: [],
      authority_response: null,
      quality_review: null,
      can_manage: true,
      can_respond: true,
      closed_at: "2026-09-15T10:30:00Z",
      created_by: facilitator,
      created_at: "2026-09-01T10:00:00Z",
      updated_at: "2026-09-15T10:30:00Z",
    };

    vi.mocked(getDecision).mockResolvedValue({
      id: "decision-1",
      organisation_id: "organisation-1",
      title: "Regional resilience decision",
      decision_question: "Which intervention should be commissioned?",
      purpose: "Choose an intervention that can be implemented this year.",
      scope: "Regional prevention services within the approved budget.",
      target_decision_date: "2026-10-01",
      status_label: "Open for Contribution",
      position_summary: { required_authorities: 1 },
    } as never);
    vi.mocked(listParticipants).mockResolvedValue([
      { id: "participant-facilitator", user: facilitator, role: "reviewer", role_label: "Reviewer", status: "active" },
      { id: "participant-contributor", user: contributor, role: "contributor", role_label: "Contributor", status: "active" },
      { id: "participant-observer", user: observer, role: "observer", role_label: "Observer", status: "active" },
    ] as never);
    vi.mocked(listFacilitationSessions).mockResolvedValue([session] as never);
    vi.mocked(createFacilitationSession).mockResolvedValue(session as never);
    vi.mocked(createFacilitationRecord).mockResolvedValue({ id: "record-1" } as never);
    vi.mocked(saveFacilitationAuthorityResponse).mockResolvedValue({ id: "response-1" } as never);
    vi.mocked(saveFacilitationQualityReview).mockResolvedValue({ id: "quality-1" } as never);
    vi.mocked(getDecisionContributions).mockResolvedValue({
      can_manage: true,
      participation: {
        participant_count: 3,
        assigned_count: 1,
        submitted_count: 0,
        coverage_percent: 33,
        unassigned_participants: [],
        role_counts: { contributor: 1, reviewer: 1, observer: 1 },
      },
      requests: [{
        id: "request-1",
        organisation_id: "organisation-1",
        organisation_name: "Resilience Lab",
        decision_id: "decision-1",
        decision_title: "Regional resilience decision",
        option_id: null,
        session_id: "session-1",
        session_title: "Evidence workshop",
        requested_by: facilitator,
        assignee: contributor,
        reviewer: facilitator,
        kind: "evidence",
        kind_label: "Evidence",
        title: "Document unresolved assumptions",
        instructions: "Record the remaining evidence gaps and their owners.",
        priority: "normal",
        priority_label: "Normal",
        status: "open",
        status_label: "Open",
        due_at: null,
        opened_at: "2026-09-15T10:30:00Z",
        submitted_at: null,
        reviewed_at: null,
        completed_at: null,
        cancelled_at: null,
        submissions: [],
        reviews: [],
        can_work: false,
        can_review: false,
        can_manage: true,
        is_overdue: false,
        created_at: "2026-09-15T10:30:00Z",
        updated_at: "2026-09-15T10:30:00Z",
      }],
    });

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/decisions/decision-1/contributions"]}>
          <Routes><Route path="/decisions/:decisionId/contributions" element={<DecisionContributionsPage />} /></Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(await screen.findByRole("tab", { name: "Facilitation sessions" }));
    expect(screen.getByText("6/6 foundations recorded")).toBeInTheDocument();
    expect(screen.getByText(/Challenge claims, not people/)).toBeInTheDocument();
    expect(screen.getByLabelText("Attendance for observer@example.com")).toHaveValue("attended");
    expect(screen.getByText("Document unresolved assumptions")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Review session quality"));
    fireEvent.change(screen.getByLabelText("What worked and why"), { target: { value: "The influence boundary stayed visible." } });
    fireEvent.change(screen.getByLabelText("What to improve next time"), { target: { value: "Give telephone participants more time." } });
    fireEvent.click(screen.getByRole("button", { name: "Save quality review" }));
    await waitFor(() => expect(saveFacilitationQualityReview).toHaveBeenCalledWith(
      "session-1",
      expect.objectContaining({
        inclusion_score: 3,
        what_worked: "The influence boundary stayed visible.",
        improve_next_time: "Give telephone participants more time.",
      }),
    ));

    fireEvent.click(screen.getByText("Capture a session record"));
    fireEvent.change(screen.getByLabelText("What was recorded"), { target: { value: "The group agreed to test the evidence threshold." } });
    fireEvent.click(screen.getByRole("button", { name: "Add to session record" }));
    await waitFor(() => expect(createFacilitationRecord).toHaveBeenCalledWith(
      "session-1",
      expect.objectContaining({
        kind: "agreement",
        body: "The group agreed to test the evidence threshold.",
        channel: "in_person",
        attribution: "anonymous",
      }),
    ));

    fireEvent.change(screen.getByLabelText("What we heard"), { target: { value: "The evidence threshold needs testing." } });
    fireEvent.change(screen.getByLabelText("What changed because of the input"), { target: { value: "A validation step was added." } });
    fireEvent.change(screen.getByLabelText("What happens next"), { target: { value: "The evidence lead will report next week." } });
    fireEvent.click(screen.getByRole("button", { name: "Publish response" }));
    await waitFor(() => expect(saveFacilitationAuthorityResponse).toHaveBeenCalledWith(
      "session-1",
      expect.objectContaining({
        what_we_heard: "The evidence threshold needs testing.",
        what_changed: "A validation step was added.",
        next_steps: "The evidence lead will report next week.",
        publish: true,
      }),
    ));

    fireEvent.click(screen.getByRole("button", { name: "Create accountable follow-up" }));
    expect(screen.getByLabelText("Facilitation session")).toHaveValue("session-1");
    expect(screen.getByLabelText("Title")).toHaveValue("Output from Evidence workshop");

    fireEvent.click(screen.getByRole("tab", { name: "Facilitation sessions" }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Decision framing workshop" } });
    fireEvent.change(screen.getByLabelText("Facilitator"), { target: { value: "facilitator-1" } });
    fireEvent.change(screen.getByLabelText("Objective"), { target: { value: "Agree the decision frame." } });
    fireEvent.change(screen.getByLabelText("What participants can influence"), { target: { value: "The decision criteria and implementation conditions." } });
    fireEvent.change(screen.getByLabelText("What is fixed"), { target: { value: "The statutory deadline and approved budget." } });
    fireEvent.change(screen.getByLabelText("Accessibility arrangements"), { target: { value: "Offer telephone participation and accessible materials." } });
    fireEvent.change(screen.getByLabelText("Consent and attribution boundary"), { target: { value: "Ask before attributing or quoting input." } });
    fireEvent.change(screen.getByLabelText("Agenda"), { target: { value: "Test the question, scope, and authority." } });
    fireEvent.change(screen.getByLabelText("Timed run of show"), { target: { value: "15 | Frame the question | Round robin\n25 | Test the criteria | Small groups" } });
    fireEvent.change(screen.getByLabelText("Participation guidance"), { target: { value: "Prepare one concern and one condition for success." } });
    fireEvent.click(screen.getByRole("checkbox", { name: /observer@example.com/i }));
    fireEvent.change(screen.getByLabelText("Offline participants or groups"), { target: { value: "Telephone participant 1 | Local residents" } });
    fireEvent.click(screen.getByRole("button", { name: "Schedule session" }));

    await waitFor(() => expect(createFacilitationSession).toHaveBeenCalledWith(
      "decision-1",
      expect.objectContaining({
        title: "Decision framing workshop",
        facilitator_id: "facilitator-1",
        participation_guidance: "Prepare one concern and one condition for success.",
        influence_boundary: "The decision criteria and implementation conditions.",
        fixed_constraints: "The statutory deadline and approved budget.",
        accessibility_arrangements: "Offer telephone participation and accessible materials.",
        consent_boundary: "Ask before attributing or quoting input.",
        participation_channels: ["in_person"],
        participants: [{ user_id: "observer-1", role: "observer" }],
        external_participants: [{ external_label: "Telephone participant 1", stakeholder_group: "Local residents", role: "participant" }],
        agenda_items: [
          { title: "Frame the question", method: "Round robin", planned_minutes: 15 },
          { title: "Test the criteria", method: "Small groups", planned_minutes: 25 },
        ],
      }),
    ));
  });
});
