import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { ResearchClaim } from "../../lib/types";
import { listMemberships } from "../organisations/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import {
  createResearchClaim,
  linkSourceToResearchClaim,
  listResearchClaims,
  listSources,
  updateResearchClaim,
  unlinkSourceFromResearchClaim,
} from "./api";

type ClaimLinkInput = {
  sourceId: string;
  relationship: "supports" | "contradicts" | "context";
  note: string;
};

const initialClaimForm = {
  statement: "",
  state: "unknown",
  recommendation: "defer",
  relevance: "platform",
  evidence_summary: "",
  limitations: "",
  assumptions: "",
  reversal_conditions: "",
  expected_outcome: "",
  authority_score: 0,
  directness_score: 0,
  recency_score: 0,
  triangulation_score: 0,
  linked_decision_id: "",
  owner_id: "",
  review_due_on: "",
  lifecycle_status: "draft",
};

function personName(user: { first_name: string; last_name: string; email: string }): string {
  return [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email;
}

function scoreGate(score: number): { label: string; tone: string; explanation: string } {
  if (score >= 8) {
    return {
      label: "Roadmap eligible",
      tone: "ready",
      explanation: "Strong enough to consider after security, privacy, accessibility, and operational review.",
    };
  }
  if (score >= 6) {
    return {
      label: "Prototype only",
      tone: "prototype",
      explanation: "Use for a reversible test or facilitation template, not a broad commitment.",
    };
  }
  return {
    label: "Evidence gap",
    tone: "gap",
    explanation: "Research further, integrate, defer, or reject before committing roadmap effort.",
  };
}

function reviewLabel(claim: ResearchClaim): string {
  if (!claim.review_due_on) return "Review not scheduled";
  const date = new Date(`${claim.review_due_on}T00:00:00`);
  const formatted = date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  if (claim.review_status === "overdue") return `Review overdue · ${formatted}`;
  if (claim.review_status === "due_soon") return `Review due soon · ${formatted}`;
  return `Review ${formatted}`;
}

export function ResearchClaimsPanel({
  organisationId,
  canContribute,
}: {
  organisationId: string;
  canContribute: boolean;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(initialClaimForm);
  const [query, setQuery] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [links, setLinks] = useState<Record<string, ClaimLinkInput>>({});

  const claims = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "research-claims"],
    queryFn: () => listResearchClaims(organisationId),
    enabled: Boolean(organisationId),
  });
  const sources = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "sources"],
    queryFn: () => listSources(organisationId),
    enabled: Boolean(organisationId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", organisationId, "memberships"],
    queryFn: () => listMemberships(organisationId),
    enabled: Boolean(organisationId),
  });
  const portfolio = useQuery({
    queryKey: ["organisations", organisationId, "portfolio", "foresight-linking"],
    queryFn: () => getOrganisationPortfolio(organisationId, {}),
    enabled: Boolean(organisationId),
  });

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["organisations", organisationId, "foresight"],
      }),
      queryClient.invalidateQueries({
        queryKey: ["organisations", organisationId, "search"],
      }),
    ]);
  };
  const createClaim = useMutation({
    mutationFn: () =>
      createResearchClaim(organisationId, {
        ...form,
        linked_decision_id: form.linked_decision_id || null,
        owner_id: form.owner_id || undefined,
        review_due_on: form.review_due_on || null,
      }),
    onSuccess: async () => {
      setForm(initialClaimForm);
      await refresh();
    },
  });
  const updateClaim = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Record<string, unknown> }) =>
      updateResearchClaim(id, input),
    onSuccess: refresh,
  });
  const linkSource = useMutation({
    mutationFn: ({ claimId, input }: { claimId: string; input: ClaimLinkInput }) =>
      linkSourceToResearchClaim(claimId, {
        source_id: input.sourceId,
        relationship: input.relationship,
        note: input.note,
      }),
    onSuccess: async (_, variables) => {
      setLinks((current) => ({
        ...current,
        [variables.claimId]: { sourceId: "", relationship: "supports", note: "" },
      }));
      await refresh();
    },
  });
  const unlinkSource = useMutation({
    mutationFn: ({ claimId, sourceId }: { claimId: string; sourceId: string }) =>
      unlinkSourceFromResearchClaim(claimId, sourceId),
    onSuccess: refresh,
  });

  const filteredClaims = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (claims.data ?? []).filter((claim) => {
      const matchesState = !stateFilter || claim.state === stateFilter;
      const haystack = `${claim.statement} ${claim.evidence_summary} ${claim.limitations} ${claim.expected_outcome}`.toLowerCase();
      return matchesState && (!needle || haystack.includes(needle));
    });
  }, [claims.data, query, stateFilter]);
  const error =
    claims.error || createClaim.error || updateClaim.error || linkSource.error || unlinkSource.error;
  const formScore =
    form.authority_score +
    form.directness_score +
    form.recency_score +
    form.triangulation_score;

  return (
    <div className="research-claims-layout">
      <section className="page-primary research-claim-workspace">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Decision-grade research</p>
            <h2>Claim ledger</h2>
            <p className="muted">
              Test one neutral proposition at a time, preserve conflicting evidence, and record
              what would change the resulting decision.
            </p>
          </div>
          <span className="role-badge">{filteredClaims.length} shown</span>
        </div>
        <div className="claim-method-strip" aria-label="Evidence score method">
          <span><strong>Authority</strong> 0–3</span>
          <span><strong>Directness</strong> 0–3</span>
          <span><strong>Recency</strong> 0–2</span>
          <span><strong>Triangulation</strong> 0–2</span>
        </div>
        {error ? (
          <StatusMessage kind="error">
            {error instanceof ApiError ? error.message : "The research claim action could not be completed."}
          </StatusMessage>
        ) : null}
        <div className="foresight-filterbar">
          <label className="visually-hidden" htmlFor="claim-search">Search claims</label>
          <input
            id="claim-search"
            type="search"
            placeholder="Search claims, evidence, limits, or outcomes…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <select
            aria-label="Filter claims by evidence state"
            value={stateFilter}
            onChange={(event) => setStateFilter(event.target.value)}
          >
            <option value="">All evidence states</option>
            <option value="demonstrated">Demonstrated</option>
            <option value="supported">Supported</option>
            <option value="plausible">Plausible</option>
            <option value="unknown">Unknown</option>
            <option value="contradicted">Contradicted</option>
          </select>
        </div>
        <div className="research-claim-list">
          {filteredClaims.map((claim) => {
            const gate = scoreGate(claim.evidence_score);
            const link = links[claim.id] ?? {
              sourceId: "",
              relationship: "supports" as const,
              note: "",
            };
            const availableSources = (sources.data ?? []).filter(
              (source) => !claim.source_links.some((item) => item.source_id === source.id),
            );
            return (
              <article className={`research-claim-card research-claim-card--${gate.tone}`} key={claim.id}>
                <header>
                  <div className="inline-badges">
                    <span className="status-badge">{claim.state_label}</span>
                    <span className="role-badge">{claim.recommendation_label}</span>
                    <span className="role-badge">{claim.relevance_label}</span>
                    <span className={`claim-review claim-review--${claim.review_status}`}>
                      {reviewLabel(claim)}
                    </span>
                  </div>
                  <div className="claim-score" title={gate.explanation}>
                    <strong>{claim.evidence_score}</strong><span>/10</span><small>{gate.label}</small>
                  </div>
                </header>
                <h3>{claim.statement}</h3>
                {claim.evidence_summary ? (
                  <div className="claim-section"><span>Evidence assessment</span><p>{claim.evidence_summary}</p></div>
                ) : null}
                <div className="claim-evidence-balance">
                  <span className="claim-support">{claim.support_count} supporting</span>
                  <span className="claim-contrary">{claim.contrary_count} contrary</span>
                  <span>{claim.source_links.length} total sources</span>
                </div>
                {claim.source_links.length ? (
                  <div className="claim-source-list">
                    {claim.source_links.map((item) => (
                      <div className={`claim-source claim-source--${item.relationship}`} key={item.id}>
                        <span>{item.relationship_label}</span>
                        <div>
                          {item.source_url ? (
                            <a href={item.source_url} target="_blank" rel="noreferrer">{item.source_title}</a>
                          ) : <strong>{item.source_title}</strong>}
                          <small>
                            {[item.source_type_label, item.publisher, item.published_on, `${item.credibility} credibility`]
                              .filter(Boolean).join(" · ")}
                          </small>
                          {item.note ? <p>{item.note}</p> : null}
                        </div>
                        {claim.can_edit ? (
                          <button
                            className="button button--quiet"
                            type="button"
                            disabled={unlinkSource.isPending}
                            onClick={() => unlinkSource.mutate({ claimId: claim.id, sourceId: item.source_id })}
                            aria-label={`Remove ${item.source_title} from this claim`}
                          >
                            Remove
                          </button>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="claim-warning">No sources linked. The score is not independently inspectable yet.</p>
                )}
                <div className="claim-detail-grid">
                  <div><span>Limitations / contrary evidence</span><p>{claim.limitations || "Not recorded."}</p></div>
                  <div><span>Reversal condition</span><p>{claim.reversal_conditions || "Not recorded."}</p></div>
                  <div><span>Expected observable result</span><p>{claim.expected_outcome || "Not recorded."}</p></div>
                  <div><span>Accountability</span><p>Owner: {personName(claim.owner)}</p>{claim.linked_decision ? <Link to={`/decisions/${claim.linked_decision.id}`}>{claim.linked_decision.title}</Link> : <p>No linked decision.</p>}</div>
                </div>
                {claim.can_edit ? (
                  <>
                    <div className="claim-controls">
                      <select
                        aria-label={`Evidence state for ${claim.statement}`}
                        value={claim.state}
                        onChange={(event) => updateClaim.mutate({ id: claim.id, input: { state: event.target.value } })}
                      >
                        <option value="demonstrated">Demonstrated</option>
                        <option value="supported">Supported</option>
                        <option value="plausible">Plausible</option>
                        <option value="unknown">Unknown</option>
                        <option value="contradicted">Contradicted</option>
                      </select>
                      <select
                        aria-label={`Recommendation for ${claim.statement}`}
                        value={claim.recommendation}
                        onChange={(event) => updateClaim.mutate({ id: claim.id, input: { recommendation: event.target.value } })}
                      >
                        <option value="build">Build</option>
                        <option value="integrate">Integrate</option>
                        <option value="defer">Defer</option>
                        <option value="avoid">Avoid</option>
                        <option value="monitor">Monitor</option>
                      </select>
                      <select
                        aria-label={`Lifecycle for ${claim.statement}`}
                        value={claim.lifecycle_status}
                        onChange={(event) => updateClaim.mutate({ id: claim.id, input: { lifecycle_status: event.target.value } })}
                      >
                        <option value="draft">Draft</option>
                        <option value="active">Active</option>
                        <option value="retired">Retired</option>
                      </select>
                    </div>
                    <details className="claim-source-linker">
                      <summary>Link supporting, contrary, or contextual evidence</summary>
                      <div className="claim-source-linker__grid">
                        <select
                          aria-label="Source"
                          value={link.sourceId}
                          onChange={(event) => setLinks((current) => ({ ...current, [claim.id]: { ...link, sourceId: event.target.value } }))}
                        >
                          <option value="">Choose an unlinked source…</option>
                          {availableSources.map((source) => <option key={source.id} value={source.id}>{source.title}</option>)}
                        </select>
                        <select
                          aria-label="Evidence relationship"
                          value={link.relationship}
                          onChange={(event) => setLinks((current) => ({ ...current, [claim.id]: { ...link, relationship: event.target.value as ClaimLinkInput["relationship"] } }))}
                        >
                          <option value="supports">Supports</option>
                          <option value="contradicts">Contradicts</option>
                          <option value="context">Context only</option>
                        </select>
                        <input
                          aria-label="Evidence relationship note"
                          placeholder="Why does this source bear on the claim?"
                          value={link.note}
                          onChange={(event) => setLinks((current) => ({ ...current, [claim.id]: { ...link, note: event.target.value } }))}
                        />
                        <button
                          className="button button--secondary"
                          type="button"
                          disabled={!link.sourceId || linkSource.isPending}
                          onClick={() => linkSource.mutate({ claimId: claim.id, input: link })}
                        >
                          Link evidence
                        </button>
                      </div>
                    </details>
                  </>
                ) : null}
              </article>
            );
          })}
          {!filteredClaims.length ? (
            <div className="empty-state">
              <Icon name="layers" />
              <h3>No matching research claims</h3>
              <p>Start with a neutral proposition that could genuinely change the roadmap.</p>
            </div>
          ) : null}
        </div>
      </section>

      <aside className="side-panel foresight-create-panel claim-create-panel">
        <p className="eyebrow">Bounded research question</p>
        <h2>Record a claim</h2>
        <p className="muted">Keep it small enough that contrary evidence could change the decision.</p>
        {!canContribute ? <p className="muted">Your organisation role is read-only.</p> : (
          <form onSubmit={(event) => { event.preventDefault(); createClaim.mutate(); }}>
            <label htmlFor="claim-statement">Neutral claim</label>
            <textarea id="claim-statement" rows={4} required value={form.statement} onChange={(event) => setForm({ ...form, statement: event.target.value })} />
            <div className="form-row">
              <div><label htmlFor="claim-state">Evidence state</label><select id="claim-state" value={form.state} onChange={(event) => setForm({ ...form, state: event.target.value })}><option value="unknown">Unknown</option><option value="plausible">Plausible</option><option value="supported">Supported</option><option value="demonstrated">Demonstrated</option><option value="contradicted">Contradicted</option></select></div>
              <div><label htmlFor="claim-recommendation">Decision</label><select id="claim-recommendation" value={form.recommendation} onChange={(event) => setForm({ ...form, recommendation: event.target.value })}><option value="defer">Defer</option><option value="build">Build</option><option value="integrate">Integrate</option><option value="monitor">Monitor</option><option value="avoid">Avoid</option></select></div>
            </div>
            <label htmlFor="claim-summary">Evidence assessment</label><textarea id="claim-summary" rows={4} value={form.evidence_summary} onChange={(event) => setForm({ ...form, evidence_summary: event.target.value })} />
            <label htmlFor="claim-limitations">Contrary evidence and limitations</label><textarea id="claim-limitations" rows={3} value={form.limitations} onChange={(event) => setForm({ ...form, limitations: event.target.value })} />
            <label htmlFor="claim-assumptions">Material assumptions</label><textarea id="claim-assumptions" rows={3} value={form.assumptions} onChange={(event) => setForm({ ...form, assumptions: event.target.value })} />
            <label htmlFor="claim-reversal">What evidence would reverse this decision?</label><textarea id="claim-reversal" rows={3} value={form.reversal_conditions} onChange={(event) => setForm({ ...form, reversal_conditions: event.target.value })} />
            <label htmlFor="claim-outcome">Expected observable result</label><textarea id="claim-outcome" rows={3} value={form.expected_outcome} onChange={(event) => setForm({ ...form, expected_outcome: event.target.value })} />
            <div className="claim-score-input">
              <div><strong>Evidence score</strong><span>{formScore}/10 · {scoreGate(formScore).label}</span></div>
              <label htmlFor="claim-authority">Authority: {form.authority_score}/3</label><input id="claim-authority" type="range" min="0" max="3" value={form.authority_score} onChange={(event) => setForm({ ...form, authority_score: Number(event.target.value) })} />
              <label htmlFor="claim-directness">Directness: {form.directness_score}/3</label><input id="claim-directness" type="range" min="0" max="3" value={form.directness_score} onChange={(event) => setForm({ ...form, directness_score: Number(event.target.value) })} />
              <label htmlFor="claim-recency">Recency: {form.recency_score}/2</label><input id="claim-recency" type="range" min="0" max="2" value={form.recency_score} onChange={(event) => setForm({ ...form, recency_score: Number(event.target.value) })} />
              <label htmlFor="claim-triangulation">Triangulation: {form.triangulation_score}/2</label><input id="claim-triangulation" type="range" min="0" max="2" value={form.triangulation_score} onChange={(event) => setForm({ ...form, triangulation_score: Number(event.target.value) })} />
            </div>
            <div className="form-row">
              <div><label htmlFor="claim-relevance">Relevance</label><select id="claim-relevance" value={form.relevance} onChange={(event) => setForm({ ...form, relevance: event.target.value })}><option value="facilitation">Facilitation</option><option value="platform">Platform</option><option value="operations">Operations</option><option value="mixed">Mixed</option></select></div>
              <div><label htmlFor="claim-review">Review due</label><input id="claim-review" type="date" value={form.review_due_on} onChange={(event) => setForm({ ...form, review_due_on: event.target.value })} /></div>
            </div>
            <label htmlFor="claim-decision">Linked decision</label><select id="claim-decision" value={form.linked_decision_id} onChange={(event) => setForm({ ...form, linked_decision_id: event.target.value })}><option value="">No linked decision yet</option>{portfolio.data?.decisions.map((decision) => <option key={decision.id} value={decision.id}>{decision.title}</option>)}</select>
            <label htmlFor="claim-owner">Accountable owner</label><select id="claim-owner" value={form.owner_id} onChange={(event) => setForm({ ...form, owner_id: event.target.value })}><option value="">Me</option>{memberships.data?.filter((item) => item.status === "active").map((item) => <option key={item.user.id} value={item.user.id}>{personName(item.user)}</option>)}</select>
            <label htmlFor="claim-lifecycle">Workflow</label><select id="claim-lifecycle" value={form.lifecycle_status} onChange={(event) => setForm({ ...form, lifecycle_status: event.target.value })}><option value="draft">Draft</option><option value="active">Active</option></select>
            <button className="button button--primary button--full" type="submit" disabled={createClaim.isPending}>{createClaim.isPending ? "Saving…" : "Save research claim"}</button>
          </form>
        )}
      </aside>
    </div>
  );
}
