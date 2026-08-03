import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { ContributionPreference } from "../../lib/types";
import {
  getContributionPreference,
  getPersonalContributions,
  updateContributionPreference,
} from "./api";

function formatDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "No due date";
}

function PreferenceCard({ organisationId, organisationName }: { organisationId: string; organisationName: string }) {
  const queryClient = useQueryClient();
  const preference = useQuery({
    queryKey: ["contribution-preference", organisationId],
    queryFn: () => getContributionPreference(organisationId),
  });
  const [draft, setDraft] = useState<Pick<ContributionPreference, "digest_cadence" | "email_enabled" | "due_reminders_enabled" | "reminder_days_before"> | null>(null);
  const current = draft ?? (preference.data ? {
    digest_cadence: preference.data.digest_cadence,
    email_enabled: preference.data.email_enabled,
    due_reminders_enabled: preference.data.due_reminders_enabled,
    reminder_days_before: preference.data.reminder_days_before,
  } : null);
  const save = useMutation({
    mutationFn: () => updateContributionPreference(organisationId, current!),
    onSuccess: async () => {
      setDraft(null);
      await queryClient.invalidateQueries({ queryKey: ["contribution-preference", organisationId] });
    },
  });
  if (!current) return <article className="preference-card"><p>Loading preferences for {organisationName}…</p></article>;
  return (
    <article className="preference-card">
      <div><p className="eyebrow">{organisationName}</p><h2>Reminder and digest preferences</h2></div>
      {save.error ? <StatusMessage kind="error">{save.error instanceof ApiError ? save.error.message : "Preferences could not be saved."}</StatusMessage> : null}
      <label htmlFor={`cadence-${organisationId}`}>Email cadence</label>
      <select id={`cadence-${organisationId}`} value={current.digest_cadence} onChange={(event) => setDraft({ ...current, digest_cadence: event.target.value as ContributionPreference["digest_cadence"] })}>
        <option value="immediate">Immediate assignment emails</option>
        <option value="daily">Daily digest</option>
        <option value="weekly">Weekly digest</option>
        <option value="none">No email digest</option>
      </select>
      <label className="checkbox-row"><input type="checkbox" checked={current.email_enabled} onChange={(event) => setDraft({ ...current, email_enabled: event.target.checked })} />Enable contribution emails</label>
      <label className="checkbox-row"><input type="checkbox" checked={current.due_reminders_enabled} onChange={(event) => setDraft({ ...current, due_reminders_enabled: event.target.checked })} />Create due-soon and overdue reminders</label>
      <label htmlFor={`reminder-days-${organisationId}`}>Reminder lead time</label>
      <select id={`reminder-days-${organisationId}`} value={current.reminder_days_before} onChange={(event) => setDraft({ ...current, reminder_days_before: Number(event.target.value) })}>
        {[0, 1, 2, 3, 5, 7, 14].map((days) => <option value={days} key={days}>{days === 0 ? "On the due date" : `${days} day${days === 1 ? "" : "s"} before`}</option>)}
      </select>
      <button className="button button--secondary" type="button" disabled={!draft || save.isPending} onClick={() => save.mutate()}>{save.isPending ? "Saving…" : "Save preferences"}</button>
    </article>
  );
}

export function MyContributionsPage() {
  const work = useQuery({ queryKey: ["personal-contributions"], queryFn: getPersonalContributions });
  const organisations = Array.from(new Map((work.data?.requests ?? []).map((item) => [item.organisation_id, item.organisation_name])).entries());
  return (
    <div className="personal-contributions-page">
      <div className="page-heading"><div><p className="eyebrow">Contribution inbox</p><h1>Your contribution work</h1><p className="muted">Assigned contributions, saved drafts, returned revisions, and work awaiting your review across organisations.</p></div></div>
      {work.isError ? <StatusMessage kind="error">Your contribution work could not be loaded.</StatusMessage> : null}
      <section className="contribution-metrics" aria-label="Contribution summary"><article><span>Active</span><strong>{work.data?.summary.total ?? 0}</strong></article><article><span>Overdue</span><strong>{work.data?.summary.overdue ?? 0}</strong></article><article><span>Returned</span><strong>{work.data?.summary.returned ?? 0}</strong></article><article><span>Under review</span><strong>{work.data?.summary.submitted ?? 0}</strong></article><article><span>Awaiting your review</span><strong>{work.data?.summary.awaiting_review ?? 0}</strong></article></section>
      {work.isPending ? <p>Loading assigned contributions…</p> : null}
      {work.data?.requests.length === 0 ? <div className="empty-state"><h2>No active contribution work</h2><p>Assignments and explicit review requests will appear here when a decision team needs your input.</p></div> : null}
      <div className="personal-contribution-list">{work.data?.requests.map((item) => <Link className={`personal-contribution-card${item.is_overdue ? " is-overdue" : ""}`} to={`/decisions/${item.decision_id}/contributions#request-${item.id}`} key={item.id}><div><p className="eyebrow">{item.organisation_name} · {item.kind_label}</p><h2>{item.title}</h2><p>{item.instructions}</p><span>{item.decision_title} · {item.status_label} · {item.priority_label} priority</span></div><div><strong>{formatDate(item.due_at)}</strong><span>{item.reviewer ? `Reviewer: ${item.reviewer.email}` : "Decision authority review"}</span></div></Link>)}</div>
      {organisations.length ? <section className="contribution-preferences-section"><div className="section-heading"><div><p className="eyebrow">Delivery controls</p><h2>Contribution notifications</h2><p className="muted">In-app workflow notifications remain available; email delivery is optional and organisation specific.</p></div></div><div className="preference-grid">{organisations.map(([id, name]) => <PreferenceCard organisationId={id} organisationName={name} key={id} />)}</div></section> : null}
    </div>
  );
}
