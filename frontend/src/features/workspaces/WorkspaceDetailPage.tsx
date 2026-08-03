import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { listDecisions } from "../decisions/api";
import { getWorkspace } from "./api";

function displayName(firstName: string, lastName: string, email: string) {
  return `${firstName} ${lastName}`.trim() || email;
}

export function WorkspaceDetailPage() {
  const { workspaceId: routeWorkspaceId } = useParams<{ workspaceId: string }>();
  const workspaceId = routeWorkspaceId ?? "";
  const workspace = useQuery({
    queryKey: ["workspaces", workspaceId],
    queryFn: () => getWorkspace(workspaceId),
    enabled: Boolean(workspaceId),
  });
  const decisions = useQuery({
    queryKey: ["workspaces", workspaceId, "decisions"],
    queryFn: () => listDecisions(workspaceId),
    enabled: Boolean(workspaceId),
  });

  return (
    <div>
      <Link className="back-link" to={`/organisations/${workspace.data?.organisation_id ?? ""}/workspaces`}>← Workspaces</Link>
      <div className="page-heading workspace-heading">
        <div>
          <p className="eyebrow">Decision workspace</p>
          <h1>{workspace.data?.name ?? "Workspace"}</h1>
          <p className="muted">{workspace.data?.description}</p>
        </div>
        {workspace.data?.can_create_decisions ? (
          <Link className="button button--primary button-link" to={`/workspaces/${workspaceId}/decisions/new`}>
            Start a guided decision
          </Link>
        ) : null}
      </div>

      {decisions.isPending || workspace.isPending ? <p>Loading decisions…</p> : null}
      {decisions.isError || workspace.isError ? (
        <StatusMessage kind="error">The decision workspace could not be loaded.</StatusMessage>
      ) : null}
      {decisions.data?.length === 0 ? (
        <div className="empty-state empty-state--action">
          <p className="eyebrow">No decision records yet</p>
          <h2>Start with the question, not the paperwork</h2>
          <p>The guided flow helps you choose a decision pattern, define boundaries, assign ownership, and create a complete draft.</p>
          {workspace.data?.can_create_decisions ? (
            <Link className="button button--primary button-link" to={`/workspaces/${workspaceId}/decisions/new`}>Create the first decision</Link>
          ) : null}
        </div>
      ) : null}
      <div className="card-list">
        {decisions.data?.map((decision) => (
          <Link className="decision-card decision-card--portfolio" to={`/decisions/${decision.id}`} key={decision.id}>
            <div>
              <div className="inline-heading">
                <h2>{decision.title}</h2>
                <span className="status-badge">{decision.status_label}</span>
              </div>
              <p>{decision.decision_question || "Decision question not framed yet."}</p>
              <p className="muted decision-meta">
                Owner: {displayName(decision.owner.first_name, decision.owner.last_name, decision.owner.email)}
                {" · "}Urgency: {decision.urgency}
                {decision.target_decision_date ? ` · Target: ${new Date(`${decision.target_decision_date}T00:00:00`).toLocaleDateString()}` : ""}
              </p>
            </div>
            <span aria-hidden="true">→</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
