import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getTerminology, type Terminology } from "../../lib/terminology";
import type { Idea } from "../../lib/types";
import { lookupOrganisation } from "../org-enrichment/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import { archiveIdea, getOrganiserSession, promoteIdea, setSessionState, shortlistIdea } from "./api";

const CREATE_NEW_DECISION_VALUE = "__new__";

function submitterLabel(idea: Idea): string {
  if (idea.submitted_by_participant) return idea.submitted_by_participant.name;
  if (idea.submitted_by_user) {
    const name = `${idea.submitted_by_user.first_name} ${idea.submitted_by_user.last_name}`.trim();
    return name || idea.submitted_by_user.email;
  }
  return "Someone";
}

function IdeaRow({
  organisationId,
  sessionId,
  idea,
  decisions,
  terms,
}: {
  organisationId: string;
  sessionId: string;
  idea: Idea;
  decisions: Array<{ id: string; title: string }>;
  terms: Terminology;
}) {
  const queryClient = useQueryClient();
  const [decisionId, setDecisionId] = useState("");
  const queryKey = ["sessions", sessionId, "organiser"];

  const shortlist = useMutation({
    mutationFn: (shortlisted: boolean) => shortlistIdea(sessionId, idea.id, shortlisted),
    onSuccess: (data) => queryClient.setQueryData(queryKey, data),
  });
  const archive = useMutation({
    mutationFn: (archived: boolean) => archiveIdea(sessionId, idea.id, archived),
    onSuccess: (data) => queryClient.setQueryData(queryKey, data),
  });
  const promote = useMutation({
    mutationFn: () =>
      promoteIdea(sessionId, idea.id, decisionId === CREATE_NEW_DECISION_VALUE ? null : decisionId),
    onSuccess: (data) => queryClient.setQueryData(queryKey, data),
  });
  const [verifyQuery, setVerifyQuery] = useState(submitterLabel(idea));
  const verifyOrganisation = useMutation({
    mutationFn: () => lookupOrganisation(organisationId, verifyQuery),
  });

  return (
    <article className="idea-card">
      <div className="idea-card__body">
        <h3>{idea.title}</h3>
        {idea.description ? <p>{idea.description}</p> : null}
        {idea.requested_amount ? (
          <p className="muted">
            <strong>{terms.amountFieldLabel}:</strong> {idea.requested_amount}
          </p>
        ) : null}
        {idea.team_name ? (
          <p className="muted">
            <strong>Team:</strong> {idea.team_name}
            {idea.team_members.length > 0
              ? ` - ${idea.team_members.map((member) => (member.role ? `${member.name} (${member.role})` : member.name)).join(", ")}`
              : ""}
          </p>
        ) : null}
        {idea.submitter_school || idea.submitter_age_bracket_label ? (
          <p className="muted">
            {idea.submitter_school ? <>{idea.submitter_school}</> : null}
            {idea.submitter_school && idea.submitter_age_bracket_label ? " · " : ""}
            {idea.submitter_age_bracket_label ?? ""}
            {idea.submitter_guardian_consent_given !== null && idea.submitter_guardian_consent_given !== undefined ? (
              <span className={`status-badge status-badge--${idea.submitter_guardian_consent_given ? "open" : "blocked"}`}>
                {idea.submitter_guardian_consent_given ? "Guardian consent recorded" : "Guardian consent missing"}
              </span>
            ) : null}
          </p>
        ) : null}
        <small className="muted">
          {submitterLabel(idea)} · {idea.status_label} · {idea.vote_count} vote{idea.vote_count === 1 ? "" : "s"}
          {idea.comments.length > 0 ? ` · ${idea.comments.length} comment${idea.comments.length === 1 ? "" : "s"}` : ""}
        </small>
        {promote.isError ? (
          <StatusMessage kind="error">
            {promote.error instanceof ApiError
              ? promote.error.message
              : `Could not promote this ${terms.ideaNoun.toLowerCase()}.`}
          </StatusMessage>
        ) : null}
        <div className="verify-organisation">
          <input
            aria-label="Organisation name or registration number to verify"
            value={verifyQuery}
            onChange={(event) => setVerifyQuery(event.target.value)}
          />
          <button
            className="button button--quiet button--compact"
            type="button"
            disabled={verifyOrganisation.isPending || !verifyQuery.trim()}
            onClick={() => verifyOrganisation.mutate()}
          >
            {verifyOrganisation.isPending ? "Verifying…" : "Verify organisation"}
          </button>
          {verifyOrganisation.data ? (
            verifyOrganisation.data.found ? (
              <p className="muted">
                {verifyOrganisation.data.legal_name} · {verifyOrganisation.data.ein_or_charity_number} · {verifyOrganisation.data.standing}
              </p>
            ) : (
              <p className="muted">{verifyOrganisation.data.detail}</p>
            )
          ) : null}
        </div>
        {idea.status === "promoted" ? null : (
          <div className="button-row">
            <button
              className="button button--secondary button--compact"
              type="button"
              disabled={shortlist.isPending}
              onClick={() => shortlist.mutate(idea.status !== "shortlisted")}
            >
              {idea.status === "shortlisted" ? "Remove from shortlist" : "Shortlist"}
            </button>
            <button
              className="button button--secondary button--compact"
              type="button"
              disabled={archive.isPending}
              onClick={() => archive.mutate(idea.status !== "archived")}
            >
              {idea.status === "archived" ? "Unarchive" : "Archive"}
            </button>
            <select value={decisionId} onChange={(event) => setDecisionId(event.target.value)}>
              <option value="">Promote into…</option>
              <option value={CREATE_NEW_DECISION_VALUE}>+ Create a new grant round from this {terms.ideaNoun.toLowerCase()}</option>
              {decisions.map((decision) => <option key={decision.id} value={decision.id}>{decision.title}</option>)}
            </select>
            <button
              className="button button--primary button--compact"
              type="button"
              disabled={!decisionId || promote.isPending}
              onClick={() => promote.mutate()}
            >
              {promote.isPending ? "Promoting…" : `Promote to ${terms.optionNoun.toLowerCase()}`}
            </button>
          </div>
        )}
      </div>
    </article>
  );
}

export function OpenSessionOrganiserPage() {
  const { organisationId: routeOrganisationId, sessionId: routeSessionId } = useParams<{ organisationId: string; sessionId: string }>();
  const organisationId = routeOrganisationId ?? "";
  const sessionId = routeSessionId ?? "";
  const queryClient = useQueryClient();
  const queryKey = ["sessions", sessionId, "organiser"];

  const session = useQuery({ queryKey, queryFn: () => getOrganiserSession(sessionId), enabled: Boolean(sessionId) });
  const terms = getTerminology(session.data?.decision_template_key);
  const portfolio = useQuery({
    queryKey: ["organisations", organisationId, "portfolio-decisions"],
    queryFn: () => getOrganisationPortfolio(organisationId, {}),
    enabled: Boolean(organisationId),
  });

  const state = useMutation({
    mutationFn: (action: "open" | "close") => setSessionState(sessionId, action),
    onSuccess: (data) => queryClient.setQueryData(queryKey, data),
  });

  const publicUrl = session.data ? `${window.location.origin}/s/${session.data.public_slug}` : "";
  const [copied, setCopied] = useState(false);

  return (
    <div>
      <Link className="back-link" to={`/organisations/${organisationId}/sessions`}>← Open sessions</Link>
      {session.isPending ? <p>Loading session…</p> : null}
      {session.isError ? <StatusMessage kind="error">This session could not be loaded.</StatusMessage> : null}
      {session.data ? (
        <>
          <div className="page-heading">
            <div>
              <p className="eyebrow">Open session</p>
              <h1>{session.data.title}</h1>
              <p className="muted">{session.data.prompt}</p>
              <span className={`status-badge status-badge--${session.data.status}`}>{session.data.status_label}</span>
            </div>
            <div className="button-row">
              {session.data.status === "open" ? (
                <button className="button button--secondary" type="button" disabled={state.isPending} onClick={() => state.mutate("close")}>Close session</button>
              ) : (
                <button className="button button--primary" type="button" disabled={state.isPending} onClick={() => state.mutate("open")}>
                  {session.data.status === "draft" ? "Open session" : "Reopen session"}
                </button>
              )}
            </div>
          </div>

          <section className="card-panel">
            <p className="eyebrow">Shareable link</p>
            <div className="button-row">
              <code>{publicUrl}</code>
              <button
                className="button button--secondary button--compact"
                type="button"
                onClick={async () => {
                  await navigator.clipboard.writeText(publicUrl);
                  setCopied(true);
                  window.setTimeout(() => setCopied(false), 2000);
                }}
              >
                {copied ? "Copied" : "Copy link"}
              </button>
            </div>
            <p className="muted">Anyone with this link can join and submit ideas once the session is open.</p>
          </section>

          <section aria-label={terms.ideaNounPlural}>
            <h2>{terms.ideaNounPlural} ({session.data.ideas.length})</h2>
            {session.data.ideas.length === 0 ? (
              <p className="muted">No {terms.ideaNounPlural.toLowerCase()} submitted yet.</p>
            ) : (
              <div className="idea-list">
                {session.data.ideas.map((idea) => (
                  <IdeaRow
                    key={idea.id}
                    organisationId={organisationId}
                    sessionId={sessionId}
                    idea={idea}
                    decisions={portfolio.data?.decisions ?? []}
                    terms={terms}
                  />
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
