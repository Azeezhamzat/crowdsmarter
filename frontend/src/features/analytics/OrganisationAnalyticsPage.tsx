import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { getOrganisation } from "../organisations/api";
import { getOrganisationAnalytics } from "./api";

function valueOrDash(value: number | null, suffix = ""): string {
  return value === null ? "—" : `${value}${suffix}`;
}

export function OrganisationAnalyticsPage() {
  const { organisationId: routeOrganisationId } = useParams<{ organisationId: string }>();
  const organisationId = routeOrganisationId ?? "";
  const organisation = useQuery({ queryKey: ["organisations", organisationId], queryFn: () => getOrganisation(organisationId), enabled: Boolean(organisationId) });
  const analytics = useQuery({ queryKey: ["organisations", organisationId, "analytics"], queryFn: () => getOrganisationAnalytics(organisationId), enabled: Boolean(organisationId) });

  return (
    <div>
      <Link className="back-link" to={`/organisations/${organisationId}`}>← Organisation</Link>
      <div className="page-heading">
        <div><p className="eyebrow">Decision system health</p><h1>{organisation.data?.name ?? "Organisation"} analytics</h1><p className="muted">A small set of explainable measures—not a leaderboard or an automated judgement of decision quality.</p></div>
      </div>
      {analytics.isPending ? <p>Calculating decision metrics…</p> : null}
      {analytics.isError ? <StatusMessage kind="error">Analytics could not be loaded.</StatusMessage> : null}
      {analytics.data ? (
        <>
          <section className="analytics-scorecards" aria-label="Organisation decision totals">
            <article><span>All decisions</span><strong>{analytics.data.totals.decisions}</strong></article>
            <article><span>Open decisions</span><strong>{analytics.data.totals.open_decisions}</strong></article>
            <article><span>Human-finalised</span><strong>{analytics.data.totals.finalised_decisions}</strong></article>
            <article><span>Active lessons</span><strong>{analytics.data.totals.active_lessons}</strong></article>
          </section>
          <div className="analytics-layout">
            <section className="page-primary">
              <p className="eyebrow">Flow</p><h2>Decision movement</h2>
              <dl className="record-grid">
                <div><dt>Created in 90 days</dt><dd>{analytics.data.flow.created_last_90_days}</dd></div>
                <div><dt>Finalised in 90 days</dt><dd>{analytics.data.flow.finalised_last_90_days}</dd></div>
                <div><dt>Median days to finalise</dt><dd>{valueOrDash(analytics.data.flow.median_days_to_finalise)}</dd></div>
                <div><dt>Overdue target dates</dt><dd>{analytics.data.flow.overdue_target_decisions}</dd></div>
                <div className="record-grid__wide"><dt>Open decisions with at least two participants</dt><dd>{valueOrDash(analytics.data.flow.contribution_coverage_percent, "%")}</dd></div>
              </dl>
              <div className="analytics-bars">
                {analytics.data.flow.status_counts.filter((item) => item.count > 0).map((item) => (
                  <div key={item.status}><span>{item.label}</span><div><i style={{ width: `${Math.max(5, item.count / Math.max(analytics.data.totals.decisions, 1) * 100)}%` }} /></div><strong>{item.count}</strong></div>
                ))}
              </div>
            </section>
            <section className="page-primary">
              <p className="eyebrow">Learning</p><h2>Outcomes and follow-through</h2>
              <dl className="record-grid">
                <div><dt>Outcome reviews completed</dt><dd>{analytics.data.learning.outcome_reviews_completed}</dd></div>
                <div><dt>Met or exceeded</dt><dd>{valueOrDash(analytics.data.learning.outcome_success_percent, "%")}</dd></div>
                <div><dt>Reviews due or overdue</dt><dd>{analytics.data.learning.reviews_due_or_overdue}</dd></div>
                <div><dt>Archived decisions</dt><dd>{analytics.data.totals.archived_decisions}</dd></div>
              </dl>
              <h3>Outcome assessments</h3>
              <ul className="analytics-outcomes">{analytics.data.learning.outcome_assessment_counts.map((item) => <li key={item.assessment}><span>{item.label}</span><strong>{item.count}</strong></li>)}</ul>
            </section>
          </div>
          <section className="analytics-definitions"><h2>How these measures are defined</h2><dl>{Object.entries(analytics.data.definitions).map(([key, definition]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{definition}</dd></div>)}</dl></section>
        </>
      ) : null}
    </div>
  );
}
