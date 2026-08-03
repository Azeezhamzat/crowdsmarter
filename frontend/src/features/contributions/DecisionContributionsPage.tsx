import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { ContributionRequest } from "../../lib/types";
import { getDecision } from "../decisions/api";
import { listParticipants } from "../participants/api";
import {
  contributionAction,
  createContributionRequest,
  createFacilitationSession,
  getDecisionContributions,
  listFacilitationSessions,
  reviewContribution,
  saveContributionDraft,
  submitContribution,
  updateContributionRequest,
  updateFacilitationSessionStatus,
  updateSessionAttendance,
} from "./api";

function formatDateTime(value: string | null): string {
  if (!value) return "No due date";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function latestDraft(item: ContributionRequest) {
  return item.submissions.find((submission) => submission.status === "draft");
}

function latestSubmitted(item: ContributionRequest) {
  return [...item.submissions].filter((submission) => submission.status === "submitted").sort((a, b) => b.sequence - a.sequence)[0];
}

export function DecisionContributionsPage() {
  const { decisionId = "" } = useParams<{ decisionId: string }>();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"requests" | "sessions">("requests");
  const [responses, setResponses] = useState<Record<string, { body: string; references: string }>>({});
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({});
  const [assignmentEdits, setAssignmentEdits] = useState<Record<string, {
    assignee_id: string; reviewer_id: string; priority: string; due_at: string;
  }>>({});
  const [requestForm, setRequestForm] = useState({
    assignee_id: "", reviewer_id: "", session_id: "", kind: "evidence", title: "", instructions: "",
    priority: "normal", due_at: "", open_immediately: true,
  });
  const [sessionForm, setSessionForm] = useState({
    title: "", objective: "", agenda: "", starts_at: "", ends_at: "", participant_ids: [] as string[],
  });

  const decision = useQuery({ queryKey: ["decisions", decisionId], queryFn: () => getDecision(decisionId), enabled: Boolean(decisionId) });
  const workspace = useQuery({ queryKey: ["decisions", decisionId, "contributions"], queryFn: () => getDecisionContributions(decisionId), enabled: Boolean(decisionId) });
  const sessions = useQuery({ queryKey: ["decisions", decisionId, "facilitation-sessions"], queryFn: () => listFacilitationSessions(decisionId), enabled: Boolean(decisionId) });
  const participants = useQuery({
    queryKey: ["decisions", decisionId, "participants"],
    queryFn: () => listParticipants(decisionId),
    enabled: Boolean(decisionId),
  });

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "contributions"] }),
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "facilitation-sessions"] }),
      queryClient.invalidateQueries({ queryKey: ["personal-contributions"] }),
      queryClient.invalidateQueries({ queryKey: ["notifications"] }),
    ]);
  };

  const createRequestMutation = useMutation({
    mutationFn: () => createContributionRequest(decisionId, {
      ...requestForm,
      reviewer_id: requestForm.reviewer_id || null,
      session_id: requestForm.session_id || null,
      due_at: requestForm.due_at ? new Date(requestForm.due_at).toISOString() : null,
    }),
    onSuccess: async () => {
      setRequestForm({ assignee_id: "", reviewer_id: "", session_id: "", kind: "evidence", title: "", instructions: "", priority: "normal", due_at: "", open_immediately: true });
      await refresh();
    },
  });
  const updateRequestMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Record<string, unknown> }) => updateContributionRequest(id, input),
    onSuccess: async (_, variables) => {
      setAssignmentEdits((current) => { const next = { ...current }; delete next[variables.id]; return next; });
      await refresh();
    },
  });
  const actionMutation = useMutation({ mutationFn: ({ id, action, reason = "" }: { id: string; action: string; reason?: string }) => contributionAction(id, action, reason), onSuccess: refresh });
  const draftMutation = useMutation({ mutationFn: ({ id, body, references }: { id: string; body: string; references: string }) => saveContributionDraft(id, body, references), onSuccess: refresh });
  const submitMutation = useMutation({ mutationFn: ({ id, body, references }: { id: string; body: string; references: string }) => submitContribution(id, body, references), onSuccess: refresh });
  const reviewMutation = useMutation({ mutationFn: ({ id, outcome, note }: { id: string; outcome: string; note: string }) => reviewContribution(id, outcome, note), onSuccess: refresh });
  const createSessionMutation = useMutation({
    mutationFn: () => createFacilitationSession(decisionId, {
      ...sessionForm,
      starts_at: sessionForm.starts_at ? new Date(sessionForm.starts_at).toISOString() : null,
      ends_at: sessionForm.ends_at ? new Date(sessionForm.ends_at).toISOString() : null,
    }),
    onSuccess: async () => {
      setSessionForm({ title: "", objective: "", agenda: "", starts_at: "", ends_at: "", participant_ids: [] });
      await refresh();
    },
  });
  const sessionStatusMutation = useMutation({ mutationFn: ({ id, status }: { id: string; status: string }) => updateFacilitationSessionStatus(id, status), onSuccess: refresh });
  const attendanceMutation = useMutation({ mutationFn: ({ id, attendance }: { id: string; attendance: string }) => updateSessionAttendance(id, attendance), onSuccess: refresh });

  const activeMembers = useMemo(() => (participants.data ?? []).filter((item) => item.status === "active" && item.role !== "observer"), [participants.data]);
  const reviewerMembers = useMemo(() => activeMembers.filter((item) => ["decision_owner", "decision_maker", "reviewer"].includes(item.role)), [activeMembers]);
  const error = createRequestMutation.error || updateRequestMutation.error || actionMutation.error || draftMutation.error || submitMutation.error || reviewMutation.error || createSessionMutation.error || sessionStatusMutation.error || attendanceMutation.error;

  if (decision.isPending || workspace.isPending) return <p>Loading contribution orchestration…</p>;
  if (decision.isError || workspace.isError || !decision.data || !workspace.data) return <StatusMessage kind="error">The contribution workspace could not be loaded.</StatusMessage>;

  return (
    <div className="contribution-workspace">
      <Link className="back-link" to={`/decisions/${decisionId}`}>← Decision workspace</Link>
      <header className="page-heading contribution-heading">
        <div>
          <p className="eyebrow">Contribution orchestration</p>
          <h1>{decision.data.title}</h1>
          <p className="muted">Assign bounded work, preserve drafts and submitted revisions, review explicitly, and see who is represented.</p>
        </div>
        <span className="status-badge">{decision.data.status_label}</span>
      </header>

      {error ? <StatusMessage kind="error">{error instanceof ApiError ? error.message : "The contribution command failed."}</StatusMessage> : null}

      <section className="contribution-metrics" aria-label="Participation coverage">
        <article><span>Decision participants</span><strong>{workspace.data.participation.participant_count}</strong></article>
        <article><span>Assigned</span><strong>{workspace.data.participation.assigned_count}</strong></article>
        <article><span>Submitted</span><strong>{workspace.data.participation.submitted_count}</strong></article>
        <article><span>Coverage</span><strong>{workspace.data.participation.coverage_percent}%</strong></article>
      </section>

      {workspace.data.participation.unassigned_participants.length ? (
        <div className="representation-alert"><strong>Participation gap</strong><span>{workspace.data.participation.unassigned_participants.map((item) => item.email).join(", ")} have no current assignment.</span></div>
      ) : null}

      <div className="segmented-control contribution-tabs" role="tablist" aria-label="Contribution workspace sections">
        <button type="button" className={tab === "requests" ? "is-active" : ""} onClick={() => setTab("requests")}>Requests</button>
        <button type="button" className={tab === "sessions" ? "is-active" : ""} onClick={() => setTab("sessions")}>Facilitation sessions</button>
      </div>

      {tab === "requests" ? (
        <div className="contribution-layout">
          <section className="contribution-list" aria-label="Contribution requests">
            {workspace.data.requests.length === 0 ? <div className="empty-state"><h2>No contribution requests</h2><p>Create a named, due-dated request rather than relying on informal follow-up.</p></div> : null}
            {workspace.data.requests.map((item) => {
              const draft = latestDraft(item);
              const submitted = latestSubmitted(item);
              const response = responses[item.id] ?? { body: draft?.body ?? "", references: draft?.references ?? "" };
              const assignmentEdit = assignmentEdits[item.id] ?? {
                assignee_id: item.assignee.id,
                reviewer_id: item.reviewer?.id ?? "",
                priority: item.priority,
                due_at: item.due_at ? new Date(new Date(item.due_at).getTime() - new Date(item.due_at).getTimezoneOffset() * 60000).toISOString().slice(0, 16) : "",
              };
              return (
                <article className={`contribution-card${item.is_overdue ? " contribution-card--overdue" : ""}`} id={`request-${item.id}`} key={item.id}>
                  <header>
                    <div><span className={`urgency-badge urgency-badge--${item.priority}`}>{item.priority_label}</span><span className="status-badge">{item.status_label}</span></div>
                    <time dateTime={item.due_at ?? undefined}>{formatDateTime(item.due_at)}</time>
                  </header>
                  <p className="eyebrow">{item.kind_label}</p>
                  <h2>{item.title}</h2>
                  <p>{item.instructions}</p>
                  <dl className="contribution-people"><div><dt>Assignee</dt><dd>{item.assignee.email}</dd></div><div><dt>Reviewer</dt><dd>{item.reviewer?.email ?? item.requested_by.email}</dd></div></dl>

                  {submitted ? <div className="submitted-contribution"><strong>Submitted revision {submitted.sequence}</strong><p>{submitted.body}</p>{submitted.references ? <small>References: {submitted.references}</small> : null}</div> : null}
                  {item.reviews.map((review) => <div className="contribution-review-record" key={review.id}><strong>{review.outcome_label}</strong><span>{review.reviewer.email}</span><p>{review.note}</p></div>)}

                  {item.can_work ? (
                    <div className="contribution-response-editor">
                      <label htmlFor={`response-${item.id}`}>Your contribution</label>
                      <textarea id={`response-${item.id}`} rows={6} value={response.body} onChange={(event) => setResponses((current) => ({ ...current, [item.id]: { ...response, body: event.target.value } }))} />
                      <label htmlFor={`references-${item.id}`}>References or linked records</label>
                      <textarea id={`references-${item.id}`} rows={2} value={response.references} onChange={(event) => setResponses((current) => ({ ...current, [item.id]: { ...response, references: event.target.value } }))} />
                      <div className="inline-actions">
                        {item.status === "open" || item.status === "returned" ? <button className="button button--quiet" type="button" onClick={() => actionMutation.mutate({ id: item.id, action: "start" })}>Start</button> : null}
                        <button className="button button--secondary" type="button" disabled={!response.body.trim()} onClick={() => draftMutation.mutate({ id: item.id, ...response })}>Save draft</button>
                        <button className="button button--primary" type="button" disabled={!response.body.trim()} onClick={() => submitMutation.mutate({ id: item.id, ...response })}>Submit for review</button>
                      </div>
                    </div>
                  ) : null}

                  {item.can_review && ["submitted", "under_review"].includes(item.status) ? (
                    <div className="contribution-review-editor">
                      <label htmlFor={`review-${item.id}`}>Review note</label>
                      <textarea id={`review-${item.id}`} rows={3} value={reviewNotes[item.id] ?? ""} onChange={(event) => setReviewNotes((current) => ({ ...current, [item.id]: event.target.value }))} />
                      <div className="inline-actions">
                        {item.status === "submitted" ? <button className="button button--quiet" type="button" onClick={() => actionMutation.mutate({ id: item.id, action: "start_review" })}>Start review</button> : null}
                        <button className="button button--secondary" type="button" disabled={!reviewNotes[item.id]?.trim()} onClick={() => reviewMutation.mutate({ id: item.id, outcome: "returned", note: reviewNotes[item.id] ?? "" })}>Return with guidance</button>
                        <button className="button button--primary" type="button" disabled={!reviewNotes[item.id]?.trim()} onClick={() => reviewMutation.mutate({ id: item.id, outcome: "accepted", note: reviewNotes[item.id] ?? "" })}>Accept contribution</button>
                      </div>
                    </div>
                  ) : null}

                  {item.can_manage && ["draft", "open", "in_progress", "returned"].includes(item.status) ? (
                    <details className="assignment-edit-panel">
                      <summary>Revise assignment</summary>
                      <div className="form-row">
                        <div><label htmlFor={`edit-assignee-${item.id}`}>Assignee</label><select id={`edit-assignee-${item.id}`} value={assignmentEdit.assignee_id} onChange={(event) => setAssignmentEdits((current) => ({ ...current, [item.id]: { ...assignmentEdit, assignee_id: event.target.value } }))}>{activeMembers.map((participant) => <option value={participant.user.id} key={participant.id}>{participant.user.email}</option>)}</select></div>
                        <div><label htmlFor={`edit-reviewer-${item.id}`}>Reviewer</label><select id={`edit-reviewer-${item.id}`} value={assignmentEdit.reviewer_id} onChange={(event) => setAssignmentEdits((current) => ({ ...current, [item.id]: { ...assignmentEdit, reviewer_id: event.target.value } }))}><option value="">Decision authority</option>{reviewerMembers.filter((participant) => participant.user.id !== assignmentEdit.assignee_id).map((participant) => <option value={participant.user.id} key={participant.id}>{participant.user.email}</option>)}</select></div>
                      </div>
                      <div className="form-row">
                        <div><label htmlFor={`edit-priority-${item.id}`}>Priority</label><select id={`edit-priority-${item.id}`} value={assignmentEdit.priority} onChange={(event) => setAssignmentEdits((current) => ({ ...current, [item.id]: { ...assignmentEdit, priority: event.target.value } }))}><option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option><option value="critical">Critical</option></select></div>
                        <div><label htmlFor={`edit-due-${item.id}`}>Due date and time</label><input id={`edit-due-${item.id}`} type="datetime-local" value={assignmentEdit.due_at} onChange={(event) => setAssignmentEdits((current) => ({ ...current, [item.id]: { ...assignmentEdit, due_at: event.target.value } }))} /></div>
                      </div>
                      <button className="button button--secondary" type="button" disabled={updateRequestMutation.isPending} onClick={() => updateRequestMutation.mutate({ id: item.id, input: { assignee_id: assignmentEdit.assignee_id, reviewer_id: assignmentEdit.reviewer_id || null, priority: assignmentEdit.priority, due_at: assignmentEdit.due_at ? new Date(assignmentEdit.due_at).toISOString() : null } })}>{updateRequestMutation.isPending ? "Saving…" : "Save assignment"}</button>
                    </details>
                  ) : null}
                  {item.can_manage && !["accepted", "cancelled"].includes(item.status) ? <button className="button button--danger-quiet" type="button" onClick={() => { const reason = window.prompt("Why is this request being cancelled?"); if (reason?.trim()) actionMutation.mutate({ id: item.id, action: "cancel", reason }); }}>Cancel request</button> : null}
                </article>
              );
            })}
          </section>

          {workspace.data.can_manage ? (
            <aside className="side-panel contribution-create-panel">
              <p className="eyebrow">Accountable request</p><h2>Create contribution request</h2>
              <label htmlFor="contribution-assignee">Assignee</label>
              <select id="contribution-assignee" value={requestForm.assignee_id} onChange={(event) => setRequestForm({ ...requestForm, assignee_id: event.target.value })}><option value="">Select participant</option>{activeMembers.map((item) => <option value={item.user.id} key={item.id}>{item.user.email}</option>)}</select>
              <label htmlFor="contribution-reviewer">Reviewer</label>
              <select id="contribution-reviewer" value={requestForm.reviewer_id} onChange={(event) => setRequestForm({ ...requestForm, reviewer_id: event.target.value })}><option value="">Decision owner/requester</option>{reviewerMembers.filter((item) => item.user.id !== requestForm.assignee_id).map((item) => <option value={item.user.id} key={item.id}>{item.user.email}</option>)}</select><label htmlFor="contribution-session">Facilitation session</label><select id="contribution-session" value={requestForm.session_id} onChange={(event) => setRequestForm({ ...requestForm, session_id: event.target.value })}><option value="">No linked session</option>{sessions.data?.filter((item) => !["closed", "cancelled"].includes(item.status)).map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select>
              <div className="form-row"><div><label htmlFor="contribution-kind">Type</label><select id="contribution-kind" value={requestForm.kind} onChange={(event) => setRequestForm({ ...requestForm, kind: event.target.value })}><option value="evidence">Evidence</option><option value="assumption">Assumption</option><option value="risk">Risk</option><option value="stakeholder">Stakeholder perspective</option><option value="option">Option</option><option value="question">Question response</option><option value="review">Review</option><option value="scenario">Scenario contribution</option><option value="implementation">Implementation input</option><option value="other">Other</option></select></div><div><label htmlFor="contribution-priority">Priority</label><select id="contribution-priority" value={requestForm.priority} onChange={(event) => setRequestForm({ ...requestForm, priority: event.target.value })}><option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option><option value="critical">Critical</option></select></div></div>
              <label htmlFor="contribution-title">Title</label><input id="contribution-title" value={requestForm.title} onChange={(event) => setRequestForm({ ...requestForm, title: event.target.value })} />
              <label htmlFor="contribution-instructions">Instructions and acceptance boundary</label><textarea id="contribution-instructions" rows={5} value={requestForm.instructions} onChange={(event) => setRequestForm({ ...requestForm, instructions: event.target.value })} />
              <label htmlFor="contribution-due">Due date and time</label><input id="contribution-due" type="datetime-local" value={requestForm.due_at} onChange={(event) => setRequestForm({ ...requestForm, due_at: event.target.value })} />
              <button className="button button--primary button--full" type="button" disabled={!requestForm.assignee_id || !requestForm.title.trim() || !requestForm.instructions.trim() || createRequestMutation.isPending} onClick={() => createRequestMutation.mutate()}>{createRequestMutation.isPending ? "Assigning…" : "Assign contribution"}</button>
            </aside>
          ) : null}
        </div>
      ) : (
        <div className="contribution-layout">
          <section className="contribution-list" aria-label="Facilitation sessions">
            {sessions.data?.length === 0 ? <div className="empty-state"><h2>No facilitation sessions</h2><p>Schedule a bounded workshop and connect its outputs to named contribution requests.</p></div> : null}
            {sessions.data?.map((session) => <article className="facilitation-card" id={`session-${session.id}`} key={session.id}><header><div><span className="status-badge">{session.status_label}</span></div><time>{formatDateTime(session.starts_at)}</time></header><p className="eyebrow">Facilitated workshop</p><h2>{session.title}</h2><p>{session.objective}</p>{session.agenda ? <div><strong>Agenda</strong><p>{session.agenda}</p></div> : null}<p className="muted">Facilitator: {session.facilitator.email} · {session.participants.length} invited</p>{session.participants.length ? <div className="session-attendance-list">{session.participants.map((participant) => <div key={participant.id}><span>{participant.user.email}</span><select aria-label={`Attendance for ${participant.user.email}`} value={participant.attendance} disabled={!session.can_manage || attendanceMutation.isPending} onChange={(event) => attendanceMutation.mutate({ id: participant.id, attendance: event.target.value })}><option value="invited">Invited</option><option value="attended">Attended</option><option value="absent">Absent</option></select></div>)}</div> : null}{session.can_manage && session.status === "planned" ? <button className="button button--secondary" type="button" onClick={() => sessionStatusMutation.mutate({ id: session.id, status: "open" })}>Open session</button> : null}{session.can_manage && session.status === "open" ? <button className="button button--primary" type="button" onClick={() => sessionStatusMutation.mutate({ id: session.id, status: "closed" })}>Close session</button> : null}</article>)}
          </section>
          {workspace.data.can_manage ? <aside className="side-panel contribution-create-panel"><p className="eyebrow">Structured workshop</p><h2>Schedule facilitation</h2><label htmlFor="session-title">Title</label><input id="session-title" value={sessionForm.title} onChange={(event) => setSessionForm({ ...sessionForm, title: event.target.value })} /><label htmlFor="session-objective">Objective</label><textarea id="session-objective" rows={4} value={sessionForm.objective} onChange={(event) => setSessionForm({ ...sessionForm, objective: event.target.value })} /><label htmlFor="session-agenda">Agenda</label><textarea id="session-agenda" rows={4} value={sessionForm.agenda} onChange={(event) => setSessionForm({ ...sessionForm, agenda: event.target.value })} /><div className="form-row"><div><label htmlFor="session-start">Starts</label><input id="session-start" type="datetime-local" value={sessionForm.starts_at} onChange={(event) => setSessionForm({ ...sessionForm, starts_at: event.target.value })} /></div><div><label htmlFor="session-end">Ends</label><input id="session-end" type="datetime-local" value={sessionForm.ends_at} onChange={(event) => setSessionForm({ ...sessionForm, ends_at: event.target.value })} /></div></div><label>Invite participants</label><div className="participant-checklist">{activeMembers.map((item) => <label key={item.id}><input type="checkbox" checked={sessionForm.participant_ids.includes(item.user.id)} onChange={(event) => setSessionForm({ ...sessionForm, participant_ids: event.target.checked ? [...sessionForm.participant_ids, item.user.id] : sessionForm.participant_ids.filter((id) => id !== item.user.id) })} />{item.user.email}</label>)}</div><button className="button button--primary button--full" type="button" disabled={!sessionForm.title.trim() || !sessionForm.objective.trim() || createSessionMutation.isPending} onClick={() => createSessionMutation.mutate()}>{createSessionMutation.isPending ? "Scheduling…" : "Schedule session"}</button></aside> : null}
        </div>
      )}
    </div>
  );
}
