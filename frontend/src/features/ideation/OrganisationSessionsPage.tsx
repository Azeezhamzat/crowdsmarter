import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getOrganisation } from "../organisations/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import { createOrganisationSession, listOrganisationSessions } from "./api";

export function OrganisationSessionsPage() {
  const { organisationId: routeOrganisationId } = useParams<{ organisationId: string }>();
  const organisationId = routeOrganisationId ?? "";
  const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [description, setDescription] = useState("");
  const [decisionId, setDecisionId] = useState("");
  const [votingEnabled, setVotingEnabled] = useState(true);

  const organisation = useQuery({
    queryKey: ["organisations", organisationId],
    queryFn: () => getOrganisation(organisationId),
    enabled: Boolean(organisationId),
  });
  const sessions = useQuery({
    queryKey: ["organisations", organisationId, "sessions"],
    queryFn: () => listOrganisationSessions(organisationId),
    enabled: Boolean(organisationId),
  });
  const portfolio = useQuery({
    queryKey: ["organisations", organisationId, "portfolio-decisions"],
    queryFn: () => getOrganisationPortfolio(organisationId, {}),
    enabled: Boolean(organisationId),
  });

  const create = useMutation({
    mutationFn: () =>
      createOrganisationSession(organisationId, {
        title,
        prompt,
        description,
        decision_id: decisionId || null,
        voting_enabled: votingEnabled,
      }),
    onSuccess: async () => {
      setTitle("");
      setPrompt("");
      setDescription("");
      setDecisionId("");
      setVotingEnabled(true);
      setFormOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "sessions"] });
    },
  });

  return (
    <div>
      <Link className="back-link" to={`/organisations/${organisationId}`}>← Organisation</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Open sessions</p>
          <h1>{organisation.data?.name ?? "Organisation"} open sessions</h1>
          <p className="muted">
            Collect and vote on ideas from anyone with the link — no invitation or account required. Shortlisted
            ideas can be promoted into a real decision option.
          </p>
        </div>
        <button className="button button--primary" type="button" onClick={() => setFormOpen((open) => !open)}>
          {formOpen ? "Cancel" : "New session"}
        </button>
      </div>

      {formOpen ? (
        <section className="card-panel">
          <h2>Create an open session</h2>
          {create.isError ? (
            <StatusMessage kind="error">
              {create.error instanceof ApiError ? create.error.message : "The session could not be created."}
            </StatusMessage>
          ) : null}
          <div className="form-grid form-grid--two">
            <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Q3 process-improvement ideathon" /></label>
            <label>Link to an existing decision (optional)
              <select value={decisionId} onChange={(event) => setDecisionId(event.target.value)}>
                <option value="">No linked decision</option>
                {portfolio.data?.decisions.map((decision) => (
                  <option key={decision.id} value={decision.id}>{decision.title}</option>
                ))}
              </select>
            </label>
            <label className="record-grid__wide">Prompt<textarea rows={2} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="What question should submissions answer?" /></label>
            <label className="record-grid__wide">Description<textarea rows={2} value={description} onChange={(event) => setDescription(event.target.value)} /></label>
            <label className="checkbox-label"><input type="checkbox" checked={votingEnabled} onChange={(event) => setVotingEnabled(event.target.checked)} />Allow voting</label>
          </div>
          <button
            className="button button--primary"
            type="button"
            disabled={title.trim().length < 3 || prompt.trim().length < 3 || create.isPending}
            onClick={() => create.mutate()}
          >
            {create.isPending ? "Creating…" : "Create session"}
          </button>
        </section>
      ) : null}

      {sessions.isPending ? <p>Loading sessions…</p> : null}
      {sessions.isError ? <StatusMessage kind="error">Sessions could not be loaded.</StatusMessage> : null}
      {sessions.data?.length === 0 ? <p className="muted">No open sessions yet.</p> : null}

      <div className="portfolio-list">
        {sessions.data?.map((session) => (
          <article className="portfolio-card" key={session.id}>
            <div className="portfolio-card__main">
              <div className="inline-heading">
                <h2><Link to={`/organisations/${organisationId}/sessions/${session.id}`}>{session.title}</Link></h2>
                <span className={`status-badge status-badge--${session.status}`}>{session.status_label}</span>
              </div>
              <p className="portfolio-card__question">{session.prompt}</p>
              {session.decision_title ? <small className="muted">Linked to: {session.decision_title}</small> : null}
            </div>
            <div className="portfolio-card__meta">
              <div><span className="meta-label">Ideas</span><strong>{session.idea_count}</strong></div>
              <div><span className="meta-label">Created by</span><strong>{session.created_by.email}</strong></div>
              <Link className="portfolio-open-link" to={`/organisations/${organisationId}/sessions/${session.id}`}>
                Manage <Icon name="arrow-right" size={17} />
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
