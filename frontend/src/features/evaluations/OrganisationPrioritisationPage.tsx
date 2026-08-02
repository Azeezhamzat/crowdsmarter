import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { PrioritisationPortfolio } from "../../lib/types";
import { getOrganisationPortfolio } from "../portfolio/api";
import { getOrganisation, listMemberships } from "../organisations/api";
import {
  addPortfolioCandidate,
  addPortfolioCriterion,
  createPrioritisation,
  getPrioritisation,
  listPrioritisations,
  savePortfolioAssessment,
  savePortfolioSelection,
  updatePrioritisation,
} from "./api";

function message(error: unknown): string {
  return error instanceof ApiError ? error.message : "The prioritisation action failed.";
}

export function OrganisationPrioritisationPage() {
  const { organisationId = "" } = useParams<{ organisationId: string }>();
  const client = useQueryClient();
  const [selectedId, setSelectedId] = useState("");
  const [title, setTitle] = useState("");
  const [purpose, setPurpose] = useState("");
  const [budget, setBudget] = useState("");
  const [capacity, setCapacity] = useState("");
  const [anonymity, setAnonymity] = useState<PrioritisationPortfolio["anonymity"]>("peer_anonymous");
  const [blindResults, setBlindResults] = useState(true);
  const [ownerId, setOwnerId] = useState("");

  const organisation = useQuery({ queryKey: ["organisations", organisationId], queryFn: () => getOrganisation(organisationId), enabled: Boolean(organisationId) });
  const memberships = useQuery({ queryKey: ["organisations", organisationId, "memberships"], queryFn: () => listMemberships(organisationId), enabled: Boolean(organisationId) });
  const decisionPortfolio = useQuery({ queryKey: ["portfolio", organisationId, "all"], queryFn: () => getOrganisationPortfolio(organisationId, {}), enabled: Boolean(organisationId) });
  const portfolios = useQuery({ queryKey: ["prioritisations", organisationId], queryFn: () => listPrioritisations(organisationId), enabled: Boolean(organisationId) });
  const portfolio = useQuery({ queryKey: ["prioritisation", selectedId], queryFn: () => getPrioritisation(selectedId), enabled: Boolean(selectedId) });

  useEffect(() => {
    if (!ownerId && memberships.data?.length) {
      const owner = memberships.data.find((item) => item.role === "owner" && item.status === "active") ?? memberships.data.find((item) => item.status === "active");
      if (owner) setOwnerId(owner.user.id);
    }
  }, [memberships.data, ownerId]);

  useEffect(() => {
    if (!selectedId) {
      const first = portfolios.data?.at(0);
      if (first) setSelectedId(first.id);
    }
  }, [portfolios.data, selectedId]);

  async function refresh(id?: string) {
    await client.invalidateQueries({ queryKey: ["prioritisations", organisationId] });
    if (id ?? selectedId) await client.invalidateQueries({ queryKey: ["prioritisation", id ?? selectedId] });
  }

  const create = useMutation({
    mutationFn: () => createPrioritisation(organisationId, {
      title,
      purpose,
      budget_limit: budget || null,
      capacity_limit: capacity || null,
      anonymity,
      blind_results_until_close: blindResults,
      owner_id: ownerId,
    }),
    onSuccess: async (item) => {
      setSelectedId(item.id);
      setTitle("");
      setPurpose("");
      setBudget("");
      setCapacity("");
      await refresh(item.id);
    },
  });

  if (organisation.isPending || memberships.isPending || portfolios.isPending || decisionPortfolio.isPending) return <p>Loading prioritisation workspace…</p>;
  if (organisation.isError || memberships.isError || portfolios.isError || decisionPortfolio.isError || !organisation.data) return <StatusMessage kind="error">The prioritisation workspace could not be loaded.</StatusMessage>;

  return (
    <div className="phase14-page">
      <Link className="back-link" to={`/organisations/${organisationId}`}>← Organisation</Link>
      <header className="page-header phase14-hero">
        <div><p className="eyebrow">Portfolio prioritisation</p><h1>{organisation.data.name}</h1><p>Compare strategic value collectively, expose uncertainty, and test a transparent recommendation against budget and capacity.</p></div>
        <div className="phase14-principle"><strong>Constraint-aware</strong><span>The recommendation is explainable support, never an automatic portfolio decision.</span></div>
      </header>

      {create.error ? <StatusMessage kind="error">{message(create.error)}</StatusMessage> : null}

      <div className="evaluation-layout">
        <aside className="evaluation-sidebar">
          <section className="panel-card">
            <p className="eyebrow">New portfolio</p><h2>Define the decision envelope</h2>
            <form className="stack-form" onSubmit={(event) => { event.preventDefault(); create.mutate(); }}>
              <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} required /></label>
              <label>Purpose<textarea rows={3} value={purpose} onChange={(event) => setPurpose(event.target.value)} /></label>
              <label>Budget limit<input type="number" min="0" step="0.01" value={budget} onChange={(event) => setBudget(event.target.value)} placeholder="Optional" /></label>
              <label>Capacity limit<input type="number" min="0" step="0.01" value={capacity} onChange={(event) => setCapacity(event.target.value)} placeholder="Optional units" /></label>
              <label>Assessment identity<select value={anonymity} onChange={(event) => setAnonymity(event.target.value as PrioritisationPortfolio["anonymity"])}><option value="peer_anonymous">Anonymous to peers</option><option value="attributed">Attributable</option></select></label>
              <label className="checkbox-row"><input type="checkbox" checked={blindResults} onChange={(event) => setBlindResults(event.target.checked)} /><span>Seal aggregate results until closure</span></label>
              <label>Accountable owner<select value={ownerId} onChange={(event) => setOwnerId(event.target.value)}>{memberships.data?.filter((item) => item.status === "active").map((item) => <option key={item.user.id} value={item.user.id}>{item.user.first_name || item.user.last_name ? `${item.user.first_name} ${item.user.last_name}`.trim() : item.user.email}</option>)}</select></label>
              <button className="button button--primary" disabled={create.isPending || !title.trim() || !ownerId}>{create.isPending ? "Creating…" : "Create portfolio"}</button>
            </form>
          </section>
          <section className="panel-card"><p className="eyebrow">Portfolios</p><div className="evaluation-list">{portfolios.data?.map((item) => <button key={item.id} type="button" className={selectedId === item.id ? "evaluation-list__item is-active" : "evaluation-list__item"} onClick={() => setSelectedId(item.id)}><span><strong>{item.title}</strong><small>{item.candidates.length} candidates</small></span><span className={`status-badge status-badge--${item.status}`}>{item.status}</span></button>)}</div></section>
        </aside>

        <main className="evaluation-main">
          {portfolio.isPending && selectedId ? <p>Loading portfolio…</p> : null}
          {portfolio.error ? <StatusMessage kind="error">{message(portfolio.error)}</StatusMessage> : null}
          {portfolio.data ? <PortfolioWorkspace portfolio={portfolio.data} decisions={decisionPortfolio.data?.decisions ?? []} onRefresh={() => refresh(portfolio.data.id)} /> : !selectedId ? <section className="panel-card empty-state"><h2>Create a prioritisation portfolio</h2><p>Set the resource envelope, define weighted criteria, add candidate decisions, then invite independent assessments.</p></section> : null}
        </main>
      </div>
    </div>
  );
}

function PortfolioWorkspace({ portfolio, decisions, onRefresh }: { portfolio: PrioritisationPortfolio; decisions: Array<{ id: string; title: string; status: string }>; onRefresh: () => Promise<void> }) {
  const [criterionTitle, setCriterionTitle] = useState("");
  const [criterionDescription, setCriterionDescription] = useState("");
  const [criterionWeight, setCriterionWeight] = useState("1");
  const [decisionId, setDecisionId] = useState("");
  const [budgetRequired, setBudgetRequired] = useState("0");
  const [capacityRequired, setCapacityRequired] = useState("0");
  const [mandatory, setMandatory] = useState(false);

  const update = useMutation({ mutationFn: (status: PrioritisationPortfolio["status"]) => updatePrioritisation(portfolio.id, { status }), onSuccess: onRefresh });
  const criterion = useMutation({ mutationFn: () => addPortfolioCriterion(portfolio.id, { title: criterionTitle, description: criterionDescription, weight: criterionWeight, higher_is_better: true, order: portfolio.criteria.length }), onSuccess: async () => { setCriterionTitle(""); setCriterionDescription(""); await onRefresh(); } });
  const candidate = useMutation({ mutationFn: () => addPortfolioCandidate(portfolio.id, { decision_id: decisionId, budget_required: budgetRequired, capacity_required: capacityRequired, mandatory, rationale: "" }), onSuccess: async () => { setDecisionId(""); setBudgetRequired("0"); setCapacityRequired("0"); setMandatory(false); await onRefresh(); } });

  const availableDecisions = decisions.filter((item) => !portfolio.candidates.some((candidateItem) => candidateItem.decision_id === item.id));
  const selectedCount = portfolio.recommendation.candidates.filter((item) => item.recommended).length;

  return (
    <div className="evaluation-workspace">
      <section className="panel-card evaluation-summary">
        <div><div className="heading-badges"><span className={`status-badge status-badge--${portfolio.status}`}>{portfolio.status}</span><span className="role-badge">Budget {portfolio.budget_limit ?? "unbounded"}</span><span className="role-badge">Capacity {portfolio.capacity_limit ?? "unbounded"}</span></div><h2>{portfolio.title}</h2><p>{portfolio.purpose || "No purpose recorded."}</p></div>
        <div className="evaluation-metrics"><div><strong>{portfolio.criteria.length}</strong><span>criteria</span></div><div><strong>{portfolio.candidates.length}</strong><span>candidates</span></div><div><strong>{portfolio.recommendation.hidden ? "—" : selectedCount}</strong><span>recommended</span></div><div><strong>{portfolio.recommendation.hidden ? "—" : portfolio.recommendation.recommended_budget}</strong><span>budget used</span></div></div>
      </section>

      {update.error || criterion.error || candidate.error ? <StatusMessage kind="error">{message(update.error ?? criterion.error ?? candidate.error)}</StatusMessage> : null}

      {portfolio.can_manage && portfolio.status === "draft" ? (
        <section className="panel-card">
          <div className="section-heading"><div><p className="eyebrow">Evaluation frame</p><h2>Criteria and candidate decisions</h2></div></div>
          <div className="criteria-strip">{portfolio.criteria.map((item) => <article key={item.id}><strong>{item.title}</strong><span>Weight {item.weight}</span><p>{item.description || "No description"}</p></article>)}</div>
          <form className="inline-form phase14-inline-form" onSubmit={(event) => { event.preventDefault(); criterion.mutate(); }}><label>Criterion<input value={criterionTitle} onChange={(event) => setCriterionTitle(event.target.value)} required /></label><label>Description<input value={criterionDescription} onChange={(event) => setCriterionDescription(event.target.value)} /></label><label>Weight<input type="number" min="0.01" step="0.01" value={criterionWeight} onChange={(event) => setCriterionWeight(event.target.value)} /></label><button className="button button--secondary">Add criterion</button></form>
          <form className="inline-form phase14-inline-form candidate-form" onSubmit={(event) => { event.preventDefault(); candidate.mutate(); }}><label>Candidate decision<select value={decisionId} onChange={(event) => setDecisionId(event.target.value)} required><option value="">Select decision</option>{availableDecisions.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label><label>Budget required<input type="number" min="0" step="0.01" value={budgetRequired} onChange={(event) => setBudgetRequired(event.target.value)} /></label><label>Capacity required<input type="number" min="0" step="0.01" value={capacityRequired} onChange={(event) => setCapacityRequired(event.target.value)} /></label><label className="checkbox-field"><input type="checkbox" checked={mandatory} onChange={(event) => setMandatory(event.target.checked)} />Mandatory commitment</label><button className="button button--secondary" disabled={!decisionId}>Add candidate</button></form>
          <button className="button button--primary" type="button" disabled={!portfolio.criteria.length || !portfolio.candidates.length || update.isPending} onClick={() => update.mutate("open")}>Open independent assessment</button>
        </section>
      ) : null}

      <section className="panel-card">
        <div className="section-heading"><div><p className="eyebrow">Collective assessment</p><h2>Value under constraints</h2></div>{portfolio.can_manage && portfolio.status === "open" ? <button className="button button--secondary" type="button" onClick={() => update.mutate("closed")}>Close assessment</button> : null}</div>
        <div className="portfolio-candidate-stack">{portfolio.candidates.map((item) => <CandidateAssessment key={item.id} candidate={item} criteria={portfolio.criteria} canAssess={portfolio.can_assess && portfolio.status === "open"} canManage={portfolio.can_manage && portfolio.status === "closed"} onRefresh={onRefresh} />)}</div>
      </section>

      <section className="panel-card recommendation-panel">
        <div className="section-heading"><div><p className="eyebrow">Explainable recommendation</p><h2>Suggested constrained portfolio</h2></div><div className="constraint-totals"><span>{portfolio.recommendation.recommended_budget} budget</span><span>{portfolio.recommendation.recommended_capacity} capacity</span></div></div>
        <p className="muted">{portfolio.recommendation.warning}</p>
        {portfolio.recommendation.hidden ? (
          <div className="sealed-results"><strong>Independent assessments are sealed</strong><p>Aggregate scores and the constrained recommendation become visible after the portfolio closes.</p></div>
        ) : (
          <div className="recommendation-list">{portfolio.recommendation.candidates.map((item, index) => <article className={item.recommended ? "is-recommended" : ""} key={item.candidate_id}><span className="rank-number">{index + 1}</span><div><strong>{item.title}</strong><p>Score {item.score.toFixed(1)} · {item.assessor_count} assessors · confidence {item.confidence ?? "—"}</p><small>Budget {item.budget_required} · Capacity {item.capacity_required}{item.mandatory ? " · Mandatory" : ""}</small>{item.constraint_reason ? <em>{item.constraint_reason}</em> : null}</div><span className={item.recommended ? "role-badge" : "status-badge"}>{item.recommended ? "Recommended" : "Outside envelope"}</span></article>)}</div>
        )}
      </section>
    </div>
  );
}

function CandidateAssessment({ candidate, criteria, canAssess, canManage, onRefresh }: { candidate: PrioritisationPortfolio["candidates"][number]; criteria: PrioritisationPortfolio["criteria"]; canAssess: boolean; canManage: boolean; onRefresh: () => Promise<void> }) {
  const [criterionId, setCriterionId] = useState(criteria[0]?.id ?? "");
  const [score, setScore] = useState("50");
  const [confidence, setConfidence] = useState(3);
  const [rationale, setRationale] = useState("");
  const [selectionRationale, setSelectionRationale] = useState(candidate.selection?.rationale ?? "");
  const assess = useMutation({ mutationFn: () => savePortfolioAssessment(candidate.id, { criterion_id: criterionId, score, confidence, rationale }), onSuccess: async () => { setRationale(""); await onRefresh(); } });
  const select = useMutation({ mutationFn: (selected: boolean) => savePortfolioSelection(candidate.id, { selected, priority_order: null, approved_budget: selected ? candidate.budget_required : null, approved_capacity: selected ? candidate.capacity_required : null, rationale: selectionRationale }), onSuccess: onRefresh });

  function submit(event: FormEvent) { event.preventDefault(); assess.mutate(); }

  return (
    <article className="candidate-card">
      <header><div><strong>{candidate.decision_title}</strong><span>{candidate.decision_status.replaceAll("_", " ")}</span></div><div className="heading-badges">{candidate.mandatory ? <span className="role-badge">Mandatory</span> : null}{candidate.selection ? <span className={candidate.selection.selected ? "role-badge" : "status-badge"}>{candidate.selection.selected ? "Selected" : "Not selected"}</span> : null}</div></header>
      <div className="candidate-costs"><span>Budget <strong>{candidate.budget_required}</strong></span><span>Capacity <strong>{candidate.capacity_required}</strong></span><span>Assessments <strong>{candidate.assessments.length}</strong></span></div>
      {assess.error || select.error ? <StatusMessage kind="error">{message(assess.error ?? select.error)}</StatusMessage> : null}
      {canAssess ? <form className="candidate-assessment-form" onSubmit={submit}><label>Criterion<select value={criterionId} onChange={(event) => setCriterionId(event.target.value)}>{criteria.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label><label>Score (0–100)<input type="number" min="0" max="100" step="0.1" value={score} onChange={(event) => setScore(event.target.value)} /></label><label>Confidence ({confidence}/5)<input type="range" min="1" max="5" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} /></label><label>Rationale<input value={rationale} onChange={(event) => setRationale(event.target.value)} /></label><button className="button button--secondary" disabled={!criterionId || assess.isPending}>Save assessment</button></form> : null}
      {canManage ? <div className="selection-controls"><label>Authority rationale<input value={selectionRationale} onChange={(event) => setSelectionRationale(event.target.value)} /></label><button className="button button--primary" type="button" onClick={() => select.mutate(true)}>Record selection</button><button className="button button--secondary" type="button" onClick={() => select.mutate(false)}>Record exclusion</button></div> : null}
    </article>
  );
}
