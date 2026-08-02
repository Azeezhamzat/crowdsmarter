import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router-dom";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { DiscussionEntry, DiscussionKind } from "../../lib/types";
import { getDecision } from "../decisions/api";
import { listMemberships } from "../organisations/api";
import {
  createDiscussionEntry,
  listDecisionActivity,
  listDiscussion,
  resolveDiscussionEntry,
} from "./api";

const discussionSchema = z.object({
  kind: z.enum(["note", "question", "concern", "update"]),
  body: z.string().trim().min(2, "Enter a useful contribution.").max(12000),
  mentioned_user_ids: z.array(z.string()).max(20),
});

type DiscussionInput = z.infer<typeof discussionSchema>;

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function displayName(entry: DiscussionEntry): string {
  const name = `${entry.author.first_name} ${entry.author.last_name}`.trim();
  return name || entry.author.email;
}

export function DecisionCollaborationPage() {
  const { decisionId: routeDecisionId } = useParams<{ decisionId: string }>();
  const decisionId = routeDecisionId ?? "";
  const queryClient = useQueryClient();
  const [replyTo, setReplyTo] = useState<DiscussionEntry | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<Record<string, string>>({});

  const decision = useQuery({
    queryKey: ["decisions", decisionId],
    queryFn: () => getDecision(decisionId),
    enabled: Boolean(decisionId),
  });
  const discussion = useQuery({
    queryKey: ["decisions", decisionId, "discussion"],
    queryFn: () => listDiscussion(decisionId),
    enabled: Boolean(decisionId),
  });
  const activity = useQuery({
    queryKey: ["decisions", decisionId, "activity"],
    queryFn: () => listDecisionActivity(decisionId),
    enabled: Boolean(decisionId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", decision.data?.organisation_id, "memberships"],
    queryFn: () => listMemberships(decision.data?.organisation_id ?? ""),
    enabled: Boolean(decision.data?.organisation_id),
  });

  const form = useForm<DiscussionInput>({
    resolver: zodResolver(discussionSchema),
    defaultValues: { kind: "note", body: "", mentioned_user_ids: [] },
  });

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["decisions", decisionId, "discussion"],
      }),
      queryClient.invalidateQueries({
        queryKey: ["decisions", decisionId, "activity"],
      }),
      queryClient.invalidateQueries({ queryKey: ["notifications"] }),
    ]);
  };

  const create = useMutation({
    mutationFn: (input: DiscussionInput) =>
      createDiscussionEntry(decisionId, {
        ...input,
        kind: input.kind as DiscussionKind,
        reply_to_id: replyTo?.id ?? null,
      }),
    onSuccess: async () => {
      form.reset({ kind: "note", body: "", mentioned_user_ids: [] });
      setReplyTo(null);
      await refresh();
    },
  });
  const resolve = useMutation({
    mutationFn: ({ entryId, note }: { entryId: string; note: string }) =>
      resolveDiscussionEntry(entryId, note),
    onSuccess: async (_, variables) => {
      setResolutionNotes((current) => ({ ...current, [variables.entryId]: "" }));
      await refresh();
    },
  });

  if (decision.isPending) return <p>Loading collaboration workspace…</p>;
  if (decision.isError || !decision.data) {
    return <StatusMessage kind="error">The decision could not be loaded.</StatusMessage>;
  }

  const error = create.error || resolve.error;

  return (
    <div>
      <Link className="back-link" to={`/decisions/${decisionId}`}>
        ← Decision workspace
      </Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Collaborative reasoning</p>
          <h1>Discussion and activity</h1>
          <p className="muted">
            {decision.data.title}. Contributions remain attributable and cannot be silently edited or deleted.
          </p>
        </div>
        <span className="status-badge">{decision.data.status_label}</span>
      </div>

      {error ? (
        <StatusMessage kind="error">
          {error instanceof ApiError ? error.message : "The collaboration command failed."}
        </StatusMessage>
      ) : null}

      <div className="collaboration-layout">
        <section className="page-primary" aria-labelledby="discussion-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Human contributions</p>
              <h2 id="discussion-title">Decision discussion</h2>
            </div>
            <span className="muted">
              {discussion.data?.entries.length ?? 0} entries
            </span>
          </div>

          {discussion.isPending ? <p>Loading discussion…</p> : null}
          {discussion.isError ? (
            <StatusMessage kind="error">The discussion could not be loaded.</StatusMessage>
          ) : null}
          {discussion.data?.entries.length === 0 ? (
            <div className="empty-state">
              <h2>No discussion entries yet</h2>
              <p>Add a question, concern, note, or implementation update.</p>
            </div>
          ) : null}

          <div className="discussion-list">
            {discussion.data?.entries.map((entry) => (
              <article
                className={`discussion-card discussion-card--${entry.kind}`}
                id={`entry-${entry.id}`}
                key={entry.id}
              >
                <div className="discussion-card__header">
                  <div>
                    <span className="role-badge">{entry.kind_label}</span>
                    {entry.is_resolved ? (
                      <span className="status-badge status-badge--complete">Resolved</span>
                    ) : null}
                  </div>
                  <time dateTime={entry.created_at}>{formatDate(entry.created_at)}</time>
                </div>
                <p className="discussion-author">
                  <strong>{displayName(entry)}</strong>
                  <span>{entry.author.email}</span>
                </p>
                {entry.reply_to_summary ? (
                  <blockquote className="reply-context">
                    Replying to {entry.reply_to_summary.author_email}: {entry.reply_to_summary.body_excerpt}
                  </blockquote>
                ) : null}
                <p className="discussion-body">{entry.body}</p>
                {entry.mentioned_users.length ? (
                  <p className="muted compact-note">
                    Mentioned: {entry.mentioned_users.map((user) => user.email).join(", ")}
                  </p>
                ) : null}
                {entry.is_resolved ? (
                  <div className="resolution-record">
                    <strong>Resolution</strong>
                    <p>{entry.resolution_note}</p>
                    <span className="table-secondary">
                      {entry.resolved_by?.email} · {entry.resolved_at ? formatDate(entry.resolved_at) : ""}
                    </span>
                  </div>
                ) : null}
                <div className="inline-actions">
                  {discussion.data.can_contribute ? (
                    <button
                      className="button button--quiet"
                      type="button"
                      onClick={() => {
                        setReplyTo(entry);
                        document.getElementById("discussion-body")?.focus();
                      }}
                    >
                      Reply
                    </button>
                  ) : null}
                </div>
                {entry.can_resolve && !entry.is_resolved && ["question", "concern"].includes(entry.kind) ? (
                  <form
                    className="resolution-form"
                    onSubmit={(event) => {
                      event.preventDefault();
                      const note = resolutionNotes[entry.id]?.trim() ?? "";
                      if (note) resolve.mutate({ entryId: entry.id, note });
                    }}
                  >
                    <label htmlFor={`resolution-${entry.id}`}>Resolution note</label>
                    <textarea
                      id={`resolution-${entry.id}`}
                      rows={3}
                      value={resolutionNotes[entry.id] ?? ""}
                      onChange={(event) =>
                        setResolutionNotes((current) => ({
                          ...current,
                          [entry.id]: event.target.value,
                        }))
                      }
                    />
                    <button
                      className="button button--secondary"
                      type="submit"
                      disabled={resolve.isPending || !(resolutionNotes[entry.id] ?? "").trim()}
                    >
                      Resolve item
                    </button>
                  </form>
                ) : null}
              </article>
            ))}
          </div>
        </section>

        <aside className="side-panel collaboration-compose" aria-labelledby="compose-title">
          <h2 id="compose-title">Add a contribution</h2>
          <p className="muted">
            Use questions and concerns for items that require an explicit resolution.
          </p>
          {discussion.data && !discussion.data.can_contribute ? (
            <StatusMessage kind="error">
              This decision is read-only for your role or lifecycle state.
            </StatusMessage>
          ) : null}
          {replyTo ? (
            <div className="reply-banner">
              <span>Replying to {replyTo.author.email}</span>
              <button className="button button--quiet" type="button" onClick={() => setReplyTo(null)}>
                Cancel
              </button>
            </div>
          ) : null}
          <form onSubmit={form.handleSubmit((values) => create.mutate(values))} noValidate>
            <label htmlFor="discussion-kind">Contribution type</label>
            <select id="discussion-kind" {...form.register("kind")}>
              <option value="note">Note</option>
              <option value="question">Question</option>
              <option value="concern">Concern</option>
              <option value="update">Update</option>
            </select>

            <label htmlFor="discussion-body">Contribution</label>
            <textarea id="discussion-body" rows={7} {...form.register("body")} />
            <FieldError message={form.formState.errors.body?.message} />

            <fieldset className="mention-fieldset">
              <legend>Mention people</legend>
              <p className="muted compact-note">Mentioned members receive a focused notification.</p>
              {memberships.data?.map((membership) => (
                <label className="checkbox-row" key={membership.id}>
                  <input
                    type="checkbox"
                    value={membership.user.id}
                    {...form.register("mentioned_user_ids")}
                  />
                  <span>{membership.user.email}</span>
                </label>
              ))}
            </fieldset>

            <button
              className="button button--primary button--full"
              type="submit"
              disabled={create.isPending || !discussion.data?.can_contribute}
            >
              {create.isPending ? "Adding…" : "Add contribution"}
            </button>
          </form>
        </aside>
      </div>

      <section className="page-primary section-block" aria-labelledby="activity-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Decision record</p>
            <h2 id="activity-title">Recent activity</h2>
          </div>
          <span className="muted">Latest 200 attributable events</span>
        </div>
        {activity.isPending ? <p>Loading activity…</p> : null}
        {activity.isError ? (
          <StatusMessage kind="error">Decision activity could not be loaded.</StatusMessage>
        ) : null}
        <ol className="activity-timeline">
          {activity.data?.map((item) => (
            <li key={`${item.source}-${item.id}`}>
              <span className={`activity-marker activity-marker--${item.source}`} aria-hidden="true" />
              <div>
                <strong>{item.title}</strong>
                <span className="table-secondary">
                  {item.actor?.email ?? "System"} · {formatDate(item.created_at)}
                </span>
                {typeof item.metadata.body_excerpt === "string" ? (
                  <p>{item.metadata.body_excerpt}</p>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
