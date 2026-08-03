import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { AIReviewFinding, AIReviewOutput } from "../../lib/types";
import { getDecision } from "../decisions/api";
import { acknowledgeAIReview, dismissAIReview, listAIReviews, requestAIReview } from "./api";

const sections: Array<{ key: keyof Pick<AIReviewOutput, "missing_evidence" | "unsupported_assumptions" | "contradictory_evidence" | "missing_stakeholders" | "risk_highlights">; title: string }> = [
  { key: "missing_evidence", title: "Missing evidence" },
  { key: "unsupported_assumptions", title: "Unsupported assumptions" },
  { key: "contradictory_evidence", title: "Contradictory evidence" },
  { key: "missing_stakeholders", title: "Missing stakeholders" },
  { key: "risk_highlights", title: "Risk highlights" },
];

function FindingList({ findings }: { findings: AIReviewFinding[] }) {
  if (!findings.length) return <p className="muted">No finding was raised in this category.</p>;
  return (
    <div className="ai-finding-list">
      {findings.map((finding, index) => (
        <article className={`ai-finding ai-finding--${finding.severity}`} key={`${finding.title}-${index}`}>
          <span className="role-badge">{finding.severity}</span>
          <h3>{finding.title}</h3>
          <p>{finding.detail}</p>
        </article>
      ))}
    </div>
  );
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function DecisionAIReviewPage() {
  const { decisionId: routeDecisionId } = useParams<{ decisionId: string }>();
  const decisionId = routeDecisionId ?? "";
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");
  const [dismissalReason, setDismissalReason] = useState("");
  const decision = useQuery({ queryKey: ["decisions", decisionId], queryFn: () => getDecision(decisionId), enabled: Boolean(decisionId) });
  const reviews = useQuery({ queryKey: ["decisions", decisionId, "ai-reviews"], queryFn: () => listAIReviews(decisionId), enabled: Boolean(decisionId) });
  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["decisions", decisionId, "ai-reviews"] });
    await queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };
  const requestReview = useMutation({ mutationFn: () => requestAIReview(decisionId), onSuccess: refresh });
  const acknowledge = useMutation({
    mutationFn: ({ reviewId, reviewNotes }: { reviewId: string; reviewNotes: string }) => acknowledgeAIReview(reviewId, reviewNotes),
    onSuccess: async () => { setNotes(""); await refresh(); },
  });
  const dismiss = useMutation({
    mutationFn: ({ reviewId, reason }: { reviewId: string; reason: string }) => dismissAIReview(reviewId, reason),
    onSuccess: async () => { setDismissalReason(""); await refresh(); },
  });

  const latest = reviews.data?.reviews[0];
  const output = latest?.status === "completed" ? latest.output as AIReviewOutput : null;
  const actionError = requestReview.error || acknowledge.error || dismiss.error;

  return (
    <div>
      <Link className="back-link" to={`/decisions/${decisionId}`}>← Decision workspace</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Advisory capability</p>
          <h1>AI review</h1>
          <p className="muted">{decision.data?.title ?? "Decision"}</p>
        </div>
        {reviews.data?.can_request ? (
          <button className="button button--primary" type="button" disabled={requestReview.isPending} onClick={() => requestReview.mutate()}>
            {requestReview.isPending ? "Reviewing…" : "Run a new advisory review"}
          </button>
        ) : null}
      </div>

      <StatusMessage kind="info">
        AI advises; humans decide. This output is attributable, reviewable, dismissible, and cannot modify options, evidence, assumptions, risks, positions, or decisions.
      </StatusMessage>
      {actionError ? <StatusMessage kind="error">{actionError instanceof ApiError ? actionError.message : "The AI review command failed."}</StatusMessage> : null}
      {reviews.isPending ? <p>Loading advisory reviews…</p> : null}
      {reviews.isError ? <StatusMessage kind="error">AI reviews could not be loaded.</StatusMessage> : null}
      {!latest && !reviews.isPending ? <div className="empty-state"><h2>No advisory review yet</h2><p>Run a review after framing the decision. The default provider uses transparent local rules and no paid service.</p></div> : null}

      {latest ? (
        <section className={`ai-review-record${latest.is_dismissed ? " ai-review-record--dismissed" : ""}`} aria-labelledby="latest-ai-review-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Latest review · {latest.provider_label}</p>
              <h2 id="latest-ai-review-title">{latest.status_label}</h2>
              <p className="muted">Requested by {latest.requested_by.email} on {formatDate(latest.created_at)} · fingerprint {latest.input_fingerprint.slice(0, 12)}</p>
            </div>
            {latest.is_reviewed ? <span className="status-badge">Human reviewed</span> : null}
            {latest.is_dismissed ? <span className="status-badge">Dismissed</span> : null}
          </div>
          {latest.status === "failed" ? <StatusMessage kind="error">The configured provider failed: {latest.error_message}</StatusMessage> : null}
          {output ? (
            <>
              <div className="ai-summary"><h3>Summary</h3><p>{output.summary}</p></div>
              <div className="ai-review-grid">
                {sections.map((section) => (
                  <section className="page-primary" key={section.key}>
                    <h2>{section.title}</h2>
                    <FindingList findings={output[section.key]} />
                  </section>
                ))}
              </div>
              <section className="page-primary ai-similar-decisions">
                <h2>Similar historical decisions</h2>
                {output.similar_decisions.length ? output.similar_decisions.map((item) => (
                  <Link className="search-result" to={item.url} key={item.decision_id}>
                    <div><span className="role-badge">{Math.round(item.similarity * 100)}% term overlap</span><h3>{item.title}</h3></div>
                    <p>{item.reason}</p><span className="search-result__open">Open record →</span>
                  </Link>
                )) : <p className="muted">No sufficiently similar historical decision was found.</p>}
              </section>
              <section className="ai-limitations" aria-labelledby="ai-limitations-title">
                <h2 id="ai-limitations-title">Limitations</h2>
                <ul>{output.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
              </section>
              {latest.can_review ? (
                <div className="ai-human-actions">
                  <section className="page-primary">
                    <h2>Mark as reviewed</h2>
                    <label htmlFor="ai-review-notes">Human review notes</label>
                    <textarea id="ai-review-notes" rows={4} value={notes} onChange={(event) => setNotes(event.target.value)} />
                    <button className="button button--primary" type="button" disabled={acknowledge.isPending} onClick={() => acknowledge.mutate({ reviewId: latest.id, reviewNotes: notes })}>Confirm human review</button>
                  </section>
                  <section className="page-primary">
                    <h2>Dismiss output</h2>
                    <label htmlFor="ai-dismissal-reason">Reason</label>
                    <textarea id="ai-dismissal-reason" rows={4} value={dismissalReason} onChange={(event) => setDismissalReason(event.target.value)} />
                    <button className="button button--danger-quiet" type="button" disabled={dismiss.isPending || !dismissalReason.trim()} onClick={() => dismiss.mutate({ reviewId: latest.id, reason: dismissalReason })}>Dismiss this review</button>
                  </section>
                </div>
              ) : null}
              {latest.is_reviewed ? <StatusMessage kind="success">Reviewed by {latest.reviewed_by?.email}. {latest.review_notes}</StatusMessage> : null}
              {latest.is_dismissed ? <StatusMessage kind="info">Dismissed by {latest.dismissed_by?.email}: {latest.dismissal_reason}</StatusMessage> : null}
            </>
          ) : null}
        </section>
      ) : null}

      {reviews.data && reviews.data.reviews.length > 1 ? (
        <section className="section-block" aria-labelledby="prior-ai-reviews-title">
          <h2 id="prior-ai-reviews-title">Previous reviews</h2>
          <div className="history-list">
            {reviews.data.reviews.slice(1).map((review) => (
              <div className="lesson-card" key={review.id}><strong>{review.provider_label} · {review.status_label}</strong><span className="table-secondary">{formatDate(review.created_at)} · {review.requested_by.email}</span></div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
