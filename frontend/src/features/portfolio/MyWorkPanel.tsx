import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { fetchCurrentUser } from "../auth/api";
import { decisionLifecycle } from "../decisions/lifecycle";
import { getPersonalWork } from "./api";

type WorkFilter = "all" | "attention" | "overdue";

function formatDate(value: string | null): string {
  if (!value) return "No due date";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(new Date(value));
}

function stagePercent(status: string): number {
  const index = decisionLifecycle.findIndex((item) => item.status === status);
  return index < 0 ? 0 : Math.round(((index + 1) / decisionLifecycle.length) * 100);
}

export function MyWorkPanel() {
  const [filter, setFilter] = useState<WorkFilter>("all");
  const currentUser = useQuery({ queryKey: ["current-user"], queryFn: fetchCurrentUser, staleTime: 60_000 });
  const work = useQuery({
    queryKey: ["personal-work"],
    queryFn: getPersonalWork,
  });

  const decisions = useMemo(() => {
    const items = work.data?.decisions ?? [];
    if (filter === "overdue") return items.filter((item) => item.is_overdue);
    if (filter === "attention") return items.filter((item) => item.is_overdue || item.unresolved_discussion_count > 0 || ["high", "critical"].includes(item.urgency));
    return items;
  }, [filter, work.data?.decisions]);

  const firstName = currentUser.data?.first_name?.trim();

  return (
    <section className="my-work-panel my-work-panel--executive" aria-labelledby="my-work-title">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Decision command centre</p>
          <h1 id="my-work-title">{firstName ? `Good to see you, ${firstName}.` : "Your decision work."}</h1>
          <p>Focus on the decisions where your judgement, contribution, or follow-through matters next.</p>
        </div>
        <div className="dashboard-hero__actions">
          <Link className="button button--secondary button-link button--with-icon" to="/contributions">
            <Icon name="check" size={18} />
            <span>Contribution inbox</span>
          </Link>
          <Link className="button button--secondary button-link button--with-icon" to="/notifications">
            <Icon name="bell" size={18} />
            <span>{work.data?.unread_notifications ?? 0} unread notifications</span>
          </Link>
        </div>
      </div>

      {work.isError ? <StatusMessage kind="error">Your work dashboard could not be loaded.</StatusMessage> : null}

      <div className="dashboard-metrics" aria-label="Personal work summary">
        <article>
          <span className="metric-icon metric-icon--green"><Icon name="decision" /></span>
          <div><strong>{work.data?.decision_count ?? 0}</strong><span>Active decisions</span></div>
        </article>
        <article>
          <span className="metric-icon metric-icon--amber"><Icon name="warning" /></span>
          <div><strong>{work.data?.overdue_count ?? 0}</strong><span>Overdue actions</span></div>
        </article>
        <article>
          <span className="metric-icon metric-icon--blue"><Icon name="bell" /></span>
          <div><strong>{work.data?.unread_notifications ?? 0}</strong><span>Unread updates</span></div>
        </article>
      </div>

      <div className="work-section-heading">
        <div>
          <h2>Priority work</h2>
          <p className="muted">Ordered by urgency, due date, and unresolved work.</p>
        </div>
        <div className="segmented-control" role="group" aria-label="Filter personal work">
          {(["all", "attention", "overdue"] as WorkFilter[]).map((value) => (
            <button key={value} type="button" className={filter === value ? "is-active" : ""} onClick={() => setFilter(value)}>
              {value === "all" ? "All" : value === "attention" ? "Needs attention" : "Overdue"}
            </button>
          ))}
        </div>
      </div>

      {work.isPending ? (
        <div className="skeleton-list" aria-label="Loading your work"><span /><span /><span /></div>
      ) : null}

      {!work.isPending && decisions.length === 0 ? (
        <div className="empty-state empty-state--polished">
          <span className="empty-state__icon"><Icon name={filter === "all" ? "check" : "search"} size={25} /></span>
          <h2>{filter === "all" ? "No active decision work" : "Nothing matches this view"}</h2>
          <p>{filter === "all" ? "Your assignments, contributions, positions, and implementation work will appear here." : "Choose another filter to see the rest of your work."}</p>
        </div>
      ) : null}

      <div className="my-work-list my-work-list--premium">
        {decisions.map((decision) => (
          <Link className={`my-work-card my-work-card--premium${decision.is_overdue ? " my-work-card--overdue" : ""}`} to={`/decisions/${decision.id}`} key={decision.id}>
            <div className="my-work-card__body">
              <div className="my-work-card__topline">
                <span>{decision.organisation_name}</span>
                <span>·</span>
                <span>{decision.workspace.name}</span>
                {decision.participant_role ? <span className="role-badge role-badge--subtle">{decision.participant_role.replaceAll("_", " ")}</span> : null}
              </div>
              <h2>{decision.title}</h2>
              <p className="my-work-card__question">{decision.decision_question || "Decision question not framed yet."}</p>
              <div className="next-action-line">
                <span className="next-action-line__icon"><Icon name="arrow-right" size={16} /></span>
                <span><strong>Next:</strong> {decision.next_action || "Open decision"}</span>
              </div>
              <div className="decision-progress" aria-label={`${decision.status_label} lifecycle progress`}>
                <span style={{ width: `${stagePercent(decision.status)}%` }} />
              </div>
            </div>
            <div className="my-work-card__meta">
              <span className={`urgency-badge urgency-badge--${decision.urgency}`}>{decision.urgency}</span>
              <span className="status-badge">{decision.status_label}</span>
              <span className={decision.is_overdue ? "overdue-text" : "muted"}>{decision.is_overdue ? "Overdue · " : "Due · "}{formatDate(decision.due_date)}</span>
              {decision.unresolved_discussion_count ? <span className="attention-pill">{decision.unresolved_discussion_count} unresolved</span> : null}
              <span className="card-arrow" aria-hidden="true"><Icon name="arrow-right" /></span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
