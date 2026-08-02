import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { StatusMessage } from "../../components/StatusMessage";
import { getOrganisation } from "../organisations/api";
import { listAuditEvents } from "./api";

function formatAction(action: string): string {
  return action.replaceAll(".", " · ").replaceAll("_", " ");
}

export function OrganisationAuditPage() {
  const { organisationId: routeOrganisationId } = useParams<{
    organisationId: string;
  }>();
  const organisationId = routeOrganisationId ?? "";
  const organisation = useQuery({
    queryKey: ["organisations", organisationId],
    queryFn: () => getOrganisation(organisationId),
    enabled: Boolean(organisationId),
  });
  const events = useQuery({
    queryKey: ["organisations", organisationId, "audit-events"],
    queryFn: () => listAuditEvents(organisationId),
    enabled: Boolean(organisationId),
  });

  if (organisation.isPending) return <p>Loading audit log…</p>;
  if (organisation.isError || !organisation.data) {
    return <StatusMessage kind="error">The organisation could not be loaded.</StatusMessage>;
  }

  return (
    <div>
      <Link className="back-link" to={`/organisations/${organisationId}`}>
        ← Organisation governance
      </Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Customer-owned accountability</p>
          <h1>Audit log</h1>
          <p>{organisation.data.name}</p>
        </div>
      </div>
      <section className="page-primary" aria-labelledby="audit-title">
        <div className="section-heading">
          <div>
            <h2 id="audit-title">Recent material actions</h2>
            <p className="muted">
              The newest 100 attributable events are shown. Audit records are append-only and cannot be edited through the application.
            </p>
          </div>
        </div>
        {events.isPending ? <p>Loading events…</p> : null}
        {events.isError ? (
          <StatusMessage kind="error">
            The audit log is available only to organisation owners and administrators.
          </StatusMessage>
        ) : null}
        {events.data?.length === 0 ? <p className="muted">No audit events exist yet.</p> : null}
        <ol className="audit-list">
          {events.data?.map((event) => (
            <li key={event.id}>
              <div className="section-heading">
                <div>
                  <strong>{formatAction(event.action)}</strong>
                  <span className="table-secondary">
                    {event.object_type} · {event.object_id}
                  </span>
                </div>
                <span className="table-secondary">
                  {new Date(event.created_at).toLocaleString("en-GB")}
                </span>
              </div>
              <p className="muted">Actor: {event.actor?.email ?? "System"}</p>
              {Object.keys(event.metadata).length ? (
                <details>
                  <summary>Recorded details</summary>
                  <pre className="audit-metadata">
                    {JSON.stringify(event.metadata, null, 2)}
                  </pre>
                </details>
              ) : null}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
