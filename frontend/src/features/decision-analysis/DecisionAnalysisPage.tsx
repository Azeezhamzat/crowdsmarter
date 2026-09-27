import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent} from "react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { PageHelp } from "../../components/PageHelp";
import { StatusMessage } from "../../components/StatusMessage";
import type { DecisionAnalysisIssue, DecisionQualityReview, ExecutiveDecisionSummary } from "../../lib/types";
import { getDecision } from "../decisions/api";
import { listMemberships } from "../organisations/api";
import {
  createDecisionIssue,
  createExecutiveSummary,
  createQualityReview,
  getDecisionAnalysis,
  listDecisionIssues,
  listExecutiveSummaries,
  listQualityReviews,
  updateDecisionIssue,
  updateExecutiveSummary,
  updateQualityReview,
} from "./api";

const QUALITY_QUESTIONS: Array<[string, string]> = [
  ["clear_question", "The decision question is clear and bounded"],
  ["distinct_options", "Genuinely distinct options are present"],
  ["status_quo_considered", "The status quo has been considered"],
  ["balanced_evidence", "Evidence is sufficiently balanced"],
  ["explicit_assumptions", "Important assumptions are explicit"],
  ["stakeholders_represented", "Material stakeholders are represented"],
  ["uncertainty_examined", "Uncertainty has been examined"],
  ["scenarios_considered", "Relevant scenarios have been considered"],
  ["risks_addressed", "Risks and mitigations are adequate"],
  ["dissent_visible", "Dissent and minority reasoning are visible"],
  ["implementation_plausible", "Implementation ownership is plausible"],
  ["review_timing_defined", "Review timing and conditions are defined"],
];

const SUMMARY_FIELDS = [
  ["context_summary", "Context"],
  ["options_summary", "Options considered"],
  ["evidence_summary", "Principal evidence"],
  ["uncertainty_summary", "Material uncertainty"],
  ["stakeholder_summary", "Stakeholder positions"],
  ["scenario_summary", "Scenario findings"],
  ["evaluation_summary", "Collective evaluation"],
  ["risk_summary", "Risks"],
  ["unresolved_issues", "Unresolved issues"],
  ["proposed_judgement", "Proposed judgement"],
  ["conditions", "Conditions and reservations"],
  ["implementation_implications", "Implementation implications"],
] as const satisfies ReadonlyArray<readonly [keyof ExecutiveDecisionSummary, string]>;

type View = "comparison" | "issues" | "quality" | "summary";

function userName(user: { first_name: string; last_name: string; email: string }): string {
  return `${user.first_name} ${user.last_name}`.trim() || user.email;
}

export function DecisionAnalysisPage() {
  const { decisionId = "" } = useParams();
  const queryClient = useQueryClient();
  const [view, setView] = useState<View>("comparison");
  const [issueForm, setIssueForm] = useState({
    issue_type: "missing_evidence",
    title: "",
    description: "",
    severity: "moderate",
    owner_id: "",
    option_id: "",
    due_date: "",
  });
  const [qualityForm, setQualityForm] = useState<Record<string, string>>({
    judgement: "not_ready", strengths: "", blockers: "", conditions: "",
  });
  const [summaryForm, setSummaryForm] = useState<Record<string, string>>({});

  const decision = useQuery({
    queryKey: ["decisions", decisionId],
    queryFn: () => getDecision(decisionId),
    enabled: Boolean(decisionId),
  });
  const analysis = useQuery({
    queryKey: ["decision-analysis", decisionId],
    queryFn: () => getDecisionAnalysis(decisionId),
    enabled: Boolean(decisionId),
  });
  const issues = useQuery({
    queryKey: ["decision-analysis", decisionId, "issues"],
    queryFn: () => listDecisionIssues(decisionId),
    enabled: Boolean(decisionId),
  });
  const qualityReviews = useQuery({
    queryKey: ["decision-analysis", decisionId, "quality-reviews"],
    queryFn: () => listQualityReviews(decisionId),
    enabled: Boolean(decisionId),
  });
  const summaries = useQuery({
    queryKey: ["decision-analysis", decisionId, "executive-summaries"],
    queryFn: () => listExecutiveSummaries(decisionId),
    enabled: Boolean(decisionId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", decision.data?.organisation_id, "memberships"],
    queryFn: () => listMemberships(decision.data?.organisation_id ?? ""),
    enabled: Boolean(decision.data?.organisation_id),
  });

  const draftQuality = qualityReviews.data?.find((item) => item.status === "draft");
  const draftSummary = summaries.data?.find((item) => item.status === "draft");

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["decision-analysis", decisionId] }),
      queryClient.invalidateQueries({ queryKey: ["decision-analysis", decisionId, "issues"] }),
      queryClient.invalidateQueries({ queryKey: ["decision-analysis", decisionId, "quality-reviews"] }),
      queryClient.invalidateQueries({ queryKey: ["decision-analysis", decisionId, "executive-summaries"] }),
    ]);
  };

  const issueMutation = useMutation({
    mutationFn: () => createDecisionIssue(decisionId, {
      ...issueForm,
      option_id: issueForm.option_id || null,
      due_date: issueForm.due_date || null,
    }),
    onSuccess: async () => {
      setIssueForm((value) => ({ ...value, title: "", description: "", option_id: "", due_date: "" }));
      await refresh();
    },
  });
  const issueUpdate = useMutation({
    mutationFn: ({ issue, input }: { issue: DecisionAnalysisIssue; input: Record<string, unknown> }) => updateDecisionIssue(issue.id, input),
    onSuccess: refresh,
  });
  const qualityMutation = useMutation({
    mutationFn: async ({ publish }: { publish: boolean }) => {
      const answers = Object.fromEntries(QUALITY_QUESTIONS.map(([key]) => [key, qualityForm[key] ?? "not_applicable"]));
      const input = {
        judgement: qualityForm.judgement ?? "not_ready",
        answers,
        strengths: qualityForm.strengths ?? "",
        blockers: qualityForm.blockers ?? "",
        conditions: qualityForm.conditions ?? "",
      };
      if (draftQuality) return updateQualityReview(draftQuality.id, { ...input, ...(publish ? { status: "published" } : {}) });
      const created = await createQualityReview(decisionId, input);
      return publish ? updateQualityReview(created.id, { ...input, status: "published" }) : created;
    },
    onSuccess: refresh,
  });
  const summaryMutation = useMutation({
    mutationFn: async ({ approve }: { approve: boolean }) => {
      const input = Object.fromEntries(SUMMARY_FIELDS.map(([key]) => [key, summaryForm[key] ?? ""]));
      if (draftSummary) return updateExecutiveSummary(draftSummary.id, { ...input, ...(approve ? { status: "approved" } : {}) });
      const created = await createExecutiveSummary(decisionId, input);
      return approve ? updateExecutiveSummary(created.id, { ...input, status: "approved" }) : created;
    },
    onSuccess: refresh,
  });

  useEffect(() => {
    if (!issueForm.owner_id && memberships.data?.length) {
      const preferred = memberships.data.find((item) => item.user.id === decision.data?.owner.id) ?? memberships.data.at(0);
      if (preferred) setIssueForm((value) => ({ ...value, owner_id: preferred.user.id }));
    }
  }, [memberships.data, decision.data?.owner.id, issueForm.owner_id]);

  useEffect(() => {
    if (draftQuality && Object.keys(qualityForm).length <= 4) {
      setQualityForm({ judgement: draftQuality.judgement, strengths: draftQuality.strengths, blockers: draftQuality.blockers, conditions: draftQuality.conditions, ...draftQuality.answers });
    }
  }, [draftQuality, qualityForm]);

  useEffect(() => {
    if (draftSummary && Object.keys(summaryForm).length === 0) {
      setSummaryForm(Object.fromEntries(SUMMARY_FIELDS.map(([key]) => [key, draftSummary[key]])));
    }
  }, [draftSummary, summaryForm]);

  if (analysis.isPending || decision.isPending) return <p>Loading integrated decision analysis…</p>;
  if (analysis.isError || !analysis.data || decision.isError || !decision.data) {
    return <StatusMessage kind="error">The integrated decision analysis could not be loaded.</StatusMessage>;
  }

  const workspace = analysis.data;
  const canManage = workspace.capabilities.can_manage;
  const canContribute = workspace.capabilities.can_contribute;

  function submitIssue(event: FormEvent) {
    event.preventDefault();
    issueMutation.mutate();
  }

  return (
    <div className="decision-analysis-page">
      <Link className="back-link" to={`/decisions/${decisionId}`}>← Decision workspace</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Integrated decision analysis</p>
          <h1>{workspace.decision.title}</h1>
          <p className="decision-question">{workspace.decision.question}</p>
        </div>
        <span className="status-badge">{workspace.decision.status_label}</span>
      </div>

      <StatusMessage kind="info">{workspace.principle}</StatusMessage>

      <PageHelp title="What each section of this analysis shows">
        <p>
          <strong>Option comparison</strong> lays each option's evidence, assumptions, risks, and
          collective evaluation scores side by side. <strong>Gaps and contradictions</strong>{" "}
          surfaces where evidence conflicts or coverage is thin, so it can be resolved before the
          decision is finalised. <strong>Decision quality</strong> is a structured, versioned
          reviewer judgement on whether the reasoning behind the decision is sound - not a score
          on the options themselves. <strong>Executive summary</strong> is a human-approved,
          versioned synthesis for people who need the outcome and rationale without the full trace.
        </p>
      </PageHelp>

      <section className="analysis-summary-strip" aria-label="Analysis summary">
        <div><strong>{workspace.options.length}</strong><span>active options</span></div>
        <div><strong>{workspace.issue_summary.open}</strong><span>open issues</span></div>
        <div><strong>{workspace.issue_summary.critical}</strong><span>critical blockers</span></div>
        <div><strong>{workspace.foresight.linked_signals.length}</strong><span>linked signals</span></div>
      </section>

      <nav className="section-tabs" aria-label="Decision analysis sections">
        {(["comparison", "issues", "quality", "summary"] as View[]).map((item) => (
          <button key={item} type="button" className={item === view ? "section-tab section-tab--active" : "section-tab"} onClick={() => setView(item)}>
            {item === "comparison" ? "Option comparison" : item === "issues" ? "Gaps and contradictions" : item === "quality" ? "Decision quality" : "Executive summary"}
          </button>
        ))}
      </nav>

      {view === "comparison" ? (
        <>
          <section className="analysis-cross-cutting">
            <div><span>Cross-cutting evidence</span><strong>{workspace.cross_cutting.evidence}</strong></div>
            <div><span>Cross-cutting assumptions</span><strong>{workspace.cross_cutting.assumptions}</strong></div>
            <div><span>Cross-cutting risks</span><strong>{workspace.cross_cutting.risks}</strong></div>
            <div><span>Reject-all positions</span><strong>{workspace.cross_cutting.do_not_support_any}</strong></div>
          </section>
          <div className="analysis-option-grid">
            {workspace.options.map((option) => (
              <article className="analysis-option-card" key={option.id}>
                <header>
                  <div><p className="eyebrow">{option.is_status_quo ? "Status quo" : "Option"}</p><h2>{option.title}</h2></div>
                  {option.issues.critical ? <span className="severity-badge severity-badge--critical">{option.issues.critical} critical</span> : null}
                </header>
                <p>{option.description}</p>
                <dl className="analysis-metric-grid">
                  <div><dt>Evidence balance</dt><dd>{option.evidence.supporting} support · {option.evidence.challenging} challenge</dd><small>{option.evidence.high_credibility_sources} high-credibility · {option.evidence.unassessed_sources} unassessed</small></div>
                  <div><dt>Assumptions</dt><dd>{option.assumptions.unverified} unverified · {option.assumptions.low_confidence} low confidence</dd><small>{option.assumptions.overdue_review} overdue review</small></div>
                  <div><dt>Risk exposure</dt><dd>{option.risks.exposure} total · {option.risks.highest_score} highest</dd><small>{option.risks.without_mitigation} without mitigation · {option.risks.overdue_review} overdue review</small></div>
                  <div><dt>Stakeholders</dt><dd>{option.stakeholders.support} support · {option.stakeholders.conditional} conditional</dd></div>
                  <div><dt>Scenario robustness</dt><dd>{option.scenarios.average_robustness ?? "Not assessed"}{option.scenarios.minimum_robustness !== null ? ` average · ${option.scenarios.minimum_robustness} minimum` : ""}</dd></div>
                  <div><dt>Open issues</dt><dd>{option.issues.open}</dd></div>
                </dl>
                {option.evaluations.length ? (
                  <div className="analysis-evaluation-list">
                    <strong>Collective evaluation</strong>
                    {option.evaluations.map((evaluation) => (
                      <p key={evaluation.exercise_id}>{evaluation.exercise_title}: {evaluation.weighted_score ?? evaluation.approval_rate ?? "Reviewed"}{evaluation.weighted_score != null ? " weighted score" : evaluation.approval_rate != null ? "% approval" : ""}</p>
                    ))}
                  </div>
                ) : <p className="muted">No closed collective evaluation is available for this option.</p>}
              </article>
            ))}
          </div>
          <section className="workspace-detail-section">
            <p className="eyebrow">Foresight connection</p><h2>Signals and strategic implications</h2>
            <div className="analysis-foresight-grid">
              <div><h3>Linked signals</h3>{workspace.foresight.linked_signals.length ? <ul>{workspace.foresight.linked_signals.map((item) => <li key={item.id}><strong>{item.title}</strong><span>{item.relevance}</span></li>)}</ul> : <p className="muted">No signals are linked.</p>}</div>
              <div><h3>Strategic implications</h3>{workspace.foresight.implications.length ? <ul>{workspace.foresight.implications.map((item) => <li key={item.id}><strong>{item.title}</strong><span>{item.canvas_title} · priority {item.priority}</span></li>)}</ul> : <p className="muted">No implications are linked.</p>}</div>
            </div>
          </section>
          {workspace.minority_reports.length ? (
            <section className="workspace-detail-section">
              <p className="eyebrow">Preserved disagreement</p><h2>Minority reports</h2>
              <div className="version-history-list">{workspace.minority_reports.map((item) => <article className="version-history-card" key={item.id}><strong>{item.title}</strong><span>{item.exercise_title} · {new Date(item.published_at).toLocaleDateString()}</span><p>{item.analysis}</p>{item.recommendation ? <p><b>Alternative recommendation:</b> {item.recommendation}</p> : null}</article>)}</div>
            </section>
          ) : null}
        </>
      ) : null}

      {view === "issues" ? (
        <div className="analysis-two-column">
          <section className="workspace-detail-section">
            <p className="eyebrow">Contradiction and gap register</p><h2>Issues requiring human attention</h2>
            {issues.data?.length ? <ul className="analysis-issue-list">{issues.data.map((issue) => (
              <li key={issue.id}>
                <div><span className={`severity-badge severity-badge--${issue.severity}`}>{issue.severity_label}</span><strong>{issue.title}</strong><p>{issue.description}</p><small>{issue.issue_type_label} · {userName(issue.owner)}{issue.due_date ? ` · due ${issue.due_date}` : ""}</small></div>
                {issue.can_edit && (issue.status === "open" || issue.status === "in_progress") ? <div className="issue-actions"><button type="button" className="button button--secondary" onClick={() => issueUpdate.mutate({ issue, input: { status: "in_progress" } })}>Start</button><button type="button" className="button button--secondary" onClick={() => { const resolution = window.prompt("How was this issue resolved?"); if (resolution) issueUpdate.mutate({ issue, input: { status: "resolved", resolution } }); }}>Resolve</button></div> : <span className="status-badge">{issue.status_label}</span>}
              </li>
            ))}</ul> : <p className="muted">No governed analysis issues have been recorded.</p>}
          </section>
          <section className="workspace-detail-section">
            <p className="eyebrow">Human acceptance</p><h2>Add an issue</h2>
            {!canContribute ? <StatusMessage kind="info">You have read-only access to the analysis register.</StatusMessage> : null}
            <form onSubmit={submitIssue}>
              <label htmlFor="analysis-issue-type">Issue type</label><select id="analysis-issue-type" value={issueForm.issue_type} onChange={(event) => setIssueForm({ ...issueForm, issue_type: event.target.value })}><option value="evidence_contradiction">Evidence contradiction</option><option value="missing_evidence">Missing evidence</option><option value="unsupported_assumption">Unsupported assumption</option><option value="stakeholder_gap">Stakeholder gap</option><option value="unresolved_objection">Unresolved objection</option><option value="scenario_vulnerability">Scenario vulnerability</option><option value="resource_uncertainty">Resource uncertainty</option><option value="implementation_uncertainty">Implementation uncertainty</option><option value="other">Other</option></select>
              <label htmlFor="analysis-issue-title">Title</label><input id="analysis-issue-title" required value={issueForm.title} onChange={(event) => setIssueForm({ ...issueForm, title: event.target.value })} />
              <label htmlFor="analysis-issue-description">Description</label><textarea id="analysis-issue-description" required rows={5} value={issueForm.description} onChange={(event) => setIssueForm({ ...issueForm, description: event.target.value })} />
              <div className="form-row"><div><label htmlFor="analysis-issue-severity">Severity</label><select id="analysis-issue-severity" value={issueForm.severity} onChange={(event) => setIssueForm({ ...issueForm, severity: event.target.value })}><option value="low">Low</option><option value="moderate">Moderate</option><option value="high">High</option><option value="critical">Critical</option></select></div><div><label htmlFor="analysis-issue-option">Option</label><select id="analysis-issue-option" value={issueForm.option_id} onChange={(event) => setIssueForm({ ...issueForm, option_id: event.target.value })}><option value="">Cross-cutting</option>{workspace.options.map((option) => <option value={option.id} key={option.id}>{option.title}</option>)}</select></div></div>
              <label htmlFor="analysis-issue-owner">Owner</label><select id="analysis-issue-owner" value={issueForm.owner_id} onChange={(event) => setIssueForm({ ...issueForm, owner_id: event.target.value })}>{memberships.data?.map((membership) => <option key={membership.user.id} value={membership.user.id}>{userName(membership.user)}</option>)}</select>
              <label htmlFor="analysis-issue-due">Due date</label><input id="analysis-issue-due" type="date" value={issueForm.due_date} onChange={(event) => setIssueForm({ ...issueForm, due_date: event.target.value })} />
              {issueMutation.isError ? <StatusMessage kind="error">{issueMutation.error.message}</StatusMessage> : null}
              <button className="button button--primary" type="submit" disabled={!canContribute || !issueForm.owner_id || issueMutation.isPending}>{issueMutation.isPending ? "Adding…" : "Add governed issue"}</button>
            </form>
          </section>
        </div>
      ) : null}

      {view === "quality" ? (
        <section className="workspace-detail-section">
          <p className="eyebrow">Decision-quality review</p><h2>Human judgement, not a universal score</h2>
          {!canManage ? <StatusMessage kind="info">Only the decision owner, a decision maker, or an organisation manager may author and publish this review.</StatusMessage> : null}
          <div className="quality-question-list">{QUALITY_QUESTIONS.map(([key, label]) => <label key={key}><span>{label}</span><select value={qualityForm[key] ?? "not_applicable"} onChange={(event) => setQualityForm({ ...qualityForm, [key]: event.target.value })} disabled={!canManage}><option value="yes">Yes</option><option value="partly">Partly</option><option value="no">No</option><option value="not_applicable">Not applicable</option></select></label>)}</div>
          <label htmlFor="quality-judgement">Overall judgement</label><select id="quality-judgement" value={qualityForm.judgement ?? "not_ready"} onChange={(event) => setQualityForm({ ...qualityForm, judgement: event.target.value })} disabled={!canManage}><option value="not_ready">Not ready</option><option value="ready_with_conditions">Ready with conditions</option><option value="ready">Ready</option></select>
          <label htmlFor="quality-strengths">Strengths</label><textarea id="quality-strengths" rows={4} value={qualityForm.strengths ?? ""} onChange={(event) => setQualityForm({ ...qualityForm, strengths: event.target.value })} disabled={!canManage} />
          <label htmlFor="quality-blockers">Blockers</label><textarea id="quality-blockers" rows={4} value={qualityForm.blockers ?? ""} onChange={(event) => setQualityForm({ ...qualityForm, blockers: event.target.value })} disabled={!canManage} />
          <label htmlFor="quality-conditions">Conditions</label><textarea id="quality-conditions" rows={4} value={qualityForm.conditions ?? ""} onChange={(event) => setQualityForm({ ...qualityForm, conditions: event.target.value })} disabled={!canManage} />
          {qualityMutation.isError ? <StatusMessage kind="error">{qualityMutation.error.message}</StatusMessage> : null}
          {canManage ? <div className="form-actions"><button className="button button--secondary" type="button" onClick={() => qualityMutation.mutate({ publish: false })}>Save draft</button><button className="button button--primary" type="button" onClick={() => qualityMutation.mutate({ publish: true })}>Publish review</button></div> : null}
          {qualityReviews.data?.filter((item) => item.status !== "draft").map((item: DecisionQualityReview) => <article className="version-history-card" key={item.id}><strong>Version {item.version} · {item.judgement_label}</strong><span>{item.status_label}{item.published_at ? ` · ${new Date(item.published_at).toLocaleString()}` : ""}</span><p>{item.blockers || item.strengths}</p></article>)}
        </section>
      ) : null}

      {view === "summary" ? (
        <section className="workspace-detail-section">
          <p className="eyebrow">Executive synthesis</p><h2>Traceable, versioned, human-approved summary</h2>
          {!canManage ? <StatusMessage kind="info">Only accountable decision authorities may author or approve the executive summary.</StatusMessage> : null}
          <div className="executive-summary-form">{SUMMARY_FIELDS.map(([key, label]) => <div key={key}><label htmlFor={`summary-${key}`}>{label}</label><textarea id={`summary-${key}`} rows={key === "proposed_judgement" ? 6 : 4} value={summaryForm[key] ?? ""} onChange={(event) => setSummaryForm({ ...summaryForm, [key]: event.target.value })} disabled={!canManage} /></div>)}</div>
          {summaryMutation.isError ? <StatusMessage kind="error">{summaryMutation.error.message}</StatusMessage> : null}
          {canManage ? <div className="form-actions"><button className="button button--secondary" type="button" onClick={() => summaryMutation.mutate({ approve: false })}>Save draft</button><button className="button button--primary" type="button" onClick={() => summaryMutation.mutate({ approve: true })}>Approve summary</button></div> : null}
          {summaries.data?.filter((item) => item.status !== "draft").map((item: ExecutiveDecisionSummary) => <article className="version-history-card" key={item.id}><strong>Version {item.version} · {item.status_label}</strong><span>{item.approved_at ? new Date(item.approved_at).toLocaleString() : ""}</span><p>{item.proposed_judgement}</p></article>)}
        </section>
      ) : null}
    </div>
  );
}
