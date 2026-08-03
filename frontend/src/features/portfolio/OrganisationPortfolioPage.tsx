import { useQuery } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";
import { Link, useParams } from "react-router";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import type { DecisionUrgency, DecisionStatus } from "../../lib/types";
import { decisionLifecycle } from "../decisions/lifecycle";
import { getOrganisationPortfolio } from "./api";

function formatDate(value: string | null): string {
  if (!value) return "No due date";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(new Date(value));
}

function stagePercent(status: DecisionStatus): number {
  const index = decisionLifecycle.findIndex((item) => item.status === status);
  return index < 0 ? 0 : Math.round(((index + 1) / decisionLifecycle.length) * 100);
}

export function OrganisationPortfolioPage() {
  const { organisationId: routeOrganisationId } = useParams<{ organisationId: string }>();
  const organisationId = routeOrganisationId ?? "";
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [status, setStatus] = useState<DecisionStatus | "">("");
  const [urgency, setUrgency] = useState<DecisionUrgency | "">("");
  const [myWork, setMyWork] = useState(false);
  const [overdue, setOverdue] = useState(false);
  const [view, setView] = useState<"cards" | "compact">("cards");
  const [filtersOpen, setFiltersOpen] = useState(false);

  const portfolio = useQuery({
    queryKey: ["organisations", organisationId, "portfolio", deferredQuery, status, urgency, myWork, overdue],
    queryFn: () => getOrganisationPortfolio(organisationId, { q: deferredQuery, status, urgency, my_work: myWork, overdue }),
    enabled: Boolean(organisationId),
  });

  const activeFilterCount = [status, urgency, myWork, overdue].filter(Boolean).length;

  function clearFilters() {
    setQuery("");
    setStatus("");
    setUrgency("");
    setMyWork(false);
    setOverdue(false);
  }

  return (
    <div className="portfolio-page">
      <Link className="back-link back-link--icon" to={`/organisations/${organisationId}`}><Icon name="arrow-right" size={17} />Organisation</Link>
      <div className="page-heading page-heading--premium">
        <div>
          <p className="eyebrow">Organisation portfolio</p>
          <h1>{portfolio.data?.organisation.name ?? "Organisation decisions"}</h1>
          <p className="muted">A single operating view of decision flow, urgency, ownership, and unresolved work.</p>
        </div>
        <div className="heading-actions">
          <button className="button button--secondary button--with-icon" type="button" onClick={() => setFiltersOpen((open) => !open)}>
            <Icon name="layers" size={18} />Filters{activeFilterCount ? <span className="button-count">{activeFilterCount}</span> : null}
          </button>
          <div className="view-toggle" role="group" aria-label="Portfolio view">
            <button type="button" className={view === "cards" ? "is-active" : ""} onClick={() => setView("cards")} aria-label="Card view"><Icon name="layers" /></button>
            <button type="button" className={view === "compact" ? "is-active" : ""} onClick={() => setView("compact")} aria-label="Compact view"><Icon name="activity" /></button>
          </div>
        </div>
      </div>

      {portfolio.isError ? <StatusMessage kind="error">The decision portfolio could not be loaded.</StatusMessage> : null}

      <section className="portfolio-summary portfolio-summary--premium" aria-label="Portfolio summary">
        <article><span className="metric-icon metric-icon--blue"><Icon name="decision" /></span><div><strong>{portfolio.data?.summary.total ?? 0}</strong><span>Total decisions</span></div></article>
        <article><span className="metric-icon metric-icon--green"><Icon name="activity" /></span><div><strong>{portfolio.data?.summary.active ?? 0}</strong><span>Active</span></div></article>
        <article><span className="metric-icon metric-icon--amber"><Icon name="warning" /></span><div><strong>{portfolio.data?.summary.overdue ?? 0}</strong><span>Overdue</span></div></article>
        <article><span className="metric-icon metric-icon--violet"><Icon name="users" /></span><div><strong>{portfolio.data?.summary.unresolved_discussion ?? 0}</strong><span>Open questions or concerns</span></div></article>
      </section>

      {portfolio.data?.watchlist ? (
        <section className="portfolio-watchlist" aria-label="Executive watchlist">
          <h2>Watchlist</h2>
          <p className="muted">Signals worth acting on, drawn from across every decision in this organisation.</p>
          <div className="watchlist-grid">
            <article className="watchlist-card">
              <h3>Stalled decisions</h3>
              {portfolio.data.watchlist.stalled_decisions.length ? (
                <ul>
                  {portfolio.data.watchlist.stalled_decisions.map((item) => (
                    <li key={item.id}>
                      <Link to={`/decisions/${item.id}`}>{item.title}</Link>
                      <span className="muted"> · {item.status_label} · {item.days_stalled} days without an update</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="muted">No decisions have stalled.</p>}
            </article>
            <article className="watchlist-card">
              <h3>Open high risks</h3>
              {portfolio.data.watchlist.open_high_risks.length ? (
                <ul>
                  {portfolio.data.watchlist.open_high_risks.map((item) => (
                    <li key={item.id}>
                      <Link to={`/decisions/${item.decision_id}`}>{item.title}</Link>
                      <span className="muted"> · {item.decision_title} · likelihood {item.likelihood}/5, impact {item.impact}/5</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="muted">No open high-severity risks.</p>}
            </article>
            <article className="watchlist-card">
              <h3>Assumptions at risk</h3>
              {portfolio.data.watchlist.assumptions_at_risk.length ? (
                <ul>
                  {portfolio.data.watchlist.assumptions_at_risk.map((item) => (
                    <li key={item.id}>
                      <Link to={`/decisions/${item.decision_id}`}>{item.statement}</Link>
                      <span className="muted"> · {item.decision_title} · {item.verification_status_label}</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="muted">No assumptions are overdue or invalidated.</p>}
            </article>
            <article className="watchlist-card">
              <h3>Signposts triggered</h3>
              {portfolio.data.watchlist.triggered_signposts.length ? (
                <ul>
                  {portfolio.data.watchlist.triggered_signposts.map((item) => (
                    <li key={item.id}>
                      <Link to={`/organisations/${organisationId}/foresight/canvases/${item.canvas_id}/scenarios/${item.scenario_set_id}?tab=signposts`}>{item.signpost_title}</Link>
                      <span className="muted"> · {item.assessment_label} on {formatDate(item.observed_on)}</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="muted">No signposts have moved sharply recently.</p>}
            </article>
            <article className="watchlist-card">
              <h3>Benefits realization</h3>
              {portfolio.data.watchlist.benefits_realization.total_reviewed ? (
                <ul className="benefits-realization-list">
                  <li><span>Exceeded</span><strong>{portfolio.data.watchlist.benefits_realization.exceeded}</strong></li>
                  <li><span>Met</span><strong>{portfolio.data.watchlist.benefits_realization.met}</strong></li>
                  <li><span>Partially met</span><strong>{portfolio.data.watchlist.benefits_realization.partially_met}</strong></li>
                  <li><span>Not met</span><strong>{portfolio.data.watchlist.benefits_realization.not_met}</strong></li>
                  <li><span>Inconclusive</span><strong>{portfolio.data.watchlist.benefits_realization.inconclusive}</strong></li>
                </ul>
              ) : <p className="muted">No outcome reviews have been completed yet.</p>}
            </article>
          </div>
        </section>
      ) : null}

      <section className={`portfolio-filters portfolio-filters--premium${filtersOpen ? " is-open" : ""}`} aria-labelledby="portfolio-filters-title">
        <div className="portfolio-search-row">
          <div className="search-field">
            <Icon name="search" size={19} />
            <input id="portfolio-query" type="search" value={query} placeholder="Search title, question, or purpose" onChange={(event) => setQuery(event.target.value)} />
          </div>
          <button className="button button--quiet" type="button" onClick={clearFilters}>Clear filters</button>
        </div>
        <div className="portfolio-filter-grid">
          <div>
            <label htmlFor="portfolio-status">Lifecycle status</label>
            <select id="portfolio-status" value={status} onChange={(event) => setStatus(event.target.value as DecisionStatus | "")}>
              <option value="">All statuses</option>
              {decisionLifecycle.map((item) => <option value={item.status} key={item.status}>{item.label}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="portfolio-urgency">Urgency</label>
            <select id="portfolio-urgency" value={urgency} onChange={(event) => setUrgency(event.target.value as DecisionUrgency | "")}>
              <option value="">All urgency levels</option>
              <option value="critical">Critical</option><option value="high">High</option><option value="normal">Normal</option><option value="low">Low</option>
            </select>
          </div>
          <label className="filter-card"><input type="checkbox" checked={myWork} onChange={(event) => setMyWork(event.target.checked)} /><span><strong>My decisions</strong><small>Only work involving me</small></span></label>
          <label className="filter-card"><input type="checkbox" checked={overdue} onChange={(event) => setOverdue(event.target.checked)} /><span><strong>Overdue only</strong><small>Past target or contribution date</small></span></label>
        </div>
      </section>

      <div className="portfolio-result-bar">
        <span><strong>{portfolio.data?.decisions.length ?? 0}</strong> decision{portfolio.data?.decisions.length === 1 ? "" : "s"}</span>
        {query ? <span className="muted">Matching “{query}”</span> : null}
      </div>

      {portfolio.isPending ? <div className="skeleton-list" aria-label="Loading portfolio"><span /><span /><span /></div> : null}
      {portfolio.data?.decisions.length === 0 ? (
        <div className="empty-state empty-state--polished"><span className="empty-state__icon"><Icon name="search" /></span><h2>No decisions match these filters</h2><p>Clear one or more filters to widen the portfolio view.</p></div>
      ) : null}

      <div className={`portfolio-list portfolio-list--${view}`}>
        {portfolio.data?.decisions.map((decision) => (
          <article className={`portfolio-card portfolio-card--premium${decision.is_overdue ? " portfolio-card--overdue" : ""}`} key={decision.id}>
            <div className="portfolio-card__main">
              <div className="portfolio-card__eyebrow">
                <span>{decision.workspace.name}</span>
                <span className={`urgency-badge urgency-badge--${decision.urgency}`}>{decision.urgency}</span>
              </div>
              <div className="inline-heading">
                <h2><Link to={`/decisions/${decision.id}`}>{decision.title}</Link></h2>
                <span className="status-badge">{decision.status_label}</span>
              </div>
              <p className="portfolio-card__question">{decision.decision_question || "Decision question not framed yet."}</p>
              <div className="portfolio-next-action"><span><Icon name="arrow-right" size={16} /></span><p><strong>Next action:</strong> {decision.next_action}</p></div>
              <div className="portfolio-progress"><span style={{ width: `${stagePercent(decision.status)}%` }} /></div>
            </div>
            <div className="portfolio-card__meta">
              <div><span className="meta-label">Owner</span><strong>{decision.owner.first_name || decision.owner.last_name ? `${decision.owner.first_name} ${decision.owner.last_name}`.trim() : decision.owner.email}</strong></div>
              <div><span className="meta-label">Target</span><strong className={decision.is_overdue ? "overdue-text" : ""}>{formatDate(decision.due_date)}</strong></div>
              <div><span className="meta-label">Discussion</span>{decision.unresolved_discussion_count ? <Link to={`/decisions/${decision.id}/collaboration`}>{decision.unresolved_discussion_count} unresolved discussion item{decision.unresolved_discussion_count === 1 ? "" : "s"}</Link> : <span className="muted">No unresolved discussion</span>}</div>
              <Link className="portfolio-open-link" to={`/decisions/${decision.id}`}>Open decision <Icon name="arrow-right" size={17} /></Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
