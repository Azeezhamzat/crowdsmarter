import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { Link, useParams } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { LanguageSwitcher } from "../../components/LanguageSwitcher";
import { LogoMark } from "../../components/Logo";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { openSessionCatalog } from "../../lib/catalogs/openSession";
import { useTranslations } from "../../lib/i18n";
import { getTerminology } from "../../lib/terminology";
import type { Idea } from "../../lib/types";
import {
  getStoredParticipantToken,
  getPublicSession,
  joinSession,
  postIdeaComment,
  removeVote,
  submitIdea,
  voteIdea,
} from "./api";

const AGE_BRACKETS = ["", "under_13", "age_13_17", "age_18_plus"] as const;
const MINOR_AGE_BRACKETS = new Set(["under_13", "age_13_17"]);
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function buildJoinSchema(requiresGuardianConsent: boolean) {
  return z
    .object({
      name: z.string().trim().min(2, "Enter your name.").max(200),
      email: z.string().trim().email("Enter a valid email address."),
      school_name: z.string().trim().max(200),
      age_bracket: z.enum(AGE_BRACKETS),
      guardian_name: z.string().trim().max(200),
      guardian_email: z.string().trim(),
      guardian_consent_given: z.boolean(),
    })
    .superRefine((values, ctx) => {
      if (!requiresGuardianConsent || !MINOR_AGE_BRACKETS.has(values.age_bracket)) return;
      if (!values.guardian_name.trim()) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["guardian_name"], message: "Enter a parent or guardian's name." });
      }
      if (!EMAIL_PATTERN.test(values.guardian_email.trim())) {
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["guardian_email"], message: "Enter a valid guardian email address." });
      }
      if (!values.guardian_consent_given) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["guardian_consent_given"],
          message: "A parent or guardian must consent before this participant can join.",
        });
      }
    });
}
type JoinForm = z.infer<ReturnType<typeof buildJoinSchema>>;

const ideaSchema = z.object({
  title: z.string().trim().min(3, "Give the idea a short title.").max(240),
  description: z.string().trim().max(4000),
  category: z.string().trim().max(60),
  requested_amount: z.string().trim(),
  team_name: z.string().trim().max(200),
  team_members: z
    .array(z.object({ name: z.string().trim().max(200), role: z.string().trim().max(60) }))
    .max(12),
});
type IdeaForm = z.infer<typeof ideaSchema>;

const commentSchema = z.object({
  body: z.string().trim().min(1, "Write a comment first.").max(4000),
});
type CommentForm = z.infer<typeof commentSchema>;

function submitterLabel(idea: Idea): string {
  if (idea.submitted_by_participant) return idea.submitted_by_participant.name;
  if (idea.submitted_by_user) {
    const name = `${idea.submitted_by_user.first_name} ${idea.submitted_by_user.last_name}`.trim();
    return name || idea.submitted_by_user.email;
  }
  return "Someone";
}

function commenterLabel(comment: Idea["comments"][number]): string {
  if (comment.submitted_by_participant) return comment.submitted_by_participant.name;
  if (comment.submitted_by_user) {
    const name = `${comment.submitted_by_user.first_name} ${comment.submitted_by_user.last_name}`.trim();
    return name || comment.submitted_by_user.email;
  }
  return "Someone";
}

function ApplicationStatusBlock({ status }: { status: NonNullable<Idea["application_status"]> }) {
  return (
    <div className="idea-card__status">
      <span className={`status-badge status-badge--${status.eligibility_status}`}>
        {status.eligibility_status_label}
      </span>
      <span className={`status-badge status-badge--${status.outcome_status}`}>
        {status.outcome_status_label}
        {status.outcome_status === "funded" && status.awarded_amount ? ` · ${status.awarded_amount}` : ""}
      </span>
      {status.outcome_note ? <p className="muted">{status.outcome_note}</p> : null}
    </div>
  );
}

function CommentThread({
  idea,
  canComment,
  onComment,
  isPending,
}: {
  idea: Idea;
  canComment: boolean;
  onComment: (body: string) => void;
  isPending: boolean;
}) {
  const [open, setOpen] = useState(false);
  const form = useForm<CommentForm>({ resolver: zodResolver(commentSchema), defaultValues: { body: "" } });

  return (
    <div className="idea-card__comments">
      <button className="button button--link button--compact" type="button" onClick={() => setOpen((value) => !value)}>
        {idea.comments.length} comment{idea.comments.length === 1 ? "" : "s"} {open ? "▲" : "▼"}
      </button>
      {open ? (
        <div className="idea-card__comment-thread">
          {idea.comments.map((comment) => (
            <div key={comment.id} className="idea-card__comment">
              <strong>{commenterLabel(comment)}</strong>
              <p>{comment.body}</p>
            </div>
          ))}
          {canComment ? (
            <form
              onSubmit={form.handleSubmit((values) => {
                onComment(values.body);
                form.reset();
              })}
              noValidate
            >
              <textarea rows={2} placeholder="Add a comment…" {...form.register("body")} />
              <FieldError message={form.formState.errors.body?.message} />
              <button className="button button--secondary button--compact" type="submit" disabled={isPending}>
                {isPending ? "Posting…" : "Post comment"}
              </button>
            </form>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function IdeaCard({
  idea,
  canVote,
  onVote,
  onUnvote,
  isPending,
  amountFieldLabel,
  canComment,
  onComment,
  commentPending,
}: {
  idea: Idea;
  canVote: boolean;
  onVote: () => void;
  onUnvote: () => void;
  isPending: boolean;
  amountFieldLabel: string;
  canComment: boolean;
  onComment: (body: string) => void;
  commentPending: boolean;
}) {
  return (
    <li className="idea-card">
      <div className="idea-card__body">
        <h3>{idea.title}</h3>
        {idea.category ? <span className="idea-card__category">{idea.category}</span> : null}
        {idea.description ? <p>{idea.description}</p> : null}
        {idea.requested_amount ? (
          <p className="muted">
            <strong>{amountFieldLabel}:</strong> {idea.requested_amount}
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
        <small className="muted">
          {submitterLabel(idea)} · {idea.status_label}
        </small>
        {idea.application_status ? <ApplicationStatusBlock status={idea.application_status} /> : null}
        <CommentThread idea={idea} canComment={canComment} onComment={onComment} isPending={commentPending} />
      </div>
      {canVote ? (
        <button
          className={idea.voted_by_me ? "button button--primary button--compact" : "button button--secondary button--compact"}
          type="button"
          disabled={isPending}
          onClick={idea.voted_by_me ? onUnvote : onVote}
        >
          {idea.voted_by_me ? "Voted" : "Vote"} ({idea.vote_count})
        </button>
      ) : (
        <span className="idea-card__votes">
          {idea.vote_count} vote{idea.vote_count === 1 ? "" : "s"}
        </span>
      )}
    </li>
  );
}

export function OpenSessionPublicPage() {
  const { publicSlug = "" } = useParams<{ publicSlug: string }>();
  const queryClient = useQueryClient();
  const queryKey = ["open-session", publicSlug];
  const [hasToken, setHasToken] = useState(() => Boolean(getStoredParticipantToken(publicSlug)));

  const session = useQuery({
    queryKey,
    queryFn: () => getPublicSession(publicSlug),
    enabled: Boolean(publicSlug),
  });

  const terms = getTerminology(session.data?.decision_template_key);
  const isGrantRound = session.data?.decision_template_key === "grant_round";
  const isIdeaCompetition = session.data?.decision_template_key === "idea_competition";
  const requiresGuardianConsent = session.data?.requires_guardian_consent ?? false;
  const teamSubmissionsEnabled = session.data?.team_submissions_enabled ?? false;
  const t = useTranslations(openSessionCatalog);

  const joinForm = useForm<JoinForm>({
    resolver: zodResolver(buildJoinSchema(requiresGuardianConsent)),
    defaultValues: {
      name: "",
      email: "",
      school_name: "",
      age_bracket: "",
      guardian_name: "",
      guardian_email: "",
      guardian_consent_given: false,
    },
  });
  const declaredAgeBracket = joinForm.watch("age_bracket");
  const isDeclaredMinor = MINOR_AGE_BRACKETS.has(declaredAgeBracket);
  const join = useMutation({
    mutationFn: (values: JoinForm) => joinSession(publicSlug, values),
    onSuccess: async () => {
      setHasToken(true);
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  const ideaForm = useForm<IdeaForm>({
    resolver: zodResolver(ideaSchema),
    defaultValues: { title: "", description: "", category: "", requested_amount: "", team_name: "", team_members: [] },
  });
  const teamFields = useFieldArray({ control: ideaForm.control, name: "team_members" });
  const submit = useMutation({
    mutationFn: (values: IdeaForm) =>
      submitIdea(publicSlug, {
        ...values,
        requested_amount: values.requested_amount || undefined,
        team_name: values.team_name || undefined,
        team_members: values.team_members
          .filter((member) => member.name.trim())
          .map((member) => ({ name: member.name, role: member.role || undefined })),
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKey, data);
      ideaForm.reset();
    },
  });

  const vote = useMutation({
    mutationFn: (ideaId: string) => voteIdea(publicSlug, ideaId),
    onSuccess: (data) => queryClient.setQueryData(queryKey, data),
  });
  const unvote = useMutation({
    mutationFn: (ideaId: string) => removeVote(publicSlug, ideaId),
    onSuccess: (data) => queryClient.setQueryData(queryKey, data),
  });
  const comment = useMutation({
    mutationFn: ({ ideaId, body }: { ideaId: string; body: string }) => postIdeaComment(publicSlug, ideaId, body),
    onSuccess: (data) => queryClient.setQueryData(queryKey, data),
  });

  return (
    <main id="main-content" className="open-session-page" tabIndex={-1}>
      <header className="demo-request-header">
        <Link className="public-brand" to="/" aria-label="CrowdSmarter home">
          <LogoMark size={38} />
          <span><strong>CrowdSmarter</strong><small>Foresight. Collective intelligence. Decisions.</small></span>
        </Link>
        <LanguageSwitcher />
      </header>

      {session.isPending ? <p>Loading this session…</p> : null}
      {session.isError ? (
        <StatusMessage kind="error">
          {session.error instanceof ApiError && session.error.status === 404
            ? "This session link is invalid, or the session hasn't opened yet."
            : "This session could not be loaded."}
        </StatusMessage>
      ) : null}

      {session.data ? (
        <>
          <section className="open-session-intro">
            <p className="public-eyebrow">{session.data.organisation_name}</p>
            <h1>{session.data.title}</h1>
            <p className="open-session-prompt">{session.data.prompt}</p>
            {session.data.description ? <p className="muted">{session.data.description}</p> : null}
            <span className={`status-badge status-badge--${session.data.status}`}>{session.data.status_label}</span>
          </section>

          {session.data.status !== "open" ? (
            <StatusMessage kind="info">
              {session.data.status === "closed"
                ? "This session is closed. You can still see what was submitted below."
                : "This session isn't accepting submissions yet."}
            </StatusMessage>
          ) : null}

          {!hasToken && session.data.status === "open" ? (
            <section className="open-session-join" aria-label="Join this session">
              <h2>{t.joinHeading}</h2>
              <p className="muted">{t.joinDescription}</p>
              {join.isError ? (
                <StatusMessage kind="error">
                  {join.error instanceof ApiError ? join.error.message : "Could not join this session."}
                </StatusMessage>
              ) : null}
              <form onSubmit={joinForm.handleSubmit((values) => join.mutate(values))} noValidate>
                <label htmlFor="join-name">{t.nameLabel}</label>
                <input id="join-name" autoComplete="name" {...joinForm.register("name")} />
                <FieldError message={joinForm.formState.errors.name?.message} />
                <label htmlFor="join-email">{t.emailLabel}</label>
                <input id="join-email" type="email" autoComplete="email" {...joinForm.register("email")} />
                <FieldError message={joinForm.formState.errors.email?.message} />
                {isIdeaCompetition ? (
                  <>
                    <label htmlFor="join-school">{t.schoolLabel}</label>
                    <input id="join-school" {...joinForm.register("school_name")} />
                  </>
                ) : null}
                {requiresGuardianConsent ? (
                  <>
                    <label htmlFor="join-age-bracket">{t.ageBracketLabel}</label>
                    <select id="join-age-bracket" {...joinForm.register("age_bracket")}>
                      <option value="">{t.ageBracketPlaceholder}</option>
                      <option value="under_13">{t.ageBracketUnder13}</option>
                      <option value="age_13_17">{t.ageBracket13to17}</option>
                      <option value="age_18_plus">{t.ageBracket18Plus}</option>
                    </select>
                    {isDeclaredMinor ? (
                      <div className="guardian-consent-block">
                        <h3>{t.guardianConsentHeading}</h3>
                        <p className="muted">{t.guardianConsentDescription}</p>
                        <label htmlFor="join-guardian-name">{t.guardianNameLabel}</label>
                        <input id="join-guardian-name" {...joinForm.register("guardian_name")} />
                        <FieldError message={joinForm.formState.errors.guardian_name?.message} />
                        <label htmlFor="join-guardian-email">{t.guardianEmailLabel}</label>
                        <input id="join-guardian-email" type="email" {...joinForm.register("guardian_email")} />
                        <FieldError message={joinForm.formState.errors.guardian_email?.message} />
                        <label className="checkbox-label">
                          <input type="checkbox" {...joinForm.register("guardian_consent_given")} />
                          {t.guardianConsentCheckboxLabel}
                        </label>
                        <FieldError message={joinForm.formState.errors.guardian_consent_given?.message} />
                      </div>
                    ) : null}
                  </>
                ) : null}
                <button className="button button--primary" type="submit" disabled={join.isPending}>
                  {join.isPending ? t.joiningButton : t.joinButton}
                </button>
              </form>
            </section>
          ) : null}

          {hasToken && session.data.status === "open" ? (
            <section className="open-session-submit" aria-label={terms.submitIdeaCta}>
              <h2>{terms.submitIdeaCta}</h2>
              {submit.isError ? (
                <StatusMessage kind="error">
                  {submit.error instanceof ApiError
                    ? submit.error.message
                    : `Could not submit that ${terms.ideaNoun.toLowerCase()}.`}
                </StatusMessage>
              ) : null}
              <form onSubmit={ideaForm.handleSubmit((values) => submit.mutate(values))} noValidate>
                <label htmlFor="idea-title">Title</label>
                <input id="idea-title" {...ideaForm.register("title")} />
                <FieldError message={ideaForm.formState.errors.title?.message} />
                <label htmlFor="idea-description">Description</label>
                <textarea id="idea-description" rows={3} {...ideaForm.register("description")} />
                <label htmlFor="idea-category">Category (optional)</label>
                <input id="idea-category" {...ideaForm.register("category")} />
                {isGrantRound ? (
                  <>
                    <label htmlFor="idea-amount">{terms.amountFieldLabel}</label>
                    <input
                      id="idea-amount"
                      type="number"
                      min={0}
                      step="0.01"
                      {...ideaForm.register("requested_amount")}
                    />
                  </>
                ) : null}
                {teamSubmissionsEnabled ? (
                  <>
                    <label htmlFor="idea-team-name">{t.teamNameLabel}</label>
                    <input id="idea-team-name" {...ideaForm.register("team_name")} />
                    <div className="team-roster-fields">
                      <span className="form-label">{t.teamMembersLabel}</span>
                      {teamFields.fields.map((field, index) => (
                        <div className="team-roster-row" key={field.id}>
                          <input
                            aria-label={t.teamMemberNamePlaceholder}
                            placeholder={t.teamMemberNamePlaceholder}
                            {...ideaForm.register(`team_members.${index}.name` as const)}
                          />
                          <input
                            aria-label={t.teamMemberRolePlaceholder}
                            placeholder={t.teamMemberRolePlaceholder}
                            {...ideaForm.register(`team_members.${index}.role` as const)}
                          />
                          <button
                            className="button button--quiet button--compact"
                            type="button"
                            onClick={() => teamFields.remove(index)}
                          >
                            {t.removeTeamMemberButton}
                          </button>
                        </div>
                      ))}
                      <button
                        className="button button--secondary button--compact"
                        type="button"
                        onClick={() => teamFields.append({ name: "", role: "" })}
                      >
                        {t.addTeamMemberButton}
                      </button>
                    </div>
                  </>
                ) : null}
                <button className="button button--secondary" type="submit" disabled={submit.isPending}>
                  {submit.isPending ? "Submitting…" : `Submit ${terms.ideaNoun.toLowerCase()}`}
                </button>
              </form>
            </section>
          ) : null}

          <section className="open-session-ideas" aria-label={`Submitted ${terms.ideaNounPlural.toLowerCase()}`}>
            <h2>{terms.ideaNounPlural} ({session.data.ideas.length})</h2>
            {session.data.ideas.length === 0 ? (
              <p className="muted">No {terms.ideaNounPlural.toLowerCase()} yet - be the first.</p>
            ) : (
              <ul className="idea-list">
                {session.data.ideas.map((idea) => (
                  <IdeaCard
                    key={idea.id}
                    idea={idea}
                    canVote={hasToken && session.data!.status === "open" && session.data!.voting_enabled}
                    isPending={vote.isPending || unvote.isPending}
                    onVote={() => vote.mutate(idea.id)}
                    onUnvote={() => unvote.mutate(idea.id)}
                    amountFieldLabel={terms.amountFieldLabel}
                    canComment={hasToken && session.data!.status === "open"}
                    onComment={(body) => comment.mutate({ ideaId: idea.id, body })}
                    commentPending={comment.isPending}
                  />
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}
