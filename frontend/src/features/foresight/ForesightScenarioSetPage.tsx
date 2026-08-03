import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { ForesightScenario } from "../../lib/types";
import { listAssumptions, listRisks } from "../reasoning/api";
import {
  assessScenarioOption,
  createScenario,
  createScenarioSignpost,
  createSignpostObservation,
  getForesightCanvas,
  getScenarioSet,
  linkScenarioImplication,
  linkSignpostToAssumption,
  linkSignpostToRisk,
  listSources,
  setScenarioDriverState,
  submitScenarioReview,
  updateScenarioSet,
} from "./api";
import { personName } from "./canvasTypes";

type ScenarioTab = "worlds" | "reviews" | "wind-tunnel" | "signposts";

const EMPTY_SCENARIO = {
  title: "",
  code: "",
  axis_x_position: "low",
  axis_y_position: "low",
  headline: "",
  narrative: "",
  key_assumptions: "",
  opportunities: "",
  threats: "",
};

const EMPTY_DRIVER_STATE = {
  scenario_id: "",
  driver_id: "",
  state: "uncertain",
  salience: 3,
  description: "",
};

const EMPTY_REVIEW = {
  scenario_id: "",
  plausibility: 3,
  internal_consistency: 3,
  distinctiveness: 3,
  usefulness: 3,
  confidence: 3,
  comment: "",
};

const EMPTY_ASSESSMENT = {
  scenario_id: "",
  option_id: "",
  verdict: "uncertain",
  desirability: 3,
  feasibility: 3,
  resilience: 3,
  rationale: "",
  conditions_for_success: "",
  vulnerabilities: "",
  mitigations: "",
};

const EMPTY_SIGNPOST = {
  title: "",
  description: "",
  indicator: "",
  threshold: "",
  direction: "change",
  review_cadence: "quarterly",
  source_notes: "",
  scenario_id: "",
  relationship: "supports",
  rationale: "",
};

const EMPTY_OBSERVATION = {
  signpost_id: "",
  observed_on: new Date().toISOString().slice(0, 10),
  value: "",
  assessment: "no_change",
  evidence: "",
  source_id: "",
};

const EMPTY_IMPLICATION = {
  scenario_id: "",
  implication_id: "",
  effect: "changes",
  rationale: "",
};

const EMPTY_WATCHLIST_LINK = {
  signpost_id: "",
  kind: "assumption" as "assumption" | "risk",
  target_id: "",
  rationale: "",
};

function errorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "The scenario action could not be completed.";
}

function score(value: number | null): string {
  return value === null ? "—" : value.toFixed(1);
}

function quadrantKey(scenario: ForesightScenario): string {
  return `${scenario.axis_x_position}-${scenario.axis_y_position}`;
}

export function ForesightScenarioSetPage() {
  const { organisationId = "", canvasId = "", scenarioSetId = "" } = useParams<{
    organisationId: string;
    canvasId: string;
    scenarioSetId: string;
  }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const tab: ScenarioTab = ["worlds", "reviews", "wind-tunnel", "signposts"].includes(
    requestedTab ?? "",
  )
    ? (requestedTab as ScenarioTab)
    : "worlds";
  const queryClient = useQueryClient();

  const [scenarioForm, setScenarioForm] = useState(EMPTY_SCENARIO);
  const [driverStateForm, setDriverStateForm] = useState(EMPTY_DRIVER_STATE);
  const [reviewForm, setReviewForm] = useState(EMPTY_REVIEW);
  const [assessmentForm, setAssessmentForm] = useState(EMPTY_ASSESSMENT);
  const [signpostForm, setSignpostForm] = useState(EMPTY_SIGNPOST);
  const [observationForm, setObservationForm] = useState(EMPTY_OBSERVATION);
  const [implicationForm, setImplicationForm] = useState(EMPTY_IMPLICATION);
  const [watchlistForm, setWatchlistForm] = useState(EMPTY_WATCHLIST_LINK);

  const scenarioSet = useQuery({
    queryKey: ["foresight", "scenario-sets", scenarioSetId],
    queryFn: () => getScenarioSet(scenarioSetId),
    enabled: Boolean(scenarioSetId),
  });
  const canvas = useQuery({
    queryKey: ["foresight", "canvases", canvasId],
    queryFn: () => getForesightCanvas(canvasId),
    enabled: Boolean(canvasId),
  });
  const sources = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "sources"],
    queryFn: () => listSources(organisationId),
    enabled: Boolean(organisationId),
  });
  const linkedDecisionId = scenarioSet.data?.linked_decision_id ?? null;
  const linkedAssumptions = useQuery({
    queryKey: ["decisions", linkedDecisionId, "assumptions"],
    queryFn: () => listAssumptions(linkedDecisionId as string),
    enabled: Boolean(linkedDecisionId),
  });
  const linkedRisks = useQuery({
    queryKey: ["decisions", linkedDecisionId, "risks"],
    queryFn: () => listRisks(linkedDecisionId as string),
    enabled: Boolean(linkedDecisionId),
  });

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["foresight", "scenario-sets", scenarioSetId],
      }),
      queryClient.invalidateQueries({
        queryKey: ["foresight", "canvases", canvasId],
      }),
      queryClient.invalidateQueries({
        queryKey: ["organisations", organisationId, "search"],
      }),
    ]);
  };

  const createWorld = useMutation({
    mutationFn: () => createScenario(scenarioSetId, scenarioForm),
    onSuccess: async () => {
      setScenarioForm(EMPTY_SCENARIO);
      await refresh();
    },
  });
  const setDriverState = useMutation({
    mutationFn: () => {
      const { scenario_id, ...input } = driverStateForm;
      return setScenarioDriverState(scenario_id, input);
    },
    onSuccess: async () => {
      setDriverStateForm(EMPTY_DRIVER_STATE);
      await refresh();
    },
  });
  const reviewScenario = useMutation({
    mutationFn: () => {
      const { scenario_id, ...input } = reviewForm;
      return submitScenarioReview(scenario_id, input);
    },
    onSuccess: async () => {
      setReviewForm(EMPTY_REVIEW);
      await refresh();
    },
  });
  const assessOption = useMutation({
    mutationFn: () => {
      const { scenario_id, ...input } = assessmentForm;
      return assessScenarioOption(scenario_id, input);
    },
    onSuccess: async () => {
      setAssessmentForm(EMPTY_ASSESSMENT);
      await refresh();
    },
  });
  const createSignpost = useMutation({
    mutationFn: () => {
      const { scenario_id, relationship, rationale, ...input } = signpostForm;
      return createScenarioSignpost(scenarioSetId, {
        ...input,
        scenario_links: scenario_id
          ? [{ scenario_id, relationship, rationale }]
          : [],
      });
    },
    onSuccess: async () => {
      setSignpostForm(EMPTY_SIGNPOST);
      await refresh();
    },
  });
  const observeSignpost = useMutation({
    mutationFn: () => {
      const { signpost_id, source_id, ...input } = observationForm;
      return createSignpostObservation(signpost_id, {
        ...input,
        source_id: source_id || null,
      });
    },
    onSuccess: async () => {
      setObservationForm(EMPTY_OBSERVATION);
      await refresh();
    },
  });
  const linkImplication = useMutation({
    mutationFn: () => {
      const { scenario_id, ...input } = implicationForm;
      return linkScenarioImplication(scenario_id, input);
    },
    onSuccess: async () => {
      setImplicationForm(EMPTY_IMPLICATION);
      await refresh();
    },
  });
  const updateSet = useMutation({
    mutationFn: (status: string) => updateScenarioSet(scenarioSetId, { status }),
    onSuccess: refresh,
  });
  const linkWatchlist = useMutation({
    mutationFn: () => {
      const { signpost_id, kind, target_id, rationale } = watchlistForm;
      return kind === "assumption"
        ? linkSignpostToAssumption(signpost_id, { assumption_id: target_id, rationale })
        : linkSignpostToRisk(signpost_id, { risk_id: target_id, rationale });
    },
    onSuccess: async () => {
      setWatchlistForm(EMPTY_WATCHLIST_LINK);
      await refresh();
    },
  });

  const mutations = [
    createWorld,
    setDriverState,
    reviewScenario,
    assessOption,
    createSignpost,
    observeSignpost,
    linkImplication,
    updateSet,
    linkWatchlist,
  ];
  const mutationError = mutations.map((item) => item.error).find(Boolean);

  const data = scenarioSet.data;
  const canvasData = canvas.data;
  const worldsByQuadrant = useMemo(() => {
    const values = new Map<string, ForesightScenario>();
    for (const scenario of data?.scenarios ?? []) values.set(quadrantKey(scenario), scenario);
    return values;
  }, [data?.scenarios]);

  if (scenarioSet.isPending || canvas.isPending) return <p>Loading scenario workspace…</p>;
  if (!data || !canvasData || scenarioSet.isError || canvas.isError) {
    return <StatusMessage kind="error">The scenario workspace could not be loaded.</StatusMessage>;
  }

  const tabs: Array<{ key: ScenarioTab; label: string }> = [
    { key: "worlds", label: "Scenario worlds" },
    { key: "reviews", label: "Collective review" },
    { key: "wind-tunnel", label: "Wind tunnel" },
    { key: "signposts", label: "Adaptive signposts" },
  ];

  const quadrants = [
    { key: "low-high", x: data.axis_x_low_label, y: data.axis_y_high_label },
    { key: "high-high", x: data.axis_x_high_label, y: data.axis_y_high_label },
    { key: "low-low", x: data.axis_x_low_label, y: data.axis_y_low_label },
    { key: "high-low", x: data.axis_x_high_label, y: data.axis_y_low_label },
  ];

  return (
    <div className="scenario-workspace-page">
      <Link
        className="back-link"
        to={`/organisations/${organisationId}/foresight/canvases/${canvasId}?tab=scenarios`}
      >
        ← Scenario sets
      </Link>

      <header className="scenario-workspace-hero">
        <div>
          <div className="inline-badges">
            <span className={`status-badge status-badge--${data.status}`}>
              {data.status_label}
            </span>
            <span className="role-badge">{data.scenarios.length}/4 worlds</span>
            {data.linked_decision_title ? (
              <Link className="role-badge" to={`/decisions/${data.linked_decision_id}`}>
                {data.linked_decision_title}
              </Link>
            ) : (
              <span className="role-badge">Exploratory</span>
            )}
          </div>
          <p className="eyebrow">Scenario intelligence</p>
          <h1>{data.title}</h1>
          <p>{data.purpose}</p>
        </div>
        <div className="scenario-workspace-owner">
          <span>Accountable owner</span>
          <strong>{personName(data.owner)}</strong>
          <label htmlFor="scenario-set-status">Exercise status</label>
          <select
            id="scenario-set-status"
            disabled={!data.can_edit || updateSet.isPending}
            value={data.status}
            onChange={(event) => updateSet.mutate(event.target.value)}
          >
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="complete">Complete</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </header>

      {mutationError ? (
        <StatusMessage kind="error">{errorMessage(mutationError)}</StatusMessage>
      ) : null}

      <section className="foresight-canvas-metrics" aria-label="Scenario summary">
        <article><strong>{data.summary.scenario_count}</strong><span>scenario worlds</span></article>
        <article><strong>{data.summary.review_count}</strong><span>member reviews</span></article>
        <article><strong>{data.summary.assessment_count}</strong><span>option tests</span></article>
        <article><strong>{data.summary.robust_assessment_count}</strong><span>robust verdicts</span></article>
        <article><strong>{data.summary.active_signpost_count}</strong><span>active signposts</span></article>
        <article><strong>{data.summary.observation_count}</strong><span>observations</span></article>
      </section>

      <section className="scenario-axis-banner">
        <div>
          <span>X axis · {data.axis_x_driver_title}</span>
          <strong>{data.axis_x_low_label} ↔ {data.axis_x_high_label}</strong>
        </div>
        <div>
          <span>Y axis · {data.axis_y_driver_title}</span>
          <strong>{data.axis_y_low_label} ↔ {data.axis_y_high_label}</strong>
        </div>
      </section>

      <nav className="foresight-canvas-tabs" aria-label="Scenario sections">
        {tabs.map((item) => (
          <button
            className={tab === item.key ? "is-active" : ""}
            key={item.key}
            onClick={() => setSearchParams(item.key === "worlds" ? {} : { tab: item.key })}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>

      {tab === "worlds" ? (
        <div className="scenario-tab-layout">
          <section className="page-primary">
            <div className="scenario-matrix" aria-label="Two by two scenario matrix">
              {quadrants.map((quadrant) => {
                const scenario = worldsByQuadrant.get(quadrant.key);
                return (
                  <article className="scenario-quadrant" key={quadrant.key}>
                    <div className="scenario-quadrant__axes">
                      <span>{quadrant.y}</span><span>{quadrant.x}</span>
                    </div>
                    {scenario ? (
                      <>
                        <div className="inline-badges">
                          <span className="status-badge">{scenario.code}</span>
                          <span className="role-badge">{scenario.status_label}</span>
                        </div>
                        <h3>{scenario.title}</h3>
                        <strong>{scenario.headline}</strong>
                        <p>{scenario.narrative}</p>
                        <details>
                          <summary>Assumptions and implications</summary>
                          <h4>Key assumptions</h4><p>{scenario.key_assumptions}</p>
                          <h4>Opportunities</h4><p>{scenario.opportunities || "Not recorded."}</p>
                          <h4>Threats</h4><p>{scenario.threats || "Not recorded."}</p>
                        </details>
                        <footer>
                          <span>{scenario.driver_states.length} driver states</span>
                          <span>{scenario.implication_links.length} implications</span>
                        </footer>
                      </>
                    ) : (
                      <div className="scenario-quadrant__empty">
                        <strong>World not yet written</strong>
                        <p>Use the form to develop this combination of uncertainty endpoints.</p>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>

            <div className="scenario-world-register">
              {data.scenarios.map((scenario) => (
                <article className="scenario-detail-card" key={scenario.id}>
                  <div className="section-heading">
                    <div><p className="eyebrow">{scenario.code}</p><h3>{scenario.title}</h3></div>
                    <span className="role-badge">{scenario.review_summary.review_count} reviews</span>
                  </div>
                  <p>{scenario.headline}</p>
                  <div className="scenario-state-list">
                    {scenario.driver_states.map((state) => (
                      <span key={state.id} title={state.description}>
                        {state.driver_title}: {state.state_label} ({state.salience}/5)
                      </span>
                    ))}
                    {!scenario.driver_states.length ? <span>No driver states recorded.</span> : null}
                  </div>
                  {scenario.implication_links.map((link) => (
                    <p className="scenario-implication-link" key={link.id}>
                      <strong>{link.effect_label}:</strong> {link.implication_title} — {link.rationale}
                    </p>
                  ))}
                </article>
              ))}
            </div>
          </section>

          <aside className="scenario-action-stack">
            <section className="side-panel foresight-create-panel">
              <p className="eyebrow">Narrative construction</p>
              <h2>Add scenario world</h2>
              <form onSubmit={(event) => { event.preventDefault(); createWorld.mutate(); }}>
                <div className="form-row">
                  <div><label htmlFor="scenario-code">Code</label><input id="scenario-code" required value={scenarioForm.code} onChange={(event) => setScenarioForm({ ...scenarioForm, code: event.target.value })} /></div>
                  <div><label htmlFor="scenario-title">Title</label><input id="scenario-title" required value={scenarioForm.title} onChange={(event) => setScenarioForm({ ...scenarioForm, title: event.target.value })} /></div>
                </div>
                <div className="form-row">
                  <div><label htmlFor="scenario-x-position">X position</label><select id="scenario-x-position" value={scenarioForm.axis_x_position} onChange={(event) => setScenarioForm({ ...scenarioForm, axis_x_position: event.target.value })}><option value="low">{data.axis_x_low_label}</option><option value="high">{data.axis_x_high_label}</option></select></div>
                  <div><label htmlFor="scenario-y-position">Y position</label><select id="scenario-y-position" value={scenarioForm.axis_y_position} onChange={(event) => setScenarioForm({ ...scenarioForm, axis_y_position: event.target.value })}><option value="low">{data.axis_y_low_label}</option><option value="high">{data.axis_y_high_label}</option></select></div>
                </div>
                <label htmlFor="scenario-headline">World headline</label><input id="scenario-headline" required value={scenarioForm.headline} onChange={(event) => setScenarioForm({ ...scenarioForm, headline: event.target.value })} />
                <label htmlFor="scenario-narrative">Narrative</label><textarea id="scenario-narrative" required rows={6} value={scenarioForm.narrative} onChange={(event) => setScenarioForm({ ...scenarioForm, narrative: event.target.value })} />
                <label htmlFor="scenario-assumptions">Key assumptions</label><textarea id="scenario-assumptions" required rows={4} value={scenarioForm.key_assumptions} onChange={(event) => setScenarioForm({ ...scenarioForm, key_assumptions: event.target.value })} />
                <label htmlFor="scenario-opportunities">Opportunities</label><textarea id="scenario-opportunities" rows={3} value={scenarioForm.opportunities} onChange={(event) => setScenarioForm({ ...scenarioForm, opportunities: event.target.value })} />
                <label htmlFor="scenario-threats">Threats</label><textarea id="scenario-threats" rows={3} value={scenarioForm.threats} onChange={(event) => setScenarioForm({ ...scenarioForm, threats: event.target.value })} />
                <button className="primary-button" disabled={createWorld.isPending || data.scenarios.length >= 4} type="submit">{createWorld.isPending ? "Creating…" : "Add world"}</button>
              </form>
            </section>

            <section className="side-panel foresight-create-panel">
              <p className="eyebrow">World logic</p><h2>Set driver state</h2>
              <form onSubmit={(event) => { event.preventDefault(); setDriverState.mutate(); }}>
                <label htmlFor="driver-state-scenario">Scenario</label><select id="driver-state-scenario" required value={driverStateForm.scenario_id} onChange={(event) => setDriverStateForm({ ...driverStateForm, scenario_id: event.target.value })}><option value="">Choose world</option>{data.scenarios.map((item) => <option key={item.id} value={item.id}>{item.code} — {item.title}</option>)}</select>
                <label htmlFor="driver-state-driver">Driver</label><select id="driver-state-driver" required value={driverStateForm.driver_id} onChange={(event) => setDriverStateForm({ ...driverStateForm, driver_id: event.target.value })}><option value="">Choose driver</option>{canvasData.drivers.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                <div className="form-row"><div><label htmlFor="driver-state-value">State</label><select id="driver-state-value" value={driverStateForm.state} onChange={(event) => setDriverStateForm({ ...driverStateForm, state: event.target.value })}><option value="strengthening">Strengthening</option><option value="weakening">Weakening</option><option value="stable">Stable</option><option value="volatile">Volatile</option><option value="transformed">Transformed</option><option value="uncertain">Uncertain</option></select></div><div><label htmlFor="driver-state-salience">Salience</label><input id="driver-state-salience" min={1} max={5} type="number" value={driverStateForm.salience} onChange={(event) => setDriverStateForm({ ...driverStateForm, salience: Number(event.target.value) })} /></div></div>
                <label htmlFor="driver-state-description">Interpretation</label><textarea id="driver-state-description" required rows={4} value={driverStateForm.description} onChange={(event) => setDriverStateForm({ ...driverStateForm, description: event.target.value })} />
                <button className="secondary-button" disabled={setDriverState.isPending || !data.scenarios.length} type="submit">Save driver state</button>
              </form>
            </section>

            <section className="side-panel foresight-create-panel">
              <p className="eyebrow">Traceability</p><h2>Link implication</h2>
              <form onSubmit={(event) => { event.preventDefault(); linkImplication.mutate(); }}>
                <label htmlFor="scenario-implication-scenario">Scenario</label><select id="scenario-implication-scenario" required value={implicationForm.scenario_id} onChange={(event) => setImplicationForm({ ...implicationForm, scenario_id: event.target.value })}><option value="">Choose world</option>{data.scenarios.map((item) => <option key={item.id} value={item.id}>{item.code} — {item.title}</option>)}</select>
                <label htmlFor="scenario-implication-item">Canvas implication</label><select id="scenario-implication-item" required value={implicationForm.implication_id} onChange={(event) => setImplicationForm({ ...implicationForm, implication_id: event.target.value })}><option value="">Choose implication</option>{canvasData.implications.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                <label htmlFor="scenario-implication-effect">Effect</label><select id="scenario-implication-effect" value={implicationForm.effect} onChange={(event) => setImplicationForm({ ...implicationForm, effect: event.target.value })}><option value="amplifies">Amplifies</option><option value="reduces">Reduces</option><option value="changes">Changes</option><option value="triggers">Triggers</option></select>
                <label htmlFor="scenario-implication-rationale">Rationale</label><textarea id="scenario-implication-rationale" required rows={4} value={implicationForm.rationale} onChange={(event) => setImplicationForm({ ...implicationForm, rationale: event.target.value })} />
                <button className="secondary-button" disabled={linkImplication.isPending || !canvasData.implications.length} type="submit">Link implication</button>
              </form>
            </section>
          </aside>
        </div>
      ) : null}

      {tab === "reviews" ? (
        <div className="scenario-tab-layout">
          <section className="page-primary">
            <div className="scenario-review-grid">
              {data.scenarios.map((scenario) => (
                <article className="scenario-review-card" key={scenario.id}>
                  <div className="section-heading"><div><p className="eyebrow">{scenario.code}</p><h3>{scenario.title}</h3></div><strong>{scenario.review_summary.review_count} reviewers</strong></div>
                  <div className="review-score-grid">
                    <span><strong>{score(scenario.review_summary.plausibility)}</strong>Plausibility</span>
                    <span><strong>{score(scenario.review_summary.internal_consistency)}</strong>Consistency</span>
                    <span><strong>{score(scenario.review_summary.distinctiveness)}</strong>Distinctiveness</span>
                    <span><strong>{score(scenario.review_summary.usefulness)}</strong>Usefulness</span>
                    <span><strong>{score(scenario.review_summary.confidence)}</strong>Confidence</span>
                    <span><strong>{scenario.review_summary.confidence_range ?? "—"}</strong>Confidence spread</span>
                  </div>
                  {scenario.reviews.map((review) => <blockquote key={review.id}><strong>{personName(review.reviewer)}</strong><p>{review.comment || "No written comment."}</p><small>Confidence {review.confidence}/5</small></blockquote>)}
                </article>
              ))}
            </div>
          </section>
          <aside className="side-panel foresight-create-panel">
            <p className="eyebrow">Collective judgement</p><h2>Review a scenario</h2>
            <form onSubmit={(event) => { event.preventDefault(); reviewScenario.mutate(); }}>
              <label htmlFor="review-scenario">Scenario</label><select id="review-scenario" required value={reviewForm.scenario_id} onChange={(event) => setReviewForm({ ...reviewForm, scenario_id: event.target.value })}><option value="">Choose world</option>{data.scenarios.map((item) => <option key={item.id} value={item.id}>{item.code} — {item.title}</option>)}</select>
              {(["plausibility", "internal_consistency", "distinctiveness", "usefulness", "confidence"] as const).map((field) => <div className="score-input-row" key={field}><label htmlFor={`review-${field}`}>{field.replace("_", " ")}</label><input id={`review-${field}`} min={1} max={5} type="range" value={reviewForm[field]} onChange={(event) => setReviewForm({ ...reviewForm, [field]: Number(event.target.value) })} /><strong>{reviewForm[field]}/5</strong></div>)}
              <label htmlFor="review-comment">Comment</label><textarea id="review-comment" rows={5} value={reviewForm.comment} onChange={(event) => setReviewForm({ ...reviewForm, comment: event.target.value })} />
              <button className="primary-button" disabled={reviewScenario.isPending || !data.scenarios.length} type="submit">Submit or update my review</button>
            </form>
          </aside>
        </div>
      ) : null}

      {tab === "wind-tunnel" ? (
        <div className="scenario-tab-layout">
          <section className="page-primary">
            {!data.linked_decision_id ? <StatusMessage kind="warning">Link this scenario set to a decision before testing options.</StatusMessage> : null}
            <div className="wind-tunnel-table-wrap">
              <table className="wind-tunnel-table">
                <thead><tr><th>Option</th>{data.scenarios.map((scenario) => <th key={scenario.id}>{scenario.code}<small>{scenario.title}</small></th>)}</tr></thead>
                <tbody>{data.decision_options.map((option) => <tr key={option.id}><th>{option.title}</th>{data.scenarios.map((scenario) => { const assessment = scenario.wind_tunnel_assessments.find((item) => item.option_id === option.id); return <td key={scenario.id}>{assessment ? <div className={`wind-verdict wind-verdict--${assessment.verdict}`}><strong>{assessment.verdict_label}</strong><span>{assessment.robustness_score}/5</span><small>{assessment.rationale}</small></div> : <span className="muted-cell">Not tested</span>}</td>; })}</tr>)}</tbody>
              </table>
            </div>
          </section>
          <aside className="side-panel foresight-create-panel">
            <p className="eyebrow">Strategy stress test</p><h2>Assess an option</h2>
            <form onSubmit={(event) => { event.preventDefault(); assessOption.mutate(); }}>
              <label htmlFor="assessment-scenario">Scenario</label><select id="assessment-scenario" required value={assessmentForm.scenario_id} onChange={(event) => setAssessmentForm({ ...assessmentForm, scenario_id: event.target.value })}><option value="">Choose world</option>{data.scenarios.map((item) => <option key={item.id} value={item.id}>{item.code} — {item.title}</option>)}</select>
              <label htmlFor="assessment-option">Decision option</label><select id="assessment-option" required value={assessmentForm.option_id} onChange={(event) => setAssessmentForm({ ...assessmentForm, option_id: event.target.value })}><option value="">Choose option</option>{data.decision_options.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
              <label htmlFor="assessment-verdict">Verdict</label><select id="assessment-verdict" value={assessmentForm.verdict} onChange={(event) => setAssessmentForm({ ...assessmentForm, verdict: event.target.value })}><option value="robust">Robust</option><option value="adaptable">Adaptable with conditions</option><option value="vulnerable">Vulnerable</option><option value="infeasible">Infeasible</option><option value="uncertain">Uncertain</option></select>
              {(["desirability", "feasibility", "resilience"] as const).map((field) => <div className="score-input-row" key={field}><label htmlFor={`assessment-${field}`}>{field}</label><input id={`assessment-${field}`} min={1} max={5} type="range" value={assessmentForm[field]} onChange={(event) => setAssessmentForm({ ...assessmentForm, [field]: Number(event.target.value) })} /><strong>{assessmentForm[field]}/5</strong></div>)}
              <label htmlFor="assessment-rationale">Rationale</label><textarea id="assessment-rationale" required rows={5} value={assessmentForm.rationale} onChange={(event) => setAssessmentForm({ ...assessmentForm, rationale: event.target.value })} />
              <label htmlFor="assessment-conditions">Conditions for success</label><textarea id="assessment-conditions" rows={3} value={assessmentForm.conditions_for_success} onChange={(event) => setAssessmentForm({ ...assessmentForm, conditions_for_success: event.target.value })} />
              <label htmlFor="assessment-vulnerabilities">Vulnerabilities</label><textarea id="assessment-vulnerabilities" rows={3} value={assessmentForm.vulnerabilities} onChange={(event) => setAssessmentForm({ ...assessmentForm, vulnerabilities: event.target.value })} />
              <label htmlFor="assessment-mitigations">Mitigations</label><textarea id="assessment-mitigations" rows={3} value={assessmentForm.mitigations} onChange={(event) => setAssessmentForm({ ...assessmentForm, mitigations: event.target.value })} />
              <button className="primary-button" disabled={assessOption.isPending || !data.linked_decision_id || !data.decision_options.length || !data.scenarios.length} type="submit">Save assessment</button>
            </form>
          </aside>
        </div>
      ) : null}

      {tab === "signposts" ? (
        <div className="scenario-tab-layout">
          <section className="page-primary">
            <div className="signpost-grid">
              {data.signposts.map((signpost) => <article className="signpost-card" key={signpost.id}><div className="section-heading"><div><p className="eyebrow">{signpost.review_cadence_label}</p><h3>{signpost.title}</h3></div><span className={`status-badge status-badge--${signpost.status}`}>{signpost.status_label}</span></div><p>{signpost.description}</p><dl><div><dt>Indicator</dt><dd>{signpost.indicator}</dd></div><div><dt>Trigger</dt><dd>{signpost.direction_label}: {signpost.threshold}</dd></div><div><dt>Owner</dt><dd>{personName(signpost.owner)}</dd></div></dl><div className="scenario-state-list">{signpost.scenario_links.map((link) => <span key={link.id}>{link.relationship_label}: {link.scenario_title}</span>)}</div>{signpost.latest_observation ? <div className={`latest-observation latest-observation--${signpost.latest_observation.assessment}`}><strong>{signpost.latest_observation.assessment_label}</strong><span>{signpost.latest_observation.observed_on}</span><p>{signpost.latest_observation.value}</p></div> : <p className="muted-cell">No observations yet.</p>}{(signpost.assumption_links.length || signpost.risk_links.length) ? <div className="scenario-state-list" aria-label="Watchlist links">{signpost.assumption_links.map((link) => <span key={link.id} title={link.rationale}>Assumption: {link.assumption_statement}</span>)}{signpost.risk_links.map((link) => <span key={link.id} title={link.rationale}>Risk: {link.risk_title}</span>)}</div> : null}<details><summary>{signpost.observations.length} observations</summary>{signpost.observations.map((observation) => <blockquote key={observation.id}><strong>{observation.observed_on} · {observation.assessment_label}</strong><p>{observation.value}</p><small>{observation.evidence}</small></blockquote>)}</details></article>)}
              {!data.signposts.length ? <div className="empty-state"><h3>No adaptive signposts</h3><p>Define observable indicators that could support, challenge, or contextualise the scenario worlds.</p></div> : null}
            </div>
          </section>
          <aside className="scenario-action-stack">
            <section className="side-panel foresight-create-panel">
              <p className="eyebrow">Early warning</p><h2>Add signpost</h2>
              <form onSubmit={(event) => { event.preventDefault(); createSignpost.mutate(); }}>
                <label htmlFor="signpost-title">Title</label><input id="signpost-title" required value={signpostForm.title} onChange={(event) => setSignpostForm({ ...signpostForm, title: event.target.value })} />
                <label htmlFor="signpost-description">Description</label><textarea id="signpost-description" required rows={4} value={signpostForm.description} onChange={(event) => setSignpostForm({ ...signpostForm, description: event.target.value })} />
                <label htmlFor="signpost-indicator">Observable indicator</label><input id="signpost-indicator" required value={signpostForm.indicator} onChange={(event) => setSignpostForm({ ...signpostForm, indicator: event.target.value })} />
                <label htmlFor="signpost-threshold">Threshold or trigger</label><input id="signpost-threshold" required value={signpostForm.threshold} onChange={(event) => setSignpostForm({ ...signpostForm, threshold: event.target.value })} />
                <div className="form-row"><div><label htmlFor="signpost-direction">Direction</label><select id="signpost-direction" value={signpostForm.direction} onChange={(event) => setSignpostForm({ ...signpostForm, direction: event.target.value })}><option value="above">Above</option><option value="below">Below</option><option value="rising">Rising</option><option value="falling">Falling</option><option value="change">Material change</option><option value="qualitative">Qualitative</option></select></div><div><label htmlFor="signpost-cadence">Review cadence</label><select id="signpost-cadence" value={signpostForm.review_cadence} onChange={(event) => setSignpostForm({ ...signpostForm, review_cadence: event.target.value })}><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="semiannual">Every six months</option><option value="annual">Annual</option><option value="event_driven">Event-driven</option></select></div></div>
                <label htmlFor="signpost-scenario">Initial scenario link</label><select id="signpost-scenario" value={signpostForm.scenario_id} onChange={(event) => setSignpostForm({ ...signpostForm, scenario_id: event.target.value })}><option value="">No initial link</option>{data.scenarios.map((item) => <option key={item.id} value={item.id}>{item.code} — {item.title}</option>)}</select>
                {signpostForm.scenario_id ? <><label htmlFor="signpost-relationship">Relationship</label><select id="signpost-relationship" value={signpostForm.relationship} onChange={(event) => setSignpostForm({ ...signpostForm, relationship: event.target.value })}><option value="supports">Supports</option><option value="contradicts">Contradicts</option><option value="contextual">Contextual</option></select><label htmlFor="signpost-rationale">Link rationale</label><textarea id="signpost-rationale" required rows={3} value={signpostForm.rationale} onChange={(event) => setSignpostForm({ ...signpostForm, rationale: event.target.value })} /></> : null}
                <label htmlFor="signpost-source-notes">Source notes</label><textarea id="signpost-source-notes" rows={3} value={signpostForm.source_notes} onChange={(event) => setSignpostForm({ ...signpostForm, source_notes: event.target.value })} />
                <button className="primary-button" disabled={createSignpost.isPending} type="submit">Create signpost</button>
              </form>
            </section>
            <section className="side-panel foresight-create-panel">
              <p className="eyebrow">Monitoring evidence</p><h2>Record observation</h2>
              <form onSubmit={(event) => { event.preventDefault(); observeSignpost.mutate(); }}>
                <label htmlFor="observation-signpost">Signpost</label><select id="observation-signpost" required value={observationForm.signpost_id} onChange={(event) => setObservationForm({ ...observationForm, signpost_id: event.target.value })}><option value="">Choose signpost</option>{data.signposts.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                <label htmlFor="observation-date">Observed on</label><input id="observation-date" required type="date" value={observationForm.observed_on} onChange={(event) => setObservationForm({ ...observationForm, observed_on: event.target.value })} />
                <label htmlFor="observation-value">Observed value or condition</label><input id="observation-value" required value={observationForm.value} onChange={(event) => setObservationForm({ ...observationForm, value: event.target.value })} />
                <label htmlFor="observation-assessment">Assessment</label><select id="observation-assessment" value={observationForm.assessment} onChange={(event) => setObservationForm({ ...observationForm, assessment: event.target.value })}><option value="no_change">No meaningful change</option><option value="weak">Weak movement</option><option value="moderate">Moderate movement</option><option value="strong">Strong movement</option><option value="contradictory">Contradictory evidence</option></select>
                <label htmlFor="observation-evidence">Evidence and interpretation</label><textarea id="observation-evidence" required rows={4} value={observationForm.evidence} onChange={(event) => setObservationForm({ ...observationForm, evidence: event.target.value })} />
                <label htmlFor="observation-source">Existing source</label><select id="observation-source" value={observationForm.source_id} onChange={(event) => setObservationForm({ ...observationForm, source_id: event.target.value })}><option value="">No source link</option>{(sources.data ?? []).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                <button className="secondary-button" disabled={observeSignpost.isPending || !data.signposts.length} type="submit">Record observation</button>
              </form>
            </section>
            <section className="side-panel foresight-create-panel">
              <p className="eyebrow">Adaptive strategy</p><h2>Add to watchlist</h2>
              {linkedDecisionId ? (
                <form onSubmit={(event) => { event.preventDefault(); linkWatchlist.mutate(); }}>
                  <label htmlFor="watchlist-signpost">Signpost</label><select id="watchlist-signpost" required value={watchlistForm.signpost_id} onChange={(event) => setWatchlistForm({ ...watchlistForm, signpost_id: event.target.value })}><option value="">Choose signpost</option>{data.signposts.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                  <label htmlFor="watchlist-kind">Watch</label><select id="watchlist-kind" value={watchlistForm.kind} onChange={(event) => setWatchlistForm({ ...watchlistForm, kind: event.target.value as "assumption" | "risk", target_id: "" })}><option value="assumption">An assumption</option><option value="risk">A risk</option></select>
                  {watchlistForm.kind === "assumption" ? (
                    <><label htmlFor="watchlist-assumption">Assumption</label><select id="watchlist-assumption" required value={watchlistForm.target_id} onChange={(event) => setWatchlistForm({ ...watchlistForm, target_id: event.target.value })}><option value="">Choose assumption</option>{(linkedAssumptions.data ?? []).map((item) => <option key={item.id} value={item.id}>{item.statement}</option>)}</select></>
                  ) : (
                    <><label htmlFor="watchlist-risk">Risk</label><select id="watchlist-risk" required value={watchlistForm.target_id} onChange={(event) => setWatchlistForm({ ...watchlistForm, target_id: event.target.value })}><option value="">Choose risk</option>{(linkedRisks.data ?? []).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></>
                  )}
                  <label htmlFor="watchlist-rationale">Why this signpost should trigger a re-review</label><textarea id="watchlist-rationale" required rows={3} value={watchlistForm.rationale} onChange={(event) => setWatchlistForm({ ...watchlistForm, rationale: event.target.value })} />
                  <button className="secondary-button" disabled={linkWatchlist.isPending || !data.signposts.length} type="submit">Add to watchlist</button>
                </form>
              ) : (
                <p className="muted">Link this scenario set to a decision to build an assumption and signpost watchlist.</p>
              )}
            </section>
          </aside>
        </div>
      ) : null}
    </div>
  );
}
