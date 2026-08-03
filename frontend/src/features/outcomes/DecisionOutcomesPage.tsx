import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { LessonCategory, OutcomeAssessment } from "../../lib/types";
import { getDecision } from "../decisions/api";
import { listMemberships } from "../organisations/api";
import {
  archiveDecision,
  changeImplementationOwner,
  completeOutcomeReview,
  createLesson,
  getDecisionReview,
  listLessons,
  openOutcomeReview,
  recordCommitment,
  retireLesson,
  startImplementation,
} from "./api";

const requiredText = (message: string) => z.string().trim().min(1, message);

const commitmentSchema = z.object({
  implementation_owner_id: requiredText("Select an implementation owner."),
  commitment_statement: requiredText("Record the commitment."),
  success_measures: requiredText("Define the success measures."),
  review_due_date: requiredText("Choose an outcome-review date."),
  rationale: requiredText("Record why this commitment is appropriate."),
});

const implementationSchema = z.object({
  implementation_plan: requiredText("Record the implementation plan."),
  rationale: requiredText("Record why implementation is ready to begin."),
});

const openReviewSchema = z.object({
  implementation_summary: requiredText("Summarise what was implemented."),
  rationale: requiredText("Record why the work is ready for outcome review."),
});

const completeReviewSchema = z.object({
  outcome_summary: requiredText("Record what actually happened."),
  outcome_assessment: z.enum(["exceeded", "met", "partially_met", "not_met", "inconclusive"]),
  review_evidence: requiredText("Record the evidence used in the assessment."),
  unintended_consequences: z.string().trim(),
  rationale: requiredText("Record why the outcome review is complete."),
});

const lessonSchema = z.object({
  title: requiredText("Give the lesson a concise title."),
  insight: requiredText("Record what the organisation learned."),
  category: z.enum(["process", "evidence", "assumption", "stakeholder", "implementation", "outcome", "other"]),
  applicability: requiredText("Explain when this lesson should be reused."),
  recommended_change: z.string().trim(),
});

const archiveSchema = z.object({
  rationale: requiredText("Record why the learning cycle is complete."),
});

type CommitmentForm = z.infer<typeof commitmentSchema>;
type ImplementationForm = z.infer<typeof implementationSchema>;
type OpenReviewForm = z.infer<typeof openReviewSchema>;
type CompleteReviewForm = z.infer<typeof completeReviewSchema>;
type LessonForm = z.infer<typeof lessonSchema>;
type ArchiveForm = z.infer<typeof archiveSchema>;

function displayName(user: { email: string; first_name: string; last_name: string }) {
  return `${user.first_name} ${user.last_name}`.trim() || user.email;
}

function formatDate(value: string | null) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(new Date(value));
}

function ReviewRecord({ review }: { review: NonNullable<Awaited<ReturnType<typeof getDecisionReview>>["review"]> }) {
  return (
    <section className="page-primary outcome-record" aria-labelledby="execution-record-title">
      <p className="eyebrow">Accountable execution record</p>
      <h2 id="execution-record-title">Commitment and outcome</h2>
      <dl className="record-grid">
        <div><dt>Implementation owner</dt><dd>{displayName(review.implementation_owner)}</dd></div>
        <div><dt>Review due</dt><dd>{formatDate(review.review_due_date)}</dd></div>
        <div className="record-grid__wide"><dt>Commitment</dt><dd>{review.commitment_statement}</dd></div>
        <div className="record-grid__wide"><dt>Success measures</dt><dd>{review.success_measures}</dd></div>
        {review.implementation_plan ? <div className="record-grid__wide"><dt>Implementation plan</dt><dd>{review.implementation_plan}</dd></div> : null}
        {review.implementation_summary ? <div className="record-grid__wide"><dt>What was implemented</dt><dd>{review.implementation_summary}</dd></div> : null}
        {review.outcome_summary ? <div className="record-grid__wide"><dt>Actual outcome</dt><dd>{review.outcome_summary}</dd></div> : null}
        {review.outcome_assessment ? <div><dt>Assessment</dt><dd><span className="status-badge">{review.outcome_assessment_label}</span></dd></div> : null}
        {review.reviewed_at ? <div><dt>Reviewed</dt><dd>{formatDate(review.reviewed_at)}</dd></div> : null}
        {review.review_evidence ? <div className="record-grid__wide"><dt>Review evidence</dt><dd>{review.review_evidence}</dd></div> : null}
        {review.unintended_consequences ? <div className="record-grid__wide"><dt>Unintended consequences</dt><dd>{review.unintended_consequences}</dd></div> : null}
      </dl>
    </section>
  );
}

export function DecisionOutcomesPage() {
  const { decisionId: routeDecisionId } = useParams<{ decisionId: string }>();
  const decisionId = routeDecisionId ?? "";
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const decision = useQuery({
    queryKey: ["decisions", decisionId],
    queryFn: () => getDecision(decisionId),
    enabled: Boolean(decisionId),
  });
  const review = useQuery({
    queryKey: ["decisions", decisionId, "review"],
    queryFn: () => getDecisionReview(decisionId),
    enabled: Boolean(decisionId),
  });
  const lessons = useQuery({
    queryKey: ["decisions", decisionId, "lessons"],
    queryFn: () => listLessons(decisionId),
    enabled: Boolean(decisionId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", decision.data?.organisation_id, "memberships"],
    queryFn: () => listMemberships(decision.data?.organisation_id ?? ""),
    enabled: Boolean(decision.data?.organisation_id),
  });

  const commitmentForm = useForm<CommitmentForm>({
    resolver: zodResolver(commitmentSchema),
    defaultValues: { implementation_owner_id: "", commitment_statement: "", success_measures: "", review_due_date: "", rationale: "" },
  });
  const implementationForm = useForm<ImplementationForm>({
    resolver: zodResolver(implementationSchema),
    defaultValues: { implementation_plan: "", rationale: "" },
  });
  const openReviewForm = useForm<OpenReviewForm>({
    resolver: zodResolver(openReviewSchema),
    defaultValues: { implementation_summary: "", rationale: "" },
  });
  const completeReviewForm = useForm<CompleteReviewForm>({
    resolver: zodResolver(completeReviewSchema),
    defaultValues: { outcome_summary: "", outcome_assessment: "met", review_evidence: "", unintended_consequences: "", rationale: "" },
  });
  const lessonForm = useForm<LessonForm>({
    resolver: zodResolver(lessonSchema),
    defaultValues: { title: "", insight: "", category: "outcome", applicability: "", recommended_change: "" },
  });
  const archiveForm = useForm<ArchiveForm>({ resolver: zodResolver(archiveSchema), defaultValues: { rationale: "" } });

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] }),
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "review"] }),
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "lessons"] }),
      queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "transitions"] }),
    ]);
  };

  const commitment = useMutation({
    mutationFn: (input: CommitmentForm) => recordCommitment(decisionId, { ...input, expected_status: decision.data?.status ?? "" }),
    onSuccess: refresh,
  });
  const implementation = useMutation({
    mutationFn: (input: ImplementationForm) => startImplementation(decisionId, { ...input, expected_status: decision.data?.status ?? "" }),
    onSuccess: refresh,
  });
  const openReview = useMutation({
    mutationFn: (input: OpenReviewForm) => openOutcomeReview(decisionId, { ...input, expected_status: decision.data?.status ?? "" }),
    onSuccess: refresh,
  });
  const completeReview = useMutation({
    mutationFn: (input: CompleteReviewForm) => completeOutcomeReview(decisionId, { ...input, expected_status: decision.data?.status ?? "", outcome_assessment: input.outcome_assessment as OutcomeAssessment }),
    onSuccess: refresh,
  });
  const addLesson = useMutation({
    mutationFn: (input: LessonForm) => createLesson(decisionId, { ...input, category: input.category as LessonCategory }),
    onSuccess: async () => { lessonForm.reset(); await refresh(); },
  });
  const retire = useMutation({ mutationFn: retireLesson, onSuccess: refresh });
  const transferOwner = useMutation({
    mutationFn: (ownerId: string) => changeImplementationOwner(decisionId, ownerId),
    onSuccess: refresh,
  });
  const archive = useMutation({
    mutationFn: (input: ArchiveForm) => archiveDecision(decisionId, { expected_status: decision.data?.status ?? "", rationale: input.rationale }),
    onSuccess: async () => { await refresh(); await navigate(`/decisions/${decisionId}`); },
  });

  if (decision.isPending || review.isPending || lessons.isPending) return <p>Loading outcomes and learning…</p>;
  if (decision.isError || !decision.data || review.isError || lessons.isError) {
    return <StatusMessage kind="error">The outcomes and learning record could not be loaded.</StatusMessage>;
  }

  const current = decision.data;
  const error = commitment.error || implementation.error || openReview.error || completeReview.error || addLesson.error || retire.error || transferOwner.error || archive.error;
  const errorMessage = error instanceof ApiError ? error.message : error ? "The workflow command failed." : null;
  const canCommand = current.can_transition;

  return (
    <div>
      <Link className="back-link" to={`/decisions/${decisionId}`}>← Decision workspace</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Outcomes and organisational learning</p>
          <h1>{current.title}</h1>
          <p className="decision-question">Follow the decision through commitment, implementation, review, and reusable learning.</p>
        </div>
        <span className="status-badge">{current.status_label}</span>
      </div>

      {errorMessage ? <StatusMessage kind="error">{errorMessage}</StatusMessage> : null}
      {review.data.review ? <ReviewRecord review={review.data.review} /> : null}
      {review.data.review && current.can_transition && current.status !== "archived" ? (
        <section className="ownership-transfer" aria-labelledby="implementation-owner-title">
          <div>
            <strong id="implementation-owner-title">Implementation accountability</strong>
            <span>Transfer ownership before removing the current owner from the organisation.</span>
          </div>
          <label className="visually-hidden" htmlFor="transfer-implementation-owner">New implementation owner</label>
          <select
            id="transfer-implementation-owner"
            value={review.data.review.implementation_owner.id}
            disabled={transferOwner.isPending}
            onChange={(event) => {
              if (event.target.value !== review.data.review?.implementation_owner.id) {
                transferOwner.mutate(event.target.value);
              }
            }}
          >
            {memberships.data?.filter((item) => item.status === "active").map((item) => (
              <option key={item.user.id} value={item.user.id}>{displayName(item.user)} — {item.role}</option>
            ))}
          </select>
        </section>
      ) : null}

      <div className="outcome-layout">
        <section className="page-primary" aria-labelledby="next-step-title">
          <p className="eyebrow">Current lifecycle command</p>
          <h2 id="next-step-title">Complete the next accountable step</h2>
          {!canCommand && current.status !== "archived" ? <p className="muted">Only the decision owner or an organisation manager may advance this workflow.</p> : null}

          {current.status === "decision_finalised" ? (
            <form className="stacked-form" onSubmit={commitmentForm.handleSubmit((values) => commitment.mutate(values))} noValidate>
              <label htmlFor="implementation-owner">Implementation owner</label>
              <select id="implementation-owner" {...commitmentForm.register("implementation_owner_id")} disabled={!canCommand}>
                <option value="">Select a member</option>
                {memberships.data?.filter((item) => item.status === "active").map((item) => <option key={item.user.id} value={item.user.id}>{displayName(item.user)} — {item.role}</option>)}
              </select>
              <FieldError message={commitmentForm.formState.errors.implementation_owner_id?.message} />
              <label htmlFor="commitment-statement">Commitment statement</label>
              <textarea id="commitment-statement" rows={4} {...commitmentForm.register("commitment_statement")} disabled={!canCommand} />
              <FieldError message={commitmentForm.formState.errors.commitment_statement?.message} />
              <label htmlFor="success-measures">Success measures</label>
              <textarea id="success-measures" rows={4} {...commitmentForm.register("success_measures")} disabled={!canCommand} />
              <FieldError message={commitmentForm.formState.errors.success_measures?.message} />
              <label htmlFor="review-due">Outcome review due</label>
              <input id="review-due" type="date" {...commitmentForm.register("review_due_date")} disabled={!canCommand} />
              <FieldError message={commitmentForm.formState.errors.review_due_date?.message} />
              <label htmlFor="commitment-rationale">Rationale</label>
              <textarea id="commitment-rationale" rows={3} {...commitmentForm.register("rationale")} disabled={!canCommand} />
              <FieldError message={commitmentForm.formState.errors.rationale?.message} />
              <button className="button button--primary" type="submit" disabled={!canCommand || commitment.isPending}>Record commitment</button>
            </form>
          ) : null}

          {current.status === "commitment" ? (
            <form className="stacked-form" onSubmit={implementationForm.handleSubmit((values) => implementation.mutate(values))} noValidate>
              <label htmlFor="implementation-plan">Implementation plan</label>
              <textarea id="implementation-plan" rows={7} {...implementationForm.register("implementation_plan")} disabled={!canCommand} />
              <FieldError message={implementationForm.formState.errors.implementation_plan?.message} />
              <label htmlFor="implementation-rationale">Rationale</label>
              <textarea id="implementation-rationale" rows={3} {...implementationForm.register("rationale")} disabled={!canCommand} />
              <FieldError message={implementationForm.formState.errors.rationale?.message} />
              <button className="button button--primary" type="submit" disabled={!canCommand || implementation.isPending}>Start implementation</button>
            </form>
          ) : null}

          {current.status === "implementation" ? (
            <form className="stacked-form" onSubmit={openReviewForm.handleSubmit((values) => openReview.mutate(values))} noValidate>
              <label htmlFor="implementation-summary">What was implemented?</label>
              <textarea id="implementation-summary" rows={7} {...openReviewForm.register("implementation_summary")} disabled={!canCommand} />
              <FieldError message={openReviewForm.formState.errors.implementation_summary?.message} />
              <label htmlFor="open-review-rationale">Rationale</label>
              <textarea id="open-review-rationale" rows={3} {...openReviewForm.register("rationale")} disabled={!canCommand} />
              <FieldError message={openReviewForm.formState.errors.rationale?.message} />
              <button className="button button--primary" type="submit" disabled={!canCommand || openReview.isPending}>Open outcome review</button>
            </form>
          ) : null}

          {current.status === "outcome_review" ? (
            <form className="stacked-form" onSubmit={completeReviewForm.handleSubmit((values) => completeReview.mutate(values))} noValidate>
              <label htmlFor="outcome-summary">What actually happened?</label>
              <textarea id="outcome-summary" rows={6} {...completeReviewForm.register("outcome_summary")} disabled={!canCommand} />
              <FieldError message={completeReviewForm.formState.errors.outcome_summary?.message} />
              <label htmlFor="outcome-assessment">Assessment</label>
              <select id="outcome-assessment" {...completeReviewForm.register("outcome_assessment")} disabled={!canCommand}>
                <option value="exceeded">Exceeded expectations</option><option value="met">Met expectations</option><option value="partially_met">Partially met expectations</option><option value="not_met">Did not meet expectations</option><option value="inconclusive">Inconclusive</option>
              </select>
              <label htmlFor="review-evidence">Evidence used</label>
              <textarea id="review-evidence" rows={5} {...completeReviewForm.register("review_evidence")} disabled={!canCommand} />
              <FieldError message={completeReviewForm.formState.errors.review_evidence?.message} />
              <label htmlFor="unintended-consequences">Unintended consequences</label>
              <textarea id="unintended-consequences" rows={4} {...completeReviewForm.register("unintended_consequences")} disabled={!canCommand} />
              <label htmlFor="complete-review-rationale">Completion rationale</label>
              <textarea id="complete-review-rationale" rows={3} {...completeReviewForm.register("rationale")} disabled={!canCommand} />
              <FieldError message={completeReviewForm.formState.errors.rationale?.message} />
              <button className="button button--primary" type="submit" disabled={!canCommand || completeReview.isPending}>Complete outcome review</button>
            </form>
          ) : null}

          {current.status === "lessons_learned" ? (
            <form className="stacked-form" onSubmit={archiveForm.handleSubmit((values) => archive.mutate(values))} noValidate>
              <p className="muted">Capture at least one active lesson before archiving the decision.</p>
              <label htmlFor="archive-rationale">Why is the learning cycle complete?</label>
              <textarea id="archive-rationale" rows={4} {...archiveForm.register("rationale")} disabled={!canCommand} />
              <FieldError message={archiveForm.formState.errors.rationale?.message} />
              <button className="button button--primary" type="submit" disabled={!canCommand || archive.isPending}>Archive decision</button>
            </form>
          ) : null}

          {current.status === "archived" ? <StatusMessage kind="success">This decision completed the full learning cycle and is archived.</StatusMessage> : null}
          {!(["decision_finalised", "commitment", "implementation", "outcome_review", "lessons_learned", "archived"] as string[]).includes(current.status) ? <p className="muted">Outcomes become available after the human final decision is recorded.</p> : null}
        </section>

        <section className="page-primary" aria-labelledby="lessons-title">
          <p className="eyebrow">Reusable knowledge</p>
          <h2 id="lessons-title">Lessons learned</h2>
          {lessons.data.length ? (
            <div className="lesson-list">
              {lessons.data.map((lesson) => (
                <article className={`lesson-card${lesson.status === "retired" ? " lesson-card--retired" : ""}`} key={lesson.id}>
                  <div className="reasoning-card__heading"><div><span className="role-badge">{lesson.category_label}</span><h3>{lesson.title}</h3></div><span className="status-badge">{lesson.status_label}</span></div>
                  <p>{lesson.insight}</p>
                  <p><strong>Reuse when:</strong> {lesson.applicability}</p>
                  {lesson.recommended_change ? <p><strong>Recommended change:</strong> {lesson.recommended_change}</p> : null}
                  {lesson.status === "active" && current.status === "lessons_learned" && canCommand ? <button className="button button--danger-quiet" type="button" onClick={() => { if (window.confirm("Retire this lesson?")) retire.mutate(lesson.id); }}>Retire</button> : null}
                </article>
              ))}
            </div>
          ) : <div className="empty-state"><p>No lessons have been captured yet.</p></div>}

          {current.status === "lessons_learned" && canCommand ? (
            <form className="stacked-form lesson-form" onSubmit={lessonForm.handleSubmit((values) => addLesson.mutate(values))} noValidate>
              <h3>Capture a lesson</h3>
              <label htmlFor="lesson-title">Title</label><input id="lesson-title" {...lessonForm.register("title")} /><FieldError message={lessonForm.formState.errors.title?.message} />
              <label htmlFor="lesson-category">Category</label><select id="lesson-category" {...lessonForm.register("category")}><option value="process">Decision process</option><option value="evidence">Evidence quality</option><option value="assumption">Assumption</option><option value="stakeholder">Stakeholder involvement</option><option value="implementation">Implementation</option><option value="outcome">Outcome</option><option value="other">Other</option></select>
              <label htmlFor="lesson-insight">What was learned?</label><textarea id="lesson-insight" rows={5} {...lessonForm.register("insight")} /><FieldError message={lessonForm.formState.errors.insight?.message} />
              <label htmlFor="lesson-applicability">When should this be reused?</label><textarea id="lesson-applicability" rows={4} {...lessonForm.register("applicability")} /><FieldError message={lessonForm.formState.errors.applicability?.message} />
              <label htmlFor="lesson-change">Recommended organisational change</label><textarea id="lesson-change" rows={4} {...lessonForm.register("recommended_change")} />
              <button className="button button--primary" type="submit" disabled={addLesson.isPending}>Save lesson</button>
            </form>
          ) : null}
        </section>
      </div>
    </div>
  );
}
