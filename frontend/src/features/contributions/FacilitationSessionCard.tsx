import { useEffect, useMemo, useState } from "react";

import type { ContributionRequest, FacilitationSession } from "../../lib/types";

type RecordDraft = {
  kind: string;
  body: string;
  channel: string;
  origin: string;
  attribution: string;
  source_participant_id: string;
  speaker_label: string;
  permission_to_quote: boolean;
  follow_up_owner: string;
  agenda_item_id: string;
};

type AgendaDraft = {
  title: string;
  purpose: string;
  method: string;
  facilitator_prompt: string;
  output_prompt: string;
  planned_minutes: number;
};

type QualityDraft = {
  inclusion_score: number;
  clarity_score: number;
  neutrality_score: number;
  participation_score: number;
  follow_through_score: number;
  what_worked: string;
  improve_next_time: string;
  unresolved_risks: string;
};

type ResponseDraft = {
  what_we_heard: string;
  what_changed: string;
  what_did_not_change: string;
  rationale: string;
  next_steps: string;
};

type Props = {
  session: FacilitationSession;
  linkedOutputs: ContributionRequest[];
  busy: boolean;
  onAttendance: (participantId: string, attendance: string) => void;
  onStatus: (status: string) => void;
  onAgendaCreate: (input: Record<string, unknown>) => void;
  onAgendaAction: (itemId: string, action: "start" | "complete" | "skip" | "reset") => void;
  onRecord: (input: Record<string, unknown>) => void;
  onResponse: (input: Record<string, unknown>) => void;
  onQualityReview: (input: Record<string, unknown>) => void;
  onCreateFollowUp: () => void;
  onDownloadReport: () => void;
};

function formatDateTime(value: string | null): string {
  if (!value) return "Not scheduled";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function participantLabel(participant: FacilitationSession["participants"][number]): string {
  return participant.display_label || participant.user?.email || "Offline participant";
}

function emptyResponse(session: FacilitationSession): ResponseDraft {
  return {
    what_we_heard: session.authority_response?.what_we_heard ?? "",
    what_changed: session.authority_response?.what_changed ?? "",
    what_did_not_change: session.authority_response?.what_did_not_change ?? "",
    rationale: session.authority_response?.rationale ?? "",
    next_steps: session.authority_response?.next_steps ?? "",
  };
}

function emptyQualityReview(session: FacilitationSession): QualityDraft {
  return {
    inclusion_score: session.quality_review?.inclusion_score ?? 3,
    clarity_score: session.quality_review?.clarity_score ?? 3,
    neutrality_score: session.quality_review?.neutrality_score ?? 3,
    participation_score: session.quality_review?.participation_score ?? 3,
    follow_through_score: session.quality_review?.follow_through_score ?? 3,
    what_worked: session.quality_review?.what_worked ?? "",
    improve_next_time: session.quality_review?.improve_next_time ?? "",
    unresolved_risks: session.quality_review?.unresolved_risks ?? "",
  };
}

export function FacilitationSessionCard({
  session,
  linkedOutputs,
  busy,
  onAttendance,
  onStatus,
  onAgendaCreate,
  onAgendaAction,
  onRecord,
  onResponse,
  onQualityReview,
  onCreateFollowUp,
  onDownloadReport,
}: Props) {
  const initialChannel = session.participation_channels[0] ?? "in_person";
  const [record, setRecord] = useState<RecordDraft>({
    kind: "agreement",
    body: "",
    channel: initialChannel,
    origin: "participant_input",
    attribution: "anonymous",
    source_participant_id: "",
    speaker_label: "",
    permission_to_quote: false,
    follow_up_owner: "",
    agenda_item_id: "",
  });
  const [agendaDraft, setAgendaDraft] = useState<AgendaDraft>({
    title: "",
    purpose: "",
    method: "",
    facilitator_prompt: "",
    output_prompt: "",
    planned_minutes: 10,
  });
  const [response, setResponse] = useState<ResponseDraft>(() => emptyResponse(session));
  const [qualityReview, setQualityReview] = useState<QualityDraft>(() => emptyQualityReview(session));
  const activeAgendaItem = session.agenda_items.find((item) => item.status === "active");
  const resolvedAgendaItems = session.agenda_items.filter((item) => ["completed", "skipped"].includes(item.status)).length;
  const [clock, setClock] = useState(() => Date.now());

  useEffect(() => {
    if (!activeAgendaItem) return undefined;
    setClock(Date.now());
    const timer = window.setInterval(() => setClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [activeAgendaItem]);

  const elapsedMinutes = activeAgendaItem?.started_at
    ? Math.max(0, (clock - new Date(activeAgendaItem.started_at).getTime()) / 60000)
    : 0;

  const canSubmitRecord = useMemo(() => {
    if (!record.body.trim()) return false;
    if (record.origin === "participant_input" && record.attribution === "attributed") {
      return Boolean(record.source_participant_id || record.speaker_label.trim());
    }
    return true;
  }, [record]);
  const canPublishResponse = Boolean(
    response.what_we_heard.trim()
      && (response.what_changed.trim() || response.what_did_not_change.trim())
      && (!response.what_did_not_change.trim() || response.rationale.trim())
      && response.next_steps.trim(),
  );
  const responsePublished = session.authority_response?.status === "published";

  const submitRecord = () => {
    onRecord({
      ...record,
      agenda_item_id: record.agenda_item_id || activeAgendaItem?.id || null,
      source_participant_id: record.attribution === "anonymous" ? null : record.source_participant_id || null,
      speaker_label: record.attribution === "anonymous" ? "" : record.speaker_label,
    });
    setRecord((current) => ({ ...current, body: "", speaker_label: "", source_participant_id: "", permission_to_quote: false, follow_up_owner: "" }));
  };

  const addAgendaItem = () => {
    onAgendaCreate(agendaDraft);
    setAgendaDraft({ title: "", purpose: "", method: "", facilitator_prompt: "", output_prompt: "", planned_minutes: 10 });
  };

  return (
    <article className="facilitation-card" id={`session-${session.id}`}>
      <header>
        <div><span className="status-badge">{session.status_label}</span></div>
        <time dateTime={session.starts_at ?? undefined}>{formatDateTime(session.starts_at)}</time>
      </header>
      <p className="eyebrow">Facilitated session</p>
      <h2>{session.title}</h2>
      <p>{session.objective}</p>

      <div className="session-boundaries">
        <div><strong>Participants can influence</strong><p>{session.influence_boundary || "Not yet recorded."}</p></div>
        <div><strong>Fixed constraints</strong><p>{session.fixed_constraints || "Not yet recorded."}</p></div>
      </div>
      {(session.accessibility_arrangements || session.consent_boundary) ? <div className="session-boundaries"><div><strong>Accessibility arrangements</strong><p>{session.accessibility_arrangements || "Not yet recorded."}</p></div><div><strong>Consent and attribution boundary</strong><p>{session.consent_boundary || "Not yet recorded."}</p></div></div> : null}
      {session.participation_channels.length ? <p className="session-channel-list"><strong>Channels:</strong> {session.participation_channels.map((channel) => channel.replaceAll("_", " ")).join(", ")}</p> : null}
      {session.agenda ? <div className="session-brief-section"><strong>Agenda</strong><p>{session.agenda}</p></div> : null}
      {session.participation_guidance ? <div className="session-brief-section"><strong>Participation guidance</strong><p>{session.participation_guidance}</p></div> : null}
      {session.missing_perspectives ? <div className="representation-alert"><strong>Missing perspectives</strong><span>{session.missing_perspectives}</span></div> : null}
      <p className="muted">Facilitator: {session.facilitator.email} · {session.participants.length} invited</p>

      <section className="facilitation-cockpit" aria-label={`Run of show for ${session.title}`}>
        <div className="session-section-heading">
          <div><p className="eyebrow">Facilitator cockpit</p><h3>Run of show</h3></div>
          <strong>{resolvedAgendaItems}/{session.agenda_items.length}</strong>
        </div>
        {session.agenda_items.length ? (
          <>
            <progress value={resolvedAgendaItems} max={session.agenda_items.length} aria-label={`${resolvedAgendaItems} of ${session.agenda_items.length} agenda items resolved`} />
            {activeAgendaItem ? (
              <div className={`live-agenda-item${elapsedMinutes > activeAgendaItem.planned_minutes ? " live-agenda-item--over" : ""}`} aria-live="polite">
                <div><span className="live-indicator">Live</span><strong>{activeAgendaItem.title}</strong></div>
                <b>{Math.floor(elapsedMinutes)}:{String(Math.floor((elapsedMinutes % 1) * 60)).padStart(2, "0")} / {activeAgendaItem.planned_minutes}:00</b>
                {activeAgendaItem.facilitator_prompt ? <p><strong>Ask:</strong> {activeAgendaItem.facilitator_prompt}</p> : null}
                {activeAgendaItem.output_prompt ? <p><strong>Capture:</strong> {activeAgendaItem.output_prompt}</p> : null}
              </div>
            ) : null}
            <ol className="agenda-run-list">
              {session.agenda_items.map((item) => (
                <li className={`agenda-run-item agenda-run-item--${item.status}`} key={item.id}>
                  <div className="agenda-run-item__main">
                    <span>{item.order}</span>
                    <div><strong>{item.title}</strong><small>{item.method || "Method not recorded"} · {item.planned_minutes} min{item.actual_minutes !== null ? ` · ${item.actual_minutes} actual` : ""}</small>{item.purpose ? <p>{item.purpose}</p> : null}</div>
                  </div>
                  <div className="agenda-run-item__actions">
                    <span className="status-badge">{item.status_label}</span>
                    {session.can_manage && session.status === "open" && item.status === "queued" ? <><button className="button button--secondary button--small" type="button" disabled={busy || Boolean(activeAgendaItem)} onClick={() => onAgendaAction(item.id, "start")}>Start</button><button className="button button--quiet button--small" type="button" disabled={busy} onClick={() => onAgendaAction(item.id, "skip")}>Skip</button></> : null}
                    {session.can_manage && item.status === "active" ? <><button className="button button--primary button--small" type="button" disabled={busy} onClick={() => onAgendaAction(item.id, "complete")}>Complete</button><button className="button button--quiet button--small" type="button" disabled={busy} onClick={() => onAgendaAction(item.id, "skip")}>Skip</button></> : null}
                    {session.can_manage && ["planned", "open"].includes(session.status) && item.status === "skipped" ? <button className="button button--quiet button--small" type="button" disabled={busy} onClick={() => onAgendaAction(item.id, "reset")}>Return to queue</button> : null}
                  </div>
                </li>
              ))}
            </ol>
          </>
        ) : <p className="muted">No timed agenda items yet. Add a concrete activity, facilitator prompt, and expected output.</p>}
        {session.can_manage && ["planned", "open"].includes(session.status) ? (
          <details className="session-editor agenda-editor">
            <summary>Add an agenda item</summary>
            <div className="form-row"><div><label htmlFor={`agenda-title-${session.id}`}>Activity</label><input id={`agenda-title-${session.id}`} value={agendaDraft.title} onChange={(event) => setAgendaDraft({ ...agendaDraft, title: event.target.value })} /></div><div><label htmlFor={`agenda-minutes-${session.id}`}>Minutes</label><input id={`agenda-minutes-${session.id}`} type="number" min={1} max={480} value={agendaDraft.planned_minutes} onChange={(event) => setAgendaDraft({ ...agendaDraft, planned_minutes: Number(event.target.value) })} /></div></div>
            <label htmlFor={`agenda-purpose-${session.id}`}>Purpose</label><textarea id={`agenda-purpose-${session.id}`} rows={2} value={agendaDraft.purpose} onChange={(event) => setAgendaDraft({ ...agendaDraft, purpose: event.target.value })} />
            <label htmlFor={`agenda-method-${session.id}`}>Method</label><input id={`agenda-method-${session.id}`} value={agendaDraft.method} onChange={(event) => setAgendaDraft({ ...agendaDraft, method: event.target.value })} placeholder="For example: silent reflection, then round robin" />
            <label htmlFor={`agenda-prompt-${session.id}`}>Facilitator prompt</label><textarea id={`agenda-prompt-${session.id}`} rows={2} value={agendaDraft.facilitator_prompt} onChange={(event) => setAgendaDraft({ ...agendaDraft, facilitator_prompt: event.target.value })} />
            <label htmlFor={`agenda-output-${session.id}`}>Expected captured output</label><textarea id={`agenda-output-${session.id}`} rows={2} value={agendaDraft.output_prompt} onChange={(event) => setAgendaDraft({ ...agendaDraft, output_prompt: event.target.value })} />
            <button className="button button--secondary" type="button" disabled={busy || !agendaDraft.title.trim() || agendaDraft.planned_minutes < 1 || agendaDraft.planned_minutes > 480} onClick={addAgendaItem}>Add to run of show</button>
          </details>
        ) : null}
      </section>

      {session.participants.length ? (
        <div className="session-attendance-list">
          {session.participants.map((participant) => (
            <div key={participant.id}>
              <span><strong>{participantLabel(participant)}</strong><small>{participant.stakeholder_group || participant.role_label}</small></span>
              <select
                aria-label={`Attendance for ${participantLabel(participant)}`}
                value={participant.attendance}
                disabled={!session.can_manage || busy}
                onChange={(event) => onAttendance(participant.id, event.target.value)}
              >
                <option value="invited">Invited</option><option value="attended">Attended</option><option value="absent">Absent</option>
              </select>
            </div>
          ))}
        </div>
      ) : null}

      <section className="session-records" aria-label={`Structured records for ${session.title}`}>
        <div className="session-section-heading"><div><p className="eyebrow">Traceable capture</p><h3>Session record</h3></div><strong>{session.records.length}</strong></div>
        {session.records.length ? (
          <ol className="session-record-list">
            {session.records.map((item) => {
              const source = item.attribution === "anonymous"
                ? "Anonymous participant input"
                : item.speaker_label || item.source_participant?.display_label || item.source_participant?.user?.email || item.origin_label;
              const agendaItem = session.agenda_items.find((candidate) => candidate.id === item.agenda_item_id);
              return <li key={item.id}><div><span className="status-badge">{item.kind_label}</span><small>{item.channel_label} · {source}</small></div><p>{item.body}</p>{agendaItem ? <small>Run of show: {agendaItem.title}</small> : null}{item.follow_up_owner ? <small>Follow-up: {item.follow_up_owner}</small> : null}</li>;
            })}
          </ol>
        ) : <p className="muted">No agreements, disagreements, actions, evidence gaps, or next questions have been captured.</p>}

        {session.can_manage && ["open", "closed"].includes(session.status) ? (
          <details className="session-editor">
            <summary>Capture a session record</summary>
            <div className="form-row">
              <div><label htmlFor={`record-kind-${session.id}`}>Record type</label><select id={`record-kind-${session.id}`} value={record.kind} onChange={(event) => setRecord({ ...record, kind: event.target.value })}><option value="agreement">Agreement</option><option value="disagreement">Unresolved disagreement</option><option value="action">Action</option><option value="evidence_gap">Evidence gap</option><option value="next_question">Next question</option><option value="participant_statement">Participant statement</option></select></div>
              <div><label htmlFor={`record-channel-${session.id}`}>Capture channel</label><select id={`record-channel-${session.id}`} value={record.channel} onChange={(event) => setRecord({ ...record, channel: event.target.value })}><option value="in_person">In person</option><option value="phone">Telephone</option><option value="paper">Paper</option><option value="partner_assisted">Partner assisted</option><option value="digital">Digital</option><option value="other">Other</option></select></div>
            </div>
            {session.agenda_items.length ? <><label htmlFor={`record-agenda-${session.id}`}>Run-of-show step</label><select id={`record-agenda-${session.id}`} value={record.agenda_item_id} onChange={(event) => setRecord({ ...record, agenda_item_id: event.target.value })}><option value="">{activeAgendaItem ? `Current live item — ${activeAgendaItem.title}` : "Not linked to an agenda item"}</option>{session.agenda_items.map((item) => <option value={item.id} key={item.id}>{item.order}. {item.title}</option>)}</select></> : null}
            <label htmlFor={`record-body-${session.id}`}>What was recorded</label><textarea id={`record-body-${session.id}`} rows={4} value={record.body} onChange={(event) => setRecord({ ...record, body: event.target.value })} />
            <div className="form-row">
              <div><label htmlFor={`record-origin-${session.id}`}>Origin</label><select id={`record-origin-${session.id}`} value={record.origin} onChange={(event) => setRecord({ ...record, origin: event.target.value })}><option value="participant_input">Participant input</option><option value="facilitator_synthesis">Facilitator synthesis</option></select></div>
              <div><label htmlFor={`record-attribution-${session.id}`}>Attribution</label><select id={`record-attribution-${session.id}`} value={record.attribution} onChange={(event) => setRecord({ ...record, attribution: event.target.value, source_participant_id: "", speaker_label: "" })}><option value="anonymous">Anonymous</option><option value="attributed">Attributed</option><option value="confidential">Confidential</option></select></div>
            </div>
            {record.attribution !== "anonymous" ? <div className="form-row"><div><label htmlFor={`record-participant-${session.id}`}>Named session participant</label><select id={`record-participant-${session.id}`} value={record.source_participant_id} onChange={(event) => setRecord({ ...record, source_participant_id: event.target.value })}><option value="">Unlisted participant or group</option>{session.participants.map((item) => <option value={item.id} key={item.id}>{participantLabel(item)}</option>)}</select></div><div><label htmlFor={`record-speaker-${session.id}`}>Unlisted participant or group label</label><input id={`record-speaker-${session.id}`} value={record.speaker_label} onChange={(event) => setRecord({ ...record, speaker_label: event.target.value })} /></div></div> : null}
            <label htmlFor={`record-owner-${session.id}`}>Follow-up owner or route</label><input id={`record-owner-${session.id}`} value={record.follow_up_owner} onChange={(event) => setRecord({ ...record, follow_up_owner: event.target.value })} placeholder="Person, team, or accountable contribution request" />
            <label className="checkbox-row"><input type="checkbox" checked={record.permission_to_quote} onChange={(event) => setRecord({ ...record, permission_to_quote: event.target.checked })} />Permission was given to quote this input</label>
            <button className="button button--secondary" type="button" disabled={!canSubmitRecord || busy} onClick={submitRecord}>Add to session record</button>
          </details>
        ) : session.status === "planned" && session.can_manage ? <p className="field-guidance">Open the session before capturing participant input.</p> : null}
      </section>

      <section className="session-output-summary" aria-label={`Accountable follow-ups for ${session.title}`}>
        <div><strong>Accountable follow-ups</strong><span>{linkedOutputs.length}</span></div>
        {linkedOutputs.length ? <ul>{linkedOutputs.map((item) => <li key={item.id}><span>{item.title}</span><small>{item.status_label} · {item.assignee.email}</small></li>)}</ul> : <p>No contribution request has been connected to this session.</p>}
      </section>

      <section className="facilitation-quality-panel" aria-label={`Quality review for ${session.title}`}>
        <div className="session-section-heading"><div><p className="eyebrow">Facilitator learning</p><h3>Session quality review</h3></div>{session.quality_review ? <strong>{session.quality_review.overall_score}/5</strong> : null}</div>
        {session.quality_review ? <div className="quality-review-summary"><p><strong>What worked</strong>{session.quality_review.what_worked}</p><p><strong>Improve next time</strong>{session.quality_review.improve_next_time}</p>{session.quality_review.unresolved_risks ? <p><strong>Unresolved risks</strong>{session.quality_review.unresolved_risks}</p> : null}</div> : null}
        {session.can_manage && session.status === "closed" ? (
          <details className="session-editor quality-review-editor">
            <summary>{session.quality_review ? "Update quality review" : "Review session quality"}</summary>
            <p className="field-guidance">Use the five-point scale as a facilitator reflection, not as an automated judgement of participants.</p>
            <div className="quality-score-grid">
              <div><label htmlFor={`quality-inclusion-${session.id}`}>Inclusion</label><select id={`quality-inclusion-${session.id}`} value={qualityReview.inclusion_score} onChange={(event) => setQualityReview({ ...qualityReview, inclusion_score: Number(event.target.value) })}>{[1, 2, 3, 4, 5].map((score) => <option value={score} key={score}>{score}/5</option>)}</select></div>
              <div><label htmlFor={`quality-clarity-${session.id}`}>Boundary clarity</label><select id={`quality-clarity-${session.id}`} value={qualityReview.clarity_score} onChange={(event) => setQualityReview({ ...qualityReview, clarity_score: Number(event.target.value) })}>{[1, 2, 3, 4, 5].map((score) => <option value={score} key={score}>{score}/5</option>)}</select></div>
              <div><label htmlFor={`quality-neutrality-${session.id}`}>Facilitator neutrality</label><select id={`quality-neutrality-${session.id}`} value={qualityReview.neutrality_score} onChange={(event) => setQualityReview({ ...qualityReview, neutrality_score: Number(event.target.value) })}>{[1, 2, 3, 4, 5].map((score) => <option value={score} key={score}>{score}/5</option>)}</select></div>
              <div><label htmlFor={`quality-participation-${session.id}`}>Meaningful participation</label><select id={`quality-participation-${session.id}`} value={qualityReview.participation_score} onChange={(event) => setQualityReview({ ...qualityReview, participation_score: Number(event.target.value) })}>{[1, 2, 3, 4, 5].map((score) => <option value={score} key={score}>{score}/5</option>)}</select></div>
              <div><label htmlFor={`quality-follow-${session.id}`}>Follow-through</label><select id={`quality-follow-${session.id}`} value={qualityReview.follow_through_score} onChange={(event) => setQualityReview({ ...qualityReview, follow_through_score: Number(event.target.value) })}>{[1, 2, 3, 4, 5].map((score) => <option value={score} key={score}>{score}/5</option>)}</select></div>
            </div>
            <label htmlFor={`quality-worked-${session.id}`}>What worked and why</label><textarea id={`quality-worked-${session.id}`} rows={3} value={qualityReview.what_worked} onChange={(event) => setQualityReview({ ...qualityReview, what_worked: event.target.value })} />
            <label htmlFor={`quality-improve-${session.id}`}>What to improve next time</label><textarea id={`quality-improve-${session.id}`} rows={3} value={qualityReview.improve_next_time} onChange={(event) => setQualityReview({ ...qualityReview, improve_next_time: event.target.value })} />
            <label htmlFor={`quality-risks-${session.id}`}>Unresolved inclusion or process risks</label><textarea id={`quality-risks-${session.id}`} rows={3} value={qualityReview.unresolved_risks} onChange={(event) => setQualityReview({ ...qualityReview, unresolved_risks: event.target.value })} />
            <button className="button button--secondary" type="button" disabled={busy || !qualityReview.what_worked.trim() || !qualityReview.improve_next_time.trim()} onClick={() => onQualityReview(qualityReview)}>Save quality review</button>
          </details>
        ) : !session.quality_review ? <p className="muted">Close the session before recording the facilitator's quality reflection.</p> : null}
      </section>

      <section className="authority-response-panel">
        <div className="session-section-heading"><div><p className="eyebrow">Close the loop</p><h3>Authority response</h3></div>{session.authority_response ? <span className="status-badge">{session.authority_response.status_label}</span> : null}</div>
        {responsePublished ? (
          <div className="published-response"><strong>What we heard</strong><p>{response.what_we_heard}</p><strong>What changed</strong><p>{response.what_changed || "No change recorded."}</p><strong>What did not change and why</strong><p>{response.what_did_not_change || "Nothing recorded."}</p>{response.rationale ? <p>{response.rationale}</p> : null}<strong>What happens next</strong><p>{response.next_steps}</p></div>
        ) : session.can_respond ? (
          <div className="authority-response-editor">
            <label htmlFor={`heard-${session.id}`}>What we heard</label><textarea id={`heard-${session.id}`} rows={3} value={response.what_we_heard} onChange={(event) => setResponse({ ...response, what_we_heard: event.target.value })} />
            <label htmlFor={`changed-${session.id}`}>What changed because of the input</label><textarea id={`changed-${session.id}`} rows={3} value={response.what_changed} onChange={(event) => setResponse({ ...response, what_changed: event.target.value })} />
            <label htmlFor={`not-changed-${session.id}`}>What did not change</label><textarea id={`not-changed-${session.id}`} rows={3} value={response.what_did_not_change} onChange={(event) => setResponse({ ...response, what_did_not_change: event.target.value })} />
            <label htmlFor={`rationale-${session.id}`}>Why it did not change</label><textarea id={`rationale-${session.id}`} rows={3} value={response.rationale} onChange={(event) => setResponse({ ...response, rationale: event.target.value })} />
            <label htmlFor={`next-${session.id}`}>What happens next</label><textarea id={`next-${session.id}`} rows={3} value={response.next_steps} onChange={(event) => setResponse({ ...response, next_steps: event.target.value })} />
            <div className="inline-actions"><button className="button button--quiet" type="button" disabled={busy} onClick={() => onResponse({ ...response, publish: false })}>Save draft</button><button className="button button--primary" type="button" disabled={busy || session.status !== "closed" || !canPublishResponse} onClick={() => onResponse({ ...response, publish: true })}>Publish response</button></div>
            {session.status !== "closed" ? <small className="field-guidance">Close the session before publishing. A draft can be prepared now.</small> : null}
          </div>
        ) : <p className="muted">The accountable authority has not published a response yet.</p>}
      </section>

      <div className="inline-actions session-actions">
        {session.can_manage ? <button className="button button--quiet" type="button" onClick={onDownloadReport}>Download printable report</button> : null}
        {session.can_manage && session.status !== "cancelled" ? <button className="button button--quiet" type="button" onClick={onCreateFollowUp}>Create accountable follow-up</button> : null}
        {session.can_manage && session.status === "planned" ? <button className="button button--secondary" type="button" onClick={() => onStatus("open")}>Open session</button> : null}
        {session.can_manage && session.status === "open" ? <button className="button button--primary" type="button" onClick={() => onStatus("closed")}>Close session</button> : null}
      </div>
    </article>
  );
}
