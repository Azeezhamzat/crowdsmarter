import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router";
import type { CSSProperties } from "react";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { downloadDecisionExport } from "../exports/api";
import { listMemberships } from "../organisations/api";
import { ParticipantsPanel } from "../participants/ParticipantsPanel";
import {
  getDecision,
  getDecisionOverview,
  listDecisionTransitions,
  transitionDecision,
  updateDecision,
} from "./api";
import { DecisionFramingForm } from "./DecisionFramingForm";
import { DecisionLifecycle } from "./DecisionLifecycle";
import { statusLabel } from "./lifecycle";

const transitionSchema = z.object({ rationale: z.string().trim().max(8000) });
type TransitionInput = z.infer<typeof transitionSchema>;

function personName(firstName: string, lastName: string, email: string) {
  return `${firstName} ${lastName}`.trim() || email;
}

function formatDate(value: string | null) {
  if (!value) return "Not set";
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

export function DecisionWorkspacePage() {
  const { decisionId: routeDecisionId } = useParams<{ decisionId: string }>();
  const decisionId = routeDecisionId ?? "";
  const queryClient = useQueryClient();
  const decision = useQuery({
    queryKey: ["decisions", decisionId],
    queryFn: () => getDecision(decisionId),
    enabled: Boolean(decisionId),
  });
  const overview = useQuery({
    queryKey: ["decisions", decisionId, "overview"],
    queryFn: () => getDecisionOverview(decisionId),
    enabled: Boolean(decisionId),
  });
  const transitions = useQuery({
    queryKey: ["decisions", decisionId, "transitions"],
    queryFn: () => listDecisionTransitions(decisionId),
    enabled: Boolean(decisionId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", decision.data?.organisation_id, "memberships"],
    queryFn: () => listMemberships(decision.data?.organisation_id ?? ""),
    enabled: Boolean(decision.data?.organisation_id),
  });
  const transitionForm = useForm<TransitionInput>({
    resolver: zodResolver(transitionSchema),
    defaultValues: { rationale: "" },
  });

  const refreshDecision = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] }),
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "overview"] }),
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "transitions"] }),
      queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
    ]);
  };

  const save = useMutation({
    mutationFn: (input: Parameters<typeof updateDecision>[1]) => updateDecision(decisionId, input),
    onSuccess: refreshDecision,
  });
  const dossier = useMutation({ mutationFn: () => downloadDecisionExport(decisionId) });
  const transition = useMutation({
    mutationFn: (input: TransitionInput) => {
      if (!decision.data) throw new Error("Decision is unavailable.");
      return transitionDecision(decisionId, {
        expected_status: decision.data.status,
        rationale: input.rationale,
      });
    },
    onSuccess: async () => {
      transitionForm.reset();
      await refreshDecision();
    },
  });

  if (decision.isPending || overview.isPending) return <p>Loading decision workspace…</p>;
  if (decision.isError || overview.isError || !decision.data || !overview.data) {
    return <StatusMessage kind="error">The decision workspace could not be loaded.</StatusMessage>;
  }

  const current = decision.data;
  const summary = overview.data;
  const next = current.next_transition;
  const hasOutcomeWorkflow = [
    "decision_finalised", "commitment", "implementation", "outcome_review", "lessons_learned", "archived",
  ].includes(current.status);

  return (
    <div className="decision-hub">
      <Link className="back-link" to={`/workspaces/${current.workspace_id}`}>← Workspace decisions</Link>

      <header className="decision-hero">
        <div>
          <div className="heading-badges">
            <span className="status-badge">{current.status_label}</span>
            <span className={`urgency-badge urgency-badge--${current.urgency}`}>{current.urgency} urgency</span>
            {current.source_template_key && current.source_template_key !== "blank" ? (
              <span className="role-badge">Template: {current.source_template_key.replaceAll("_", " ")}</span>
            ) : null}
          </div>
          <p className="eyebrow">Decision workspace</p>
          <h1>{current.title}</h1>
          <p className="decision-question">{current.decision_question || "The decision question has not been framed yet."}</p>
        </div>
        <div className="decision-owner-card">
          <span>Accountable owner</span>
          <strong>{personName(current.owner.first_name, current.owner.last_name, current.owner.email)}</strong>
          <small>Target: {formatDate(current.target_decision_date)}</small>
          <button className="button button--secondary button--small" type="button" onClick={() => dossier.mutate()} disabled={dossier.isPending}>{dossier.isPending ? "Preparing…" : "Download dossier"}</button>
        </div>
      </header>

      {save.error || transition.error ? (
        <StatusMessage kind="error">
          {(save.error instanceof ApiError && save.error.message) ||
            (transition.error instanceof ApiError && transition.error.message) ||
            "The decision change failed."}
        </StatusMessage>
      ) : null}
      {save.isSuccess ? <StatusMessage kind="success">Decision framing saved.</StatusMessage> : null}
      {dossier.error ? <StatusMessage kind="error">{dossier.error instanceof ApiError ? dossier.error.message : "The dossier could not be exported."}</StatusMessage> : null}
      {dossier.data ? <StatusMessage kind="success">Downloaded {dossier.data}</StatusMessage> : null}

      <section className="next-action-panel" aria-labelledby="next-action-title">
        <div className="progress-ring" style={{ "--progress": `${summary.progress.percent}%` } as CSSProperties}>
          <strong>{summary.progress.percent}%</strong><span>lifecycle</span>
        </div>
        <div>
          <p className="eyebrow">Next required action</p>
          <h2 id="next-action-title">{summary.next_action.label}</h2>
          <p>{summary.next_action.description}</p>
        </div>
        <Link className="button button--primary button-link" to={summary.next_action.route}>Continue this decision</Link>
      </section>

      <section className="decision-scorecards" aria-label="Decision health summary">
        <article>
          <span>Framing</span>
          <strong>{summary.framing.completed}/{summary.framing.total}</strong>
          <small>{summary.framing.missing.length ? `${summary.framing.missing.length} field(s) missing` : "Core frame complete"}</small>
        </article>
        <article>
          <span>Participants</span>
          <strong>{summary.participants.total}</strong>
          <small>{summary.participants.role_counts.reviewer ? "Reviewer included" : "No reviewer assigned"}</small>
        </article>
        <article>
          <span>Open questions</span>
          <strong>{summary.discussion.unresolved}</strong>
          <small>{summary.discussion.unresolved ? "Require explicit resolution" : "No unresolved concerns"}</small>
        </article>
        <article className={summary.target.is_overdue ? "scorecard--warning" : ""}>
          <span>Target date</span>
          <strong>{formatDate(summary.target.date)}</strong>
          <small>{summary.target.is_overdue ? "Overdue" : "Current planning target"}</small>
        </article>
      </section>

      <nav className="decision-section-nav" aria-label="Decision sections">
        <Link to={`/decisions/${current.id}/reasoning/options`}>Reasoning</Link>
        <Link to={`/decisions/${current.id}/collaboration`}>Discussion</Link>
        <Link to={`/decisions/${current.id}/contributions`}>Contributions</Link>
        <Link to={`/decisions/${current.id}/governance`}>Positions</Link>
        <Link to={`/decisions/${current.id}/evaluations`}>Collective evaluation</Link>
        <Link to={`/decisions/${current.id}/analysis`}>Integrated analysis</Link>
        <Link to={`/decisions/${current.id}/ai-review`}>Advisory review</Link>
        {hasOutcomeWorkflow ? <Link to={`/decisions/${current.id}/outcomes`}>Outcomes</Link> : null}
      </nav>

      <div className="decision-overview-grid">
        <section className="overview-card overview-card--wide" aria-labelledby="at-a-glance-title">
          <div className="section-heading">
            <div><p className="eyebrow">Decision at a glance</p><h2 id="at-a-glance-title">Why this choice exists</h2></div>
            <a className="text-link" href="#framing">Edit framing</a>
          </div>
          <div className="record-grid">
            <div><span>Purpose</span><p>{current.purpose || "Purpose has not been recorded."}</p></div>
            <div><span>Scope</span><p>{current.scope || "Scope has not been recorded."}</p></div>
            <div><span>Context</span><p>{current.context || "Context has not been recorded."}</p></div>
            <div><span>Contribution boundaries</span><p>{current.contribution_guidance || "Contribution boundaries have not been recorded."}</p></div>
          </div>
        </section>

        <section className="overview-card" aria-labelledby="reasoning-title">
          <div className="section-heading"><div><p className="eyebrow">Reasoning health</p><h2 id="reasoning-title">Structured record</h2></div></div>
          <div className="reasoning-count-grid">
            <div><strong>{summary.reasoning.active_options}</strong><span>Options</span></div>
            <div><strong>{summary.reasoning.active_criteria}</strong><span>Criteria</span></div>
            <div><strong>{summary.reasoning.active_evidence}</strong><span>Evidence</span></div>
            <div><strong>{summary.reasoning.active_assumptions}</strong><span>Assumptions</span></div>
            <div><strong>{summary.reasoning.current_risks}</strong><span>Risks</span></div>
          </div>
          {summary.reasoning.blockers.length ? (
            <ul className="blocker-list">{summary.reasoning.blockers.map((item) => <li key={item}>{item}</li>)}</ul>
          ) : <StatusMessage kind="success">The minimum structured reasoning gate is satisfied.</StatusMessage>}
          <div className="stacked-actions"><Link className="button button--secondary button-link button--full" to={`/decisions/${current.id}/reasoning/options`}>Review structured records</Link><Link className="button button--primary button-link button--full" to={`/decisions/${current.id}/analysis`}>Open integrated analysis</Link></div>
        </section>

        <section className="overview-card" aria-labelledby="options-title">
          <div className="section-heading"><div><p className="eyebrow">Alternatives</p><h2 id="options-title">Active options</h2></div></div>
          {summary.options.length ? (
            <ol className="overview-option-list">
              {summary.options.map((option) => (
                <li key={option.id}>
                  <div><strong>{option.title}</strong>{option.is_status_quo ? <small>Status quo</small> : null}</div>
                  <span>{option.evidence_count} evidence · {option.risk_count} risks</span>
                </li>
              ))}
            </ol>
          ) : <p className="muted">No active options yet.</p>}
        </section>

        <section className="overview-card" aria-labelledby="signals-title">
          <div className="section-heading"><div><p className="eyebrow">Foresight</p><h2 id="signals-title">Signals informing this decision</h2></div><Link className="text-link" to={`/organisations/${current.organisation_id}/foresight`}>Open radar</Link></div>
          {summary.linked_signals.length ? (
            <ul className="decision-signal-list">
              {summary.linked_signals.map((signal) => (
                <li key={signal.id}>
                  <span className={`signal-dot signal-dot--${signal.maturity}`} />
                  <div><strong>{signal.title}</strong><small>{signal.steep_category} · {signal.time_horizon} · attention {signal.priority_score}</small><p>{signal.relevance}</p></div>
                </li>
              ))}
            </ul>
          ) : <p className="muted">No foresight signals have been linked to this decision.</p>}
          {summary.foresight_implications.length ? (
            <div className="decision-implications">
              <h3>Strategic implications</h3>
              <ul>
                {summary.foresight_implications.map((item) => (
                  <li key={item.id}>
                    <div>
                      <strong>{item.title}</strong>
                      <small>{item.implication_type.replaceAll("_", " ")} · priority {item.priority} · {item.owner}</small>
                      <p>{item.description}</p>
                    </div>
                    <Link className="text-link" to={`/organisations/${current.organisation_id}/foresight/canvases/${item.canvas_id}`}>Open canvas</Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>

        <section className="overview-card" aria-labelledby="risks-title">
          <div className="section-heading"><div><p className="eyebrow">Exposure</p><h2 id="risks-title">Material risks</h2></div></div>
          {summary.material_risks.length ? (
            <ul className="material-risk-list">
              {summary.material_risks.map((risk) => (
                <li key={risk.id}><span className={`risk-score risk-score--${risk.score >= 15 ? "high" : risk.score >= 8 ? "medium" : "low"}`}>{risk.score}</span><div><strong>{risk.title}</strong><small>{risk.owner} · {risk.status}</small></div></li>
              ))}
            </ul>
          ) : <p className="muted">No current risks have been recorded.</p>}
        </section>

        <section className="overview-card" aria-labelledby="people-title">
          <div className="section-heading"><div><p className="eyebrow">Human authority</p><h2 id="people-title">People in this decision</h2></div><a className="text-link" href="#participants">Manage</a></div>
          <ul className="people-list">
            {summary.participants.people.map((person) => <li key={person.id}><div><strong>{person.name}</strong><small>{person.email}</small></div><span>{person.role_label}</span></li>)}
          </ul>
        </section>
      </div>

      <section id="lifecycle" className="workspace-detail-section">
        <p className="eyebrow">Lifecycle</p>
        <h2>Where the decision is now</h2>
        <DecisionLifecycle currentStatus={current.status} nextTransition={next} />
      </section>

      <details id="framing" className="workspace-disclosure" open={summary.framing.missing.length > 0}>
        <summary><div><strong>Decision framing</strong><span>{summary.framing.completed}/{summary.framing.total} core areas complete</span></div></summary>
        <div className="disclosure-body">
          {memberships.isError ? <StatusMessage kind="error">Organisation members could not be loaded. Ownership cannot be reassigned until the list is available.</StatusMessage> : null}
          <DecisionFramingForm decision={current} isSaving={save.isPending} onSave={(input) => save.mutate(input)} memberships={memberships.data ?? []} />
        </div>
      </details>

      <details id="participants" className="workspace-disclosure" open={summary.participants.total < 2}>
        <summary><div><strong>Participants and roles</strong><span>{summary.participants.total} active participant(s)</span></div></summary>
        <div className="disclosure-body"><ParticipantsPanel decisionId={current.id} canManage={current.can_manage_participants} templateKey={current.source_template_key} /></div>
      </details>

      <details className="workspace-disclosure">
        <summary><div><strong>Advance the lifecycle</strong><span>{next ? `${statusLabel(next.from_status)} → ${statusLabel(next.to_status)}` : "No further transition"}</span></div></summary>
        <div className="disclosure-body">
          {next ? (
            next.enabled ? (
              next.action === "finalise" ? (
                <><p>Finalisation requires explicit option selection and reviewed stakeholder positions.</p><Link className="button button--primary button-link" to={`/decisions/${current.id}/governance`}>Open final decision governance</Link></>
              ) : next.action === "outcome_workflow" ? (
                <><p>Continue through commitment, implementation, outcome review, and lessons learned.</p><Link className="button button--primary button-link" to={`/decisions/${current.id}/outcomes`}>Open outcomes and learning</Link></>
              ) : current.can_transition ? (
                <form onSubmit={transitionForm.handleSubmit((values) => transition.mutate(values))} noValidate>
                  <label htmlFor="transition-rationale">Transition rationale</label>
                  <textarea id="transition-rationale" rows={4} {...transitionForm.register("rationale")} />
                  <FieldError message={transitionForm.formState.errors.rationale?.message} />
                  <p className="muted compact-note">The server validates required framing, deadlines, participants, and reasoning before changing state.</p>
                  <button className="button button--primary" type="submit" disabled={transition.isPending}>{transition.isPending ? "Advancing…" : `Advance to ${statusLabel(next.to_status)}`}</button>
                </form>
              ) : <p className="muted">Only the decision owner or an organisation manager may advance it.</p>
            ) : <StatusMessage kind="error">{next.blocked_reason}</StatusMessage>
          ) : <p className="muted">This decision is archived and has no further transition.</p>}
        </div>
      </details>

      <details className="workspace-disclosure">
        <summary><div><strong>Lifecycle history</strong><span>{transitions.data?.length ?? 0} recorded transition(s)</span></div></summary>
        <div className="disclosure-body">
          {transitions.isPending ? <p>Loading history…</p> : null}
          {transitions.isError ? <StatusMessage kind="error">Lifecycle history could not be loaded.</StatusMessage> : null}
          {transitions.data?.length === 0 ? <p className="muted">No lifecycle transitions have occurred.</p> : null}
          <ol className="history-list">{transitions.data?.map((item) => <li key={item.id}><strong>{item.from_status_label} → {item.to_status_label}</strong><span className="table-secondary">{new Date(item.created_at).toLocaleString()} · {item.actor.email}</span>{item.rationale ? <p>{item.rationale}</p> : null}</li>)}</ol>
        </div>
      </details>
    </div>
  );
}
