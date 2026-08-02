import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router-dom";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getDecision } from "../decisions/api";
import { listOptions } from "../reasoning/api";
import {
  finaliseDecision,
  getFinalisation,
  listCurrentPositions,
  listPositionHistory,
  submitPosition,
} from "./api";

const positionSchema = z
  .object({
    recommendation: z.enum([
      "support",
      "support_with_conditions",
      "do_not_support_any",
      "abstain",
    ]),
    preferred_option_id: z.string().optional(),
    rationale: z.string().trim().min(1, "Explain the reasoning behind your position."),
    conditions: z.string().trim().max(8000),
    confidence: z.enum(["low", "medium", "high"]),
  })
  .superRefine((value, context) => {
    const supportsOption = ["support", "support_with_conditions"].includes(
      value.recommendation,
    );
    if (supportsOption && !value.preferred_option_id) {
      context.addIssue({
        code: "custom",
        path: ["preferred_option_id"],
        message: "Select the option you support.",
      });
    }
    if (!supportsOption && value.preferred_option_id) {
      context.addIssue({
        code: "custom",
        path: ["preferred_option_id"],
        message: "Do not select an option when abstaining or rejecting all options.",
      });
    }
    if (
      value.recommendation === "support_with_conditions" &&
      !value.conditions
    ) {
      context.addIssue({
        code: "custom",
        path: ["conditions"],
        message: "Record the conditions attached to your support.",
      });
    }
  });

const finalisationSchema = z.object({
  selected_option_id: z.string().min(1, "Select the final option."),
  rationale: z.string().trim().min(1, "Record why this option was selected."),
  conditions: z.string().trim().max(8000),
  dissent_summary: z.string().trim().max(12000),
  positions_reviewed: z.boolean().refine((value) => value, {
    message: "Confirm that the current stakeholder positions were reviewed.",
  }),
});

type PositionInput = z.infer<typeof positionSchema>;
type FinalisationInput = z.infer<typeof finalisationSchema>;

function formatPerson(firstName: string, lastName: string, email: string): string {
  return `${firstName} ${lastName}`.trim() || email;
}

export function DecisionGovernancePage() {
  const { decisionId: routeDecisionId } = useParams<{ decisionId: string }>();
  const decisionId = routeDecisionId ?? "";
  const queryClient = useQueryClient();
  const decision = useQuery({
    queryKey: ["decisions", decisionId],
    queryFn: () => getDecision(decisionId),
    enabled: Boolean(decisionId),
  });
  const options = useQuery({
    queryKey: ["decisions", decisionId, "options"],
    queryFn: () => listOptions(decisionId),
    enabled: Boolean(decisionId),
  });
  const positions = useQuery({
    queryKey: ["decisions", decisionId, "positions"],
    queryFn: () => listCurrentPositions(decisionId),
    enabled: Boolean(decisionId),
  });
  const history = useQuery({
    queryKey: ["decisions", decisionId, "position-history"],
    queryFn: () => listPositionHistory(decisionId),
    enabled: Boolean(decisionId),
  });
  const finalisation = useQuery({
    queryKey: ["decisions", decisionId, "finalisation"],
    queryFn: () => getFinalisation(decisionId),
    enabled: Boolean(decisionId),
  });

  const positionForm = useForm<PositionInput>({
    resolver: zodResolver(positionSchema),
    defaultValues: {
      recommendation: "support",
      preferred_option_id: "",
      rationale: "",
      conditions: "",
      confidence: "medium",
    },
  });
  const finalisationForm = useForm<FinalisationInput>({
    resolver: zodResolver(finalisationSchema),
    defaultValues: {
      selected_option_id: "",
      rationale: "",
      conditions: "",
      dissent_summary: "",
      positions_reviewed: false,
    },
  });

  const refreshGovernance = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] }),
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "positions"] }),
      queryClient.invalidateQueries({
        queryKey: ["decisions", decisionId, "position-history"],
      }),
      queryClient.invalidateQueries({
        queryKey: ["decisions", decisionId, "finalisation"],
      }),
      queryClient.invalidateQueries({
        queryKey: ["decisions", decisionId, "transitions"],
      }),
    ]);
  };

  const submit = useMutation({
    mutationFn: (input: PositionInput) =>
      submitPosition(decisionId, {
        ...input,
        preferred_option_id: input.preferred_option_id || null,
      }),
    onSuccess: async () => {
      positionForm.reset({
        recommendation: "support",
        preferred_option_id: "",
        rationale: "",
        conditions: "",
        confidence: "medium",
      });
      await refreshGovernance();
    },
  });
  const finalise = useMutation({
    mutationFn: (input: FinalisationInput) => {
      if (!decision.data) throw new Error("Decision is unavailable.");
      return finaliseDecision(decisionId, {
        ...input,
        expected_status: decision.data.status,
      });
    },
    onSuccess: refreshGovernance,
  });

  if (decision.isPending) return <p>Loading decision governance…</p>;
  if (decision.isError || !decision.data) {
    return <StatusMessage kind="error">The decision could not be loaded.</StatusMessage>;
  }

  const current = decision.data;
  const activeOptions = options.data?.filter((option) => option.status === "active") ?? [];
  const existingFinalisation = finalisation.data?.finalisation;

  return (
    <div>
      <Link className="back-link" to={`/decisions/${decisionId}`}>
        ← Decision workspace
      </Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Human governance</p>
          <h1>Positions and final decision</h1>
          <p className="decision-question">{current.title}</p>
        </div>
        <span className="status-badge">{current.status_label}</span>
      </div>

      <section className="readiness-panel" aria-labelledby="position-coverage-title">
        <div>
          <p className="eyebrow">Authority coverage</p>
          <h2 id="position-coverage-title">Required positions</h2>
          <p className="muted">
            Each active decision owner and decision maker must state a current position before finalisation. Other participant positions remain visible and attributable.
          </p>
        </div>
        <div className="readiness-metrics">
          <span><strong>{current.position_summary.current_positions}</strong> current positions</span>
          <span><strong>{current.position_summary.submitted_authorities}</strong> of {current.position_summary.required_authorities} authorities</span>
        </div>
        {current.position_summary.missing_authorities.length ? (
          <ul className="blocker-list">
            {current.position_summary.missing_authorities.map((item) => (
              <li key={item.participant_id}>{item.email} ({item.role_label}) must submit a position.</li>
            ))}
          </ul>
        ) : (
          <StatusMessage kind="success">All active decision authorities have current positions.</StatusMessage>
        )}
      </section>

      <div className="decision-layout governance-layout">
        <section className="page-primary" aria-labelledby="current-positions-title">
          <p className="eyebrow">Current recommendations</p>
          <h2 id="current-positions-title">Stakeholder positions</h2>
          {positions.isPending ? <p>Loading positions…</p> : null}
          {positions.isError ? <StatusMessage kind="error">Positions could not be loaded.</StatusMessage> : null}
          {positions.data?.length === 0 ? <p className="muted">No position has been submitted.</p> : null}
          <div className="position-list">
            {positions.data?.map((position) => (
              <article className="position-card" key={position.id}>
                <div className="section-heading">
                  <div>
                    <h3>{formatPerson(position.participant_user.first_name, position.participant_user.last_name, position.participant_user.email)}</h3>
                    <span className="table-secondary">{position.participant_role_label} · version {position.version}</span>
                  </div>
                  <span className="role-badge">{position.recommendation_label}</span>
                </div>
                {position.preferred_option_title ? <p><strong>Preferred option:</strong> {position.preferred_option_title}</p> : null}
                <p>{position.rationale}</p>
                {position.conditions ? <p><strong>Conditions:</strong> {position.conditions}</p> : null}
                <span className="table-secondary">{position.confidence_label} confidence · {new Date(position.created_at).toLocaleString("en-GB")}</span>
              </article>
            ))}
          </div>
        </section>

        <aside className="side-panel" aria-labelledby="submit-position-title">
          <h2 id="submit-position-title">Submit or revise your position</h2>
          <p className="muted">A revision creates a new immutable version; it does not overwrite your earlier reasoning.</p>
          {!current.can_submit_position ? (
            <StatusMessage kind="error">Your participant role or the current lifecycle state does not permit a position submission.</StatusMessage>
          ) : null}
          {submit.error ? (
            <StatusMessage kind="error">{submit.error instanceof ApiError ? submit.error.message : "The position could not be submitted."}</StatusMessage>
          ) : null}
          {submit.isSuccess ? <StatusMessage kind="success">Your position was recorded.</StatusMessage> : null}
          <form onSubmit={positionForm.handleSubmit((values) => submit.mutate(values))} noValidate>
            <label htmlFor="position-recommendation">Recommendation</label>
            <select id="position-recommendation" {...positionForm.register("recommendation")} disabled={!current.can_submit_position}>
              <option value="support">Support an option</option>
              <option value="support_with_conditions">Support with conditions</option>
              <option value="do_not_support_any">Do not support any option</option>
              <option value="abstain">Abstain</option>
            </select>

            <label htmlFor="position-option">Preferred option</label>
            <select id="position-option" {...positionForm.register("preferred_option_id")} disabled={!current.can_submit_position}>
              <option value="">No option selected</option>
              {activeOptions.map((option) => <option key={option.id} value={option.id}>{option.title}</option>)}
            </select>
            <FieldError message={positionForm.formState.errors.preferred_option_id?.message} />

            <label htmlFor="position-rationale">Rationale</label>
            <textarea id="position-rationale" rows={5} {...positionForm.register("rationale")} disabled={!current.can_submit_position} />
            <FieldError message={positionForm.formState.errors.rationale?.message} />

            <label htmlFor="position-conditions">Conditions</label>
            <textarea id="position-conditions" rows={3} {...positionForm.register("conditions")} disabled={!current.can_submit_position} />
            <FieldError message={positionForm.formState.errors.conditions?.message} />

            <label htmlFor="position-confidence">Confidence</label>
            <select id="position-confidence" {...positionForm.register("confidence")} disabled={!current.can_submit_position}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>

            <button className="button button--primary button--full" type="submit" disabled={!current.can_submit_position || submit.isPending}>
              {submit.isPending ? "Submitting…" : "Record position"}
            </button>
          </form>
        </aside>
      </div>

      <section className="page-primary finalisation-panel" aria-labelledby="finalisation-title">
        <p className="eyebrow">Human decision authority</p>
        <h2 id="finalisation-title">Final decision record</h2>
        {existingFinalisation ? (
          <div className="finalisation-record">
            <StatusMessage kind="success">This decision was finalised by a human decision authority.</StatusMessage>
            <p><strong>Selected option:</strong> {existingFinalisation.selected_option_title}</p>
            <p><strong>Decided by:</strong> {existingFinalisation.decided_by.email}</p>
            <p><strong>Rationale:</strong> {existingFinalisation.rationale}</p>
            {existingFinalisation.conditions ? <p><strong>Conditions:</strong> {existingFinalisation.conditions}</p> : null}
            {existingFinalisation.dissent_summary ? <p><strong>Dissent considered:</strong> {existingFinalisation.dissent_summary}</p> : null}
            <span className="table-secondary">{new Date(existingFinalisation.decided_at).toLocaleString("en-GB")}</span>
          </div>
        ) : current.status === "ready_for_decision" ? (
          current.can_finalise ? (
            <form className="finalisation-form" onSubmit={finalisationForm.handleSubmit((values) => finalise.mutate(values))} noValidate>
              {finalise.error ? <StatusMessage kind="error">{finalise.error instanceof ApiError ? finalise.error.message : "The decision could not be finalised."}</StatusMessage> : null}
              <label htmlFor="final-option">Selected option</label>
              <select id="final-option" {...finalisationForm.register("selected_option_id")}>
                <option value="">Select an option</option>
                {activeOptions.map((option) => <option key={option.id} value={option.id}>{option.title}</option>)}
              </select>
              <FieldError message={finalisationForm.formState.errors.selected_option_id?.message} />

              <label htmlFor="final-rationale">Final rationale</label>
              <textarea id="final-rationale" rows={6} {...finalisationForm.register("rationale")} />
              <FieldError message={finalisationForm.formState.errors.rationale?.message} />

              <label htmlFor="final-conditions">Conditions or constraints</label>
              <textarea id="final-conditions" rows={4} {...finalisationForm.register("conditions")} />

              <label htmlFor="dissent-summary">How dissent and alternatives were considered</label>
              <textarea id="dissent-summary" rows={5} {...finalisationForm.register("dissent_summary")} />

              <label className="checkbox-row" htmlFor="positions-reviewed">
                <input id="positions-reviewed" type="checkbox" {...finalisationForm.register("positions_reviewed")} />
                <span>I reviewed the current stakeholder positions and understand that the final decision remains a human judgement.</span>
              </label>
              <FieldError message={finalisationForm.formState.errors.positions_reviewed?.message} />

              <button className="button button--primary" type="submit" disabled={finalise.isPending || !current.position_summary.ready_to_finalise}>
                {finalise.isPending ? "Finalising…" : "Finalise decision"}
              </button>
            </form>
          ) : (
            <p className="muted">Only the decision owner, a designated decision maker, or an organisation manager may finalise this decision.</p>
          )
        ) : (
          <p className="muted">The finalisation form becomes available when the decision reaches Ready for Decision.</p>
        )}
      </section>

      <section className="page-primary" aria-labelledby="position-history-title">
        <p className="eyebrow">Preserved reasoning</p>
        <h2 id="position-history-title">Position history</h2>
        <p className="muted">Earlier versions remain visible for organisational learning and auditability.</p>
        {history.data?.length ? (
          <ol className="history-list">
            {history.data.map((item) => (
              <li key={item.id}>
                <strong>{item.participant_user.email} · version {item.version} · {item.recommendation_label}</strong>
                <span className="table-secondary">{new Date(item.created_at).toLocaleString("en-GB")}</span>
              </li>
            ))}
          </ol>
        ) : <p className="muted">No position history yet.</p>}
      </section>
    </div>
  );
}
