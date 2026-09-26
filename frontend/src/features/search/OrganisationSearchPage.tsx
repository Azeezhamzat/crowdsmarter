import { useQuery } from "@tanstack/react-query";
import type { FormEvent} from "react";
import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { getOrganisation } from "../organisations/api";
import { searchOrganisation } from "./api";

export function OrganisationSearchPage() {
  const { organisationId: routeOrganisationId } = useParams<{ organisationId: string }>();
  const organisationId = routeOrganisationId ?? "";
  const [searchParams, setSearchParams] = useSearchParams();
  const activeQuery = searchParams.get("q")?.trim() ?? "";
  const [draftQuery, setDraftQuery] = useState(activeQuery);

  const organisation = useQuery({
    queryKey: ["organisations", organisationId],
    queryFn: () => getOrganisation(organisationId),
    enabled: Boolean(organisationId),
  });
  const results = useQuery({
    queryKey: ["organisations", organisationId, "search", activeQuery],
    queryFn: () => searchOrganisation(organisationId, activeQuery),
    enabled: Boolean(organisationId) && activeQuery.length >= 2,
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const query = draftQuery.trim();
    if (query.length >= 2) setSearchParams({ q: query });
  };

  return (
    <div>
      <Link className="back-link" to={`/organisations/${organisationId}`}>← Organisation</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Organisational memory</p>
          <h1>Search {organisation.data?.name ?? "organisation knowledge"}</h1>
          <p className="muted">Find decisions, evidence, assumptions, risks, outcomes, and reusable lessons using PostgreSQL full-text search.</p>
        </div>
      </div>

      <form className="search-form" onSubmit={submit} role="search">
        <label className="visually-hidden" htmlFor="knowledge-search">Search organisational knowledge</label>
        <input id="knowledge-search" type="search" value={draftQuery} onChange={(event) => setDraftQuery(event.target.value)} placeholder="Search a decision, risk, evidence source, or lesson…" />
        <button className="button button--primary" type="submit">Search</button>
      </form>

      {!activeQuery ? <div className="empty-state search-empty"><h2>Search the organisation’s decision memory</h2><p>Try a project name, outcome, risk, stakeholder concern, or important assumption.</p></div> : null}
      {results.isPending && activeQuery ? <p>Searching…</p> : null}
      {results.isError ? <StatusMessage kind="error">Search could not be completed.</StatusMessage> : null}
      {results.data ? (
        <section aria-labelledby="search-results-title">
          <div className="section-heading">
            <div><p className="eyebrow">{results.data.count} results</p><h2 id="search-results-title">Results for “{results.data.query}”</h2></div>
          </div>
          {results.data.results.length ? (
            <div className="search-results">
              {results.data.results.map((result) => (
                <Link className="search-result" to={result.url} key={`${result.kind}-${result.object_id}`}>
                  <div><span className="role-badge">{result.kind}</span><h3>{result.title}</h3></div>
                  {result.snippet ? <p>{result.snippet}</p> : null}
                  <span className="search-result__open">Open record →</span>
                </Link>
              ))}
            </div>
          ) : <div className="empty-state"><h2>No matching records</h2><p>Try fewer words or a broader phrase.</p></div>}
        </section>
      ) : null}
    </div>
  );
}
