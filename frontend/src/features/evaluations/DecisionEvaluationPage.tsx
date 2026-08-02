import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { EvaluationExercise, EvaluationRound } from "../../lib/types";
import { getDecision } from "../decisions/api";
import { listOptions } from "../reasoning/api";
import {
  addEvaluationCriterion,
  createEvaluation,
  createEvaluationRound,
  createMinorityReport,
  getEvaluation,
  listEvaluations,
  saveEvaluationSubmission,
  transitionEvaluationRound,
} from "./api";

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "The evaluation action failed.";
}

function personName(person: { first_name: string; last_name: string; email: string }): string {
  return `${person.first_name} ${person.last_name}`.trim() || person.email;
}

export function DecisionEvaluationPage() {
  const { decisionId = "" } = useParams<{ decisionId: string }>();
  const client = useQueryClient();
  const [selectedId, setSelectedId] = useState("");
  const [title, setTitle] = useState("");
  const [purpose, setPurpose] = useState("");
  const [method, setMethod] = useState<EvaluationExercise["method"]>("scorecard");
  const [anonymity, setAnonymity] = useState<EvaluationExercise["anonymity"]>("peer_anonymous");
  const [quorum, setQuorum] = useState(1);

  const decision = useQuery({ queryKey: ["decisions", decisionId], queryFn: () => getDecision(decisionId), enabled: Boolean(decisionId) });
  const options = useQuery({ queryKey: ["decisions", decisionId, "options"], queryFn: () => listOptions(decisionId), enabled: Boolean(decisionId) });
  const exercises = useQuery({ queryKey: ["decisions", decisionId, "evaluations"], queryFn: () => listEvaluations(decisionId), enabled: Boolean(decisionId) });
  const exercise = useQuery({ queryKey: ["evaluations", selectedId], queryFn: () => getEvaluation(selectedId), enabled: Boolean(selectedId) });

  useEffect(() => {
    if (!selectedId) {
      const first = exercises.data?.at(0);
      if (first) setSelectedId(first.id);
    }
  }, [exercises.data, selectedId]);

  async function refresh(exerciseId?: string) {
    await client.invalidateQueries({ queryKey: ["decisions", decisionId, "evaluations"] });
    if (exerciseId ?? selectedId) await client.invalidateQueries({ queryKey: ["evaluations", exerciseId ?? selectedId] });
  }

  const create = useMutation({
    mutationFn: () => createEvaluation(decisionId, {
      title,
      purpose,
      method,
      anonymity,
      blind_results_until_close: true,
      quorum_count: quorum,
      approval_threshold: 60,
      objection_threshold: 20,
      owner_id: decision.data?.owner.id,
    }),
    onSuccess: async (item) => {
      setSelectedId(item.id);
      setTitle("");
      setPurpose("");
      await refresh(item.id);
    },
  });

  if (decision.isPending || options.isPending || exercises.isPending) return <p>Loading collective evaluation…</p>;
  if (decision.isError || options.isError || exercises.isError || !decision.data) return <StatusMessage kind="error">The decision evaluation workspace could not be loaded.</StatusMessage>;

  return (
    <div className="phase14-page">
      <Link className="back-link" to={`/decisions/${decisionId}`}>← Decision workspace</Link>
      <header className="page-header phase14-hero">
        <div>
          <p className="eyebrow">Collective evaluation</p>
          <h1>{decision.data.title}</h1>
          <p>Independent contribution, blind rounds, weighted criteria, explicit thresholds, and preserved dissent.</p>
        </div>
        <div className="phase14-principle"><strong>Human-governed</strong><span>Results inform authority; they do not automate the decision.</span></div>
      </header>

      {create.error ? <StatusMessage kind="error">{errorMessage(create.error)}</StatusMessage> : null}

      <div className="evaluation-layout">
        <aside className="evaluation-sidebar">
          <section className="panel-card">
            <p className="eyebrow">New exercise</p>
            <h2>Choose the evaluation logic</h2>
            <form onSubmit={(event) => { event.preventDefault(); create.mutate(); }} className="stack-form">
              <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={240} /></label>
              <label>Purpose<textarea value={purpose} onChange={(event) => setPurpose(event.target.value)} rows={3} /></label>
              <label>Method<select value={method} onChange={(event) => setMethod(event.target.value as EvaluationExercise["method"])}>
                <option value="scorecard">Multi-criteria scorecard</option>
                <option value="approval">Approval voting</option>
                <option value="consent">Consent and objections</option>
                <option value="delphi">Delphi rounds</option>
              </select></label>
              <label>Contribution identity<select value={anonymity} onChange={(event) => setAnonymity(event.target.value as EvaluationExercise["anonymity"])}>
                <option value="peer_anonymous">Anonymous to peers</option>
                <option value="attributed">Attributable</option>
              </select></label>
              <label>Minimum quorum<input type="number" min={1} value={quorum} onChange={(event) => setQuorum(Number(event.target.value))} /></label>
              <button className="button button--primary" disabled={create.isPending || !title.trim()}>{create.isPending ? "Creating…" : "Create exercise"}</button>
            </form>
          </section>

          <section className="panel-card">
            <p className="eyebrow">Exercises</p>
            <div className="evaluation-list">
              {exercises.data?.map((item) => (
                <button type="button" key={item.id} className={selectedId === item.id ? "evaluation-list__item is-active" : "evaluation-list__item"} onClick={() => setSelectedId(item.id)}>
                  <span><strong>{item.title}</strong><small>{item.method_label}</small></span>
                  <span className={`status-badge status-badge--${item.status}`}>{item.status_label}</span>
                </button>
              ))}
              {!exercises.data?.length ? <p className="muted">No evaluation exercise has been created.</p> : null}
            </div>
          </section>
        </aside>

        <main className="evaluation-main">
          {selectedId && exercise.isPending ? <p>Loading exercise…</p> : null}
          {exercise.isError ? <StatusMessage kind="error">The selected exercise could not be loaded.</StatusMessage> : null}
          {exercise.data ? (
            <EvaluationWorkspace
              exercise={exercise.data}
              options={options.data?.filter((item) => item.status === "active") ?? []}
              onRefresh={() => refresh(exercise.data.id)}
            />
          ) : !selectedId ? (
            <section className="empty-state panel-card"><h2>Create the first evaluation</h2><p>Start with a method that matches the decision: score alternatives, test approval, seek consent, or run iterative Delphi rounds.</p></section>
          ) : null}
        </main>
      </div>
    </div>
  );
}

function EvaluationWorkspace({ exercise, options, onRefresh }: { exercise: EvaluationExercise; options: Array<{ id: string; title: string }>; onRefresh: () => Promise<void> }) {
  const [criterionTitle, setCriterionTitle] = useState("");
  const [criterionDescription, setCriterionDescription] = useState("");
  const [criterionWeight, setCriterionWeight] = useState("1");
  const [roundTitle, setRoundTitle] = useState("");
  const [minorityTitle, setMinorityTitle] = useState("");
  const [minorityAnalysis, setMinorityAnalysis] = useState("");
  const [minorityRecommendation, setMinorityRecommendation] = useState("");

  const addCriterion = useMutation({ mutationFn: () => addEvaluationCriterion(exercise.id, { title: criterionTitle, description: criterionDescription, weight: criterionWeight, scale_min: 1, scale_max: 5, higher_is_better: true, order: exercise.criteria.length }), onSuccess: async () => { setCriterionTitle(""); setCriterionDescription(""); await onRefresh(); } });
  const addRound = useMutation({ mutationFn: () => createEvaluationRound(exercise.id, roundTitle), onSuccess: async () => { setRoundTitle(""); await onRefresh(); } });
  const report = useMutation({ mutationFn: () => createMinorityReport(exercise.id, { round_id: exercise.rounds.at(-1)?.id ?? null, title: minorityTitle, analysis: minorityAnalysis, recommendation: minorityRecommendation }), onSuccess: async () => { setMinorityTitle(""); setMinorityAnalysis(""); setMinorityRecommendation(""); await onRefresh(); } });

  return (
    <div className="evaluation-workspace">
      <section className="panel-card evaluation-summary">
        <div>
          <div className="heading-badges"><span className="status-badge">{exercise.status_label}</span><span className="role-badge">{exercise.method_label}</span><span className="role-badge">{exercise.anonymity === "peer_anonymous" ? "Peer anonymous" : "Attributable"}</span></div>
          <h2>{exercise.title}</h2>
          <p>{exercise.purpose || "No purpose has been recorded."}</p>
        </div>
        <div className="evaluation-metrics">
          <div><strong>{exercise.quorum_count}</strong><span>quorum</span></div>
          <div><strong>{exercise.criteria.length}</strong><span>criteria</span></div>
          <div><strong>{exercise.rounds.length}</strong><span>rounds</span></div>
          <div><strong>{exercise.minority_reports.length}</strong><span>minority reports</span></div>
        </div>
      </section>

      {addCriterion.error || addRound.error || report.error ? <StatusMessage kind="error">{errorMessage(addCriterion.error ?? addRound.error ?? report.error)}</StatusMessage> : null}

      {exercise.can_manage && exercise.status === "draft" && ["scorecard", "delphi"].includes(exercise.method) ? (
        <section className="panel-card">
          <div className="section-heading"><div><p className="eyebrow">Decision criteria</p><h2>Make judgement dimensions explicit</h2></div><span className="muted">Weights are normalised automatically.</span></div>
          <div className="criteria-strip">
            {exercise.criteria.map((criterion) => <article key={criterion.id}><strong>{criterion.title}</strong><span>Weight {criterion.weight}</span><p>{criterion.description || "No description"}</p></article>)}
          </div>
          <form className="inline-form phase14-inline-form" onSubmit={(event) => { event.preventDefault(); addCriterion.mutate(); }}>
            <label>Criterion<input value={criterionTitle} onChange={(event) => setCriterionTitle(event.target.value)} required /></label>
            <label>Description<input value={criterionDescription} onChange={(event) => setCriterionDescription(event.target.value)} /></label>
            <label>Weight<input type="number" min="0.01" step="0.01" value={criterionWeight} onChange={(event) => setCriterionWeight(event.target.value)} required /></label>
            <button className="button button--secondary" disabled={addCriterion.isPending}>Add criterion</button>
          </form>
        </section>
      ) : null}

      <section className="panel-card">
        <div className="section-heading"><div><p className="eyebrow">Independent rounds</p><h2>Collect before revealing</h2></div></div>
        {exercise.can_manage && (exercise.method === "delphi" || exercise.rounds.length === 0) ? (
          <form className="inline-form phase14-inline-form" onSubmit={(event) => { event.preventDefault(); addRound.mutate(); }}>
            <label>Round title<input value={roundTitle} onChange={(event) => setRoundTitle(event.target.value)} placeholder={`Round ${exercise.rounds.length + 1}`} /></label>
            <button className="button button--secondary" disabled={addRound.isPending}>{addRound.isPending ? "Creating…" : "Create round"}</button>
          </form>
        ) : null}
        <div className="round-stack">
          {exercise.rounds.map((round) => <RoundPanel key={round.id} round={round} exercise={exercise} options={options} onRefresh={onRefresh} />)}
          {!exercise.rounds.length ? <p className="muted">Create a round after defining the exercise and any required criteria.</p> : null}
        </div>
      </section>

      <section className="panel-card">
        <div className="section-heading"><div><p className="eyebrow">Preserved disagreement</p><h2>Minority reports</h2></div></div>
        <div className="minority-grid">
          {exercise.minority_reports.map((item) => <article key={item.id}><strong>{item.title}</strong><small>{personName(item.author)}</small><p>{item.analysis}</p>{item.recommendation ? <blockquote>{item.recommendation}</blockquote> : null}</article>)}
        </div>
        {exercise.can_submit ? (
          <form className="stack-form minority-form" onSubmit={(event) => { event.preventDefault(); report.mutate(); }}>
            <label>Report title<input value={minorityTitle} onChange={(event) => setMinorityTitle(event.target.value)} required /></label>
            <label>Analysis<textarea rows={4} value={minorityAnalysis} onChange={(event) => setMinorityAnalysis(event.target.value)} required /></label>
            <label>Alternative recommendation<textarea rows={2} value={minorityRecommendation} onChange={(event) => setMinorityRecommendation(event.target.value)} /></label>
            <button className="button button--secondary" disabled={report.isPending || !minorityTitle.trim() || !minorityAnalysis.trim()}>Publish minority report</button>
          </form>
        ) : null}
      </section>
    </div>
  );
}

function RoundPanel({ round, exercise, options, onRefresh }: { round: EvaluationRound; exercise: EvaluationExercise; options: Array<{ id: string; title: string }>; onRefresh: () => Promise<void> }) {
  const [scores, setScores] = useState<Record<string, string>>({});
  const [votes, setVotes] = useState<Record<string, string>>({});
  const [confidence, setConfidence] = useState(3);
  const [rationale, setRationale] = useState("");
  const [feedback, setFeedback] = useState("");

  const transition = useMutation({ mutationFn: (status: "open" | "closed") => transitionEvaluationRound(round.id, { status, feedback_summary: feedback }), onSuccess: onRefresh });
  const submit = useMutation({
    mutationFn: () => {
      const scorecard = ["scorecard", "delphi"].includes(exercise.method);
      const responses = scorecard
        ? options.flatMap((option) => exercise.criteria.flatMap((criterion) => {
          const value = scores[`${option.id}:${criterion.id}`];
          return value ? [{ option_id: option.id, criterion_id: criterion.id, score: Number(value), rationale: "" }] : [];
        }))
        : options.flatMap((option) => votes[option.id] ? [{ option_id: option.id, criterion_id: null, vote: votes[option.id], rationale: "" }] : []);
      return saveEvaluationSubmission(round.id, { confidence, overall_rationale: rationale, responses, submit: true });
    },
    onSuccess: onRefresh,
  });

  const resultByOption = useMemo(() => new Map(round.result_summary.options.map((item) => [item.option_id, item])), [round.result_summary.options]);

  function submitForm(event: FormEvent) { event.preventDefault(); submit.mutate(); }

  return (
    <article className="round-card">
      <header>
        <div><span className="round-number">Round {round.number}</span><h3>{round.title || `Evaluation round ${round.number}`}</h3></div>
        <span className={`status-badge status-badge--${round.status}`}>{round.status}</span>
      </header>
      {round.feedback_summary ? <div className="delphi-feedback"><strong>Facilitator feedback</strong><p>{round.feedback_summary}</p></div> : null}
      {transition.error || submit.error ? <StatusMessage kind="error">{errorMessage(transition.error ?? submit.error)}</StatusMessage> : null}

      {exercise.can_manage && round.status === "draft" ? <button className="button button--primary" type="button" disabled={transition.isPending} onClick={() => transition.mutate("open")}>Open blind contribution</button> : null}

      {round.status === "open" && exercise.can_submit ? (
        <form className="evaluation-ballot" onSubmit={submitForm}>
          <div className="blind-notice"><strong>Independent contribution</strong><span>{exercise.blind_results_until_close ? "Aggregate results stay hidden until the round closes." : "Live aggregates are visible."}</span></div>
          {["scorecard", "delphi"].includes(exercise.method) ? (
            <div className="score-matrix table-wrap"><table><thead><tr><th>Option</th>{exercise.criteria.map((criterion) => <th key={criterion.id}>{criterion.title}<small>{criterion.scale_min}–{criterion.scale_max}</small></th>)}</tr></thead><tbody>{options.map((option) => <tr key={option.id}><th>{option.title}</th>{exercise.criteria.map((criterion) => <td key={criterion.id}><input aria-label={`${option.title}: ${criterion.title}`} type="number" min={criterion.scale_min} max={criterion.scale_max} step="0.1" value={scores[`${option.id}:${criterion.id}`] ?? ""} onChange={(event) => setScores((current) => ({ ...current, [`${option.id}:${criterion.id}`]: event.target.value }))} /></td>)}</tr>)}</tbody></table></div>
          ) : (
            <div className="ballot-options">{options.map((option) => <label key={option.id}><strong>{option.title}</strong><select value={votes[option.id] ?? ""} onChange={(event) => setVotes((current) => ({ ...current, [option.id]: event.target.value }))}><option value="">Not answered</option>{exercise.method === "approval" ? <><option value="approve">Approve</option><option value="abstain">Abstain</option></> : <><option value="consent">Consent</option><option value="concern">Concern</option><option value="object">Reasoned objection</option><option value="abstain">Abstain</option></>}</select></label>)}</div>
          )}
          <div className="evaluation-submission-meta"><label>Confidence: {confidence}/5<input type="range" min={1} max={5} value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} /></label><label>Overall rationale<textarea rows={3} value={rationale} onChange={(event) => setRationale(event.target.value)} /></label></div>
          <button className="button button--primary" disabled={submit.isPending}>{submit.isPending ? "Submitting…" : "Submit independent judgement"}</button>
        </form>
      ) : null}

      {exercise.can_manage && round.status === "open" ? <div className="close-round"><label>Feedback for a possible next Delphi round<textarea rows={3} value={feedback} onChange={(event) => setFeedback(event.target.value)} /></label><button className="button button--secondary" type="button" disabled={transition.isPending} onClick={() => transition.mutate("closed")}>Close and reveal results</button></div> : null}

      <div className="round-results">
        <div className="result-summary"><span>{round.result_summary.submission_count} submitted</span><span>{round.result_summary.eligible_count} eligible</span><span className={round.result_summary.quorum_met ? "result-ok" : "result-warning"}>{round.result_summary.quorum_met ? "Quorum met" : `Needs ${round.result_summary.quorum_count}`}</span></div>
        {round.result_summary.hidden ? <div className="sealed-results"><strong>Results sealed</strong><p>Blindness protects independent judgement and reduces anchoring while this round remains open.</p></div> : (
          <div className="result-ranking">{options.map((option, index) => { const result = resultByOption.get(option.id); return result ? <article key={option.id}><span className="rank-number">{index + 1}</span><div><strong>{result.title}</strong>{result.weighted_score != null ? <p>{result.weighted_score.toFixed(1)} weighted score · confidence {result.confidence ?? "—"}</p> : <p>{result.approval_rate ?? 0}% approval · {result.objection_rate ?? 0}% objections</p>}</div>{result.passes_threshold != null ? <span className={result.passes_threshold ? "role-badge" : "status-badge"}>{result.passes_threshold ? "Passes" : "Below threshold"}</span> : null}</article> : null; })}</div>
        )}
      </div>
    </article>
  );
}
