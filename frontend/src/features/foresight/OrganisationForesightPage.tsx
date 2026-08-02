import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { ForesightSignal } from "../../lib/types";
import { listMemberships } from "../organisations/api";
import { getOrganisationPortfolio } from "../portfolio/api";
import {
  addSignalToWatchlist,
  createFeed,
  createSignal,
  createSource,
  createWatchlist,
  getForesightOverview,
  linkSignalToDecision,
  listFeeds,
  listSignals,
  listSources,
  listWatchlists,
  syncFeed,
  updateSignal,
  uploadSourceAttachment,
} from "./api";

type Tab = "radar" | "signals" | "sources" | "watchlists";

const steepCategories: Array<{ value: ForesightSignal["steep_category"]; label: string }> = [
  { value: "social", label: "Social" },
  { value: "technological", label: "Technological" },
  { value: "economic", label: "Economic" },
  { value: "environmental", label: "Environmental" },
  { value: "political", label: "Political" },
  { value: "legal", label: "Legal" },
  { value: "ethical", label: "Ethical" },
];

function personName(user: { first_name: string; last_name: string; email: string }): string {
  return [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email;
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function OrganisationForesightPage() {
  const { organisationId = "" } = useParams<{ organisationId: string }>();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const focusedSignalId = searchParams.get("signal");
  const focusedSourceId = searchParams.get("source");
  const [tab, setTab] = useState<Tab>(focusedSourceId ? "sources" : focusedSignalId ? "signals" : "radar");
  const [signalQuery, setSignalQuery] = useState("");
  const [signalFilter, setSignalFilter] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceForm, setSourceForm] = useState({
    title: "",
    source_type: "research",
    author: "",
    publisher: "",
    published_on: "",
    source_url: "",
    reference: "",
    credibility: "unassessed",
    credibility_rationale: "",
    notes: "",
  });
  const [signalForm, setSignalForm] = useState({
    source_id: "",
    title: "",
    summary: "",
    future_implication: "",
    steep_category: "technological",
    time_horizon: "medium",
    maturity: "weak",
    polarity: "unclear",
    geography: "",
    domain: "",
    impact: 3,
    uncertainty: 3,
    status: "draft",
    owner_id: "",
  });
  const [watchlistForm, setWatchlistForm] = useState({ name: "", description: "", owner_id: "" });
  const [feedForm, setFeedForm] = useState({ name: "", feed_url: "", owner_id: "" });
  const [feedMessage, setFeedMessage] = useState("");
  const [decisionLink, setDecisionLink] = useState<Record<string, { decisionId: string; relevance: string }>>({});
  const [watchlistSelection, setWatchlistSelection] = useState<Record<string, string>>({});

  const overview = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "overview"],
    queryFn: () => getForesightOverview(organisationId),
    enabled: Boolean(organisationId),
  });
  const feeds = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "feeds"],
    queryFn: () => listFeeds(organisationId),
    enabled: Boolean(organisationId),
  });
  const sources = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "sources"],
    queryFn: () => listSources(organisationId),
    enabled: Boolean(organisationId),
  });
  const signals = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "signals"],
    queryFn: () => listSignals(organisationId),
    enabled: Boolean(organisationId),
  });
  const watchlists = useQuery({
    queryKey: ["organisations", organisationId, "foresight", "watchlists"],
    queryFn: () => listWatchlists(organisationId),
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
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "foresight"] }),
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "search"] }),
    ]);
  };

  const sourceCreate = useMutation({
    mutationFn: async () => {
      const source = await createSource(organisationId, {
        ...sourceForm,
        published_on: sourceForm.published_on || null,
        reference: sourceForm.reference || (selectedFile ? `Uploaded file: ${selectedFile.name}` : ""),
      });
      if (selectedFile) await uploadSourceAttachment(source.id, selectedFile);
      return source;
    },
    onSuccess: async () => {
      setSourceForm({ title: "", source_type: "research", author: "", publisher: "", published_on: "", source_url: "", reference: "", credibility: "unassessed", credibility_rationale: "", notes: "" });
      setSelectedFile(null);
      await refresh();
    },
  });

  const feedCreate = useMutation({
    mutationFn: () => createFeed(organisationId, {
      ...feedForm,
      owner_id: feedForm.owner_id || undefined,
    }),
    onSuccess: async () => {
      setFeedForm({ name: "", feed_url: "", owner_id: "" });
      setFeedMessage("Feed saved. Synchronise it when you are ready to import source items.");
      await refresh();
    },
  });
  const feedSync = useMutation({
    mutationFn: syncFeed,
    onSuccess: async (response) => {
      setFeedMessage(
        response.result.not_modified
          ? "The feed has not changed since its previous successful synchronisation."
          : `${response.result.created_sources} new source item(s) imported from ${response.result.entries_seen} feed entries.`,
      );
      await refresh();
    },
  });

  const signalCreate = useMutation({
    mutationFn: () => createSignal(organisationId, {
      ...signalForm,
      source_id: signalForm.source_id || null,
      owner_id: signalForm.owner_id || undefined,
    }),
    onSuccess: async () => {
      setSignalForm({ source_id: "", title: "", summary: "", future_implication: "", steep_category: "technological", time_horizon: "medium", maturity: "weak", polarity: "unclear", geography: "", domain: "", impact: 3, uncertainty: 3, status: "draft", owner_id: "" });
      await refresh();
    },
  });

  const signalStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateSignal(id, { status }),
    onSuccess: refresh,
  });
  const signalDecision = useMutation({
    mutationFn: ({ signalId, decisionId, relevance }: { signalId: string; decisionId: string; relevance: string }) => linkSignalToDecision(signalId, decisionId, relevance),
    onSuccess: refresh,
  });
  const watchlistCreate = useMutation({
    mutationFn: () => createWatchlist(organisationId, { ...watchlistForm, owner_id: watchlistForm.owner_id || undefined }),
    onSuccess: async () => {
      setWatchlistForm({ name: "", description: "", owner_id: "" });
      await refresh();
    },
  });
  const watchlistAdd = useMutation({
    mutationFn: ({ watchlistId, signalId }: { watchlistId: string; signalId: string }) => addSignalToWatchlist(watchlistId, signalId),
    onSuccess: refresh,
  });

  useEffect(() => {
    if (focusedSourceId) setTab("sources");
    if (focusedSignalId) setTab("signals");
  }, [focusedSignalId, focusedSourceId]);

  useEffect(() => {
    const recordId = focusedSourceId
      ? `source-${focusedSourceId}`
      : focusedSignalId
        ? `signal-${focusedSignalId}`
        : "";
    if (!recordId) return;
    const timer = window.setTimeout(() => {
      document.getElementById(recordId)?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 120);
    return () => window.clearTimeout(timer);
  }, [focusedSignalId, focusedSourceId, signals.data, sources.data, tab]);

  const filteredSignals = useMemo(() => {
    const needle = signalQuery.trim().toLowerCase();
    return (signals.data ?? []).filter((signal) => {
      const matchesText = !needle || `${signal.title} ${signal.summary} ${signal.future_implication} ${signal.domain} ${signal.geography}`.toLowerCase().includes(needle);
      const matchesCategory = !signalFilter || signal.steep_category === signalFilter;
      return matchesText && matchesCategory;
    });
  }, [signals.data, signalFilter, signalQuery]);

  const error = sourceCreate.error || feedCreate.error || feedSync.error || signalCreate.error || signalStatus.error || signalDecision.error || watchlistCreate.error || watchlistAdd.error;
  const canContribute = overview.data?.can_contribute ?? false;

  return (
    <div className="foresight-page">
      <Link className="back-link" to={`/organisations/${organisationId}`}>← Organisation</Link>
      <div className="page-heading foresight-heading">
        <div>
          <p className="eyebrow">Explore · strategic foresight</p>
          <h1>Signals and source intelligence</h1>
          <p className="muted">Detect change early, preserve source quality, monitor uncertainty, and connect emerging issues to accountable decisions.</p>
        </div>
        <div className="heading-actions"><Link className="button button--secondary" to={`/organisations/${organisationId}/foresight/canvases`}><Icon name="layers" /> Systems canvases</Link>{canContribute ? <button className="button button--primary" type="button" onClick={() => setTab("signals")}><Icon name="plus" /> Capture signal</button> : null}</div>
      </div>

      {error ? <StatusMessage kind="error">{error instanceof ApiError ? error.message : "The foresight action could not be completed."}</StatusMessage> : null}
      {overview.isError || signals.isError || sources.isError ? <StatusMessage kind="error">Foresight records could not be loaded.</StatusMessage> : null}

      <section className="foresight-metrics" aria-label="Foresight overview">
        <article><span>Signals</span><strong>{overview.data?.signal_count ?? "—"}</strong><small>active observations</small></article>
        <article><span>Sources</span><strong>{overview.data?.source_count ?? "—"}</strong><small>attributable records</small></article>
        <article><span>Watchlists</span><strong>{overview.data?.watchlist_count ?? "—"}</strong><small>strategic concerns</small></article>
        <article><span>Systems canvases</span><strong>{overview.data?.canvas_count ?? "—"}</strong><small>structured inquiries</small></article>
        <article className="foresight-metric--attention"><span>High attention</span><strong>{overview.data?.high_attention_count ?? "—"}</strong><small>high impact and uncertainty</small></article>
      </section>

      <div className="foresight-tabs" role="tablist" aria-label="Foresight sections">
        {(["radar", "signals", "sources", "watchlists"] as Tab[]).map((item) => (
          <button key={item} className={tab === item ? "is-active" : ""} type="button" role="tab" aria-selected={tab === item} onClick={() => setTab(item)}>{item === "radar" ? "Foresight radar" : item.charAt(0).toUpperCase() + item.slice(1)}</button>
        ))}
      </div>

      {tab === "radar" ? (
        <div className="foresight-radar-layout">
          <section className="page-primary foresight-radar-card">
            <div className="section-heading"><div><p className="eyebrow">Portfolio view</p><h2>STEEP signal radar</h2></div><span className="role-badge">Impact × uncertainty</span></div>
            <div className="steep-radar">
              {steepCategories.map((category) => {
                const categorySignals = (signals.data ?? []).filter((signal) => signal.steep_category === category.value && signal.status !== "retired");
                return (
                  <article key={category.value} className={`steep-sector steep-sector--${category.value}`}>
                    <header><strong>{category.label}</strong><span>{categorySignals.length}</span></header>
                    <div className="steep-sector__signals">
                      {categorySignals.slice(0, 5).map((signal) => (
                        <button type="button" key={signal.id} onClick={() => { setSignalQuery(signal.title); setTab("signals"); }} title={`${signal.title}: impact ${signal.impact}, uncertainty ${signal.uncertainty}`}>
                          <span className={`signal-dot signal-dot--${signal.maturity}`} style={{ width: `${8 + signal.impact * 2}px`, height: `${8 + signal.impact * 2}px` }} />
                          <span>{signal.title}</span>
                        </button>
                      ))}
                      {!categorySignals.length ? <small>No signals yet</small> : null}
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
          <aside className="side-panel foresight-horizon-panel">
            <p className="eyebrow">Time distribution</p>
            <h2>Strategic horizons</h2>
            {(["near", "medium", "long"] as const).map((horizon) => (
              <div className="horizon-row" key={horizon}>
                <div><strong>{horizon === "near" ? "0–2 years" : horizon === "medium" ? "3–5 years" : "6+ years"}</strong><small>{horizon} term</small></div>
                <span>{overview.data?.by_horizon[horizon] ?? 0}</span>
              </div>
            ))}
            <div className="foresight-principle"><Icon name="spark" /><p><strong>Foresight is not prediction.</strong> Signals help teams test assumptions and prepare adaptive choices across plausible futures.</p></div>
          </aside>
        </div>
      ) : null}

      {tab === "signals" ? (
        <div className="reasoning-grid foresight-workspace-grid">
          <section className="page-primary">
            <div className="section-heading"><div><p className="eyebrow">Emerging change</p><h2>Signal library</h2></div><span className="muted">{filteredSignals.length} shown</span></div>
            <div className="foresight-filterbar">
              <label className="visually-hidden" htmlFor="signal-search">Search signals</label>
              <input id="signal-search" type="search" placeholder="Search signals, implications, domains…" value={signalQuery} onChange={(event) => setSignalQuery(event.target.value)} />
              <select aria-label="Filter by STEEP category" value={signalFilter} onChange={(event) => setSignalFilter(event.target.value)}><option value="">All STEEP categories</option>{steepCategories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select>
            </div>
            <div className="signal-library">
              {filteredSignals.map((signal) => (
                <article id={`signal-${signal.id}`} className={`signal-card signal-card--${signal.polarity}${focusedSignalId === signal.id ? " is-focused" : ""}`} key={signal.id}>
                  <div className="signal-card__top"><div className="inline-badges"><span className="status-badge">{signal.steep_label}</span><span className="role-badge">{signal.horizon_label}</span><span className="role-badge">{signal.maturity_label}</span></div><strong className="signal-score">{signal.priority_score}<small> attention</small></strong></div>
                  <h3>{signal.title}</h3><p>{signal.summary}</p>
                  <div className="signal-implication"><span>Future implication</span><p>{signal.future_implication}</p></div>
                  <div className="signal-card__meta"><span>Impact {signal.impact}/5</span><span>Uncertainty {signal.uncertainty}/5</span><span>Owner: {personName(signal.owner)}</span>{signal.source_title ? <span>Source: {signal.source_title}</span> : null}</div>
                  {signal.linked_decisions.length ? <div className="signal-links"><strong>Informs</strong>{signal.linked_decisions.map((decision) => <Link key={decision.id} to={`/decisions/${decision.id}`} title={decision.relevance}>{decision.title}</Link>)}</div> : null}
                  {signal.can_edit ? (
                    <div className="signal-card__actions">
                      <select aria-label={`Status for ${signal.title}`} value={signal.status} onChange={(event) => signalStatus.mutate({ id: signal.id, status: event.target.value })}><option value="draft">Draft</option><option value="reviewed">Reviewed</option><option value="monitoring">Monitoring</option><option value="retired">Retired</option></select>
                      <select aria-label={`Watchlist for ${signal.title}`} value={watchlistSelection[signal.id] ?? ""} onChange={(event) => setWatchlistSelection((current) => ({ ...current, [signal.id]: event.target.value }))}><option value="">Add to watchlist…</option>{watchlists.data?.filter((item) => !signal.watchlists.some((linked) => linked.id === item.id)).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
                      {(() => { const watchlistId = watchlistSelection[signal.id] ?? ""; return <button className="button button--quiet" type="button" disabled={!watchlistId} onClick={() => { if (watchlistId) watchlistAdd.mutate({ watchlistId, signalId: signal.id }); }}>Add</button>; })()}
                    </div>
                  ) : null}
                  {signal.can_edit && portfolio.data?.decisions.length ? (
                    (() => {
                      const link = decisionLink[signal.id] ?? { decisionId: "", relevance: "" };
                      return <details className="signal-decision-linker"><summary>Connect to a decision</summary><select value={link.decisionId} onChange={(event) => setDecisionLink((current) => ({ ...current, [signal.id]: { decisionId: event.target.value, relevance: current[signal.id]?.relevance ?? "" } }))}><option value="">Choose decision</option>{portfolio.data.decisions.map((decision) => <option key={decision.id} value={decision.id}>{decision.title}</option>)}</select><textarea rows={2} placeholder="Explain how this signal affects the decision…" value={link.relevance} onChange={(event) => setDecisionLink((current) => ({ ...current, [signal.id]: { decisionId: current[signal.id]?.decisionId ?? "", relevance: event.target.value } }))} /><button className="button button--secondary" type="button" disabled={!link.decisionId || !link.relevance.trim()} onClick={() => { if (link.decisionId && link.relevance.trim()) signalDecision.mutate({ signalId: signal.id, decisionId: link.decisionId, relevance: link.relevance }); }}>Link decision</button></details>;
                    })()
                  ) : null}
                </article>
              ))}
              {!filteredSignals.length ? <div className="empty-state"><Icon name="spark" /><h3>No matching signals</h3><p>Capture a weak signal or change the filters.</p></div> : null}
            </div>
          </section>
          <aside className="side-panel foresight-create-panel">
            <p className="eyebrow">Capture observation</p><h2>New signal</h2><p className="muted">Separate what is observable now from what it may mean for the future.</p>
            {!canContribute ? <p className="muted">Your organisation role is read-only.</p> : (
              <form onSubmit={(event) => { event.preventDefault(); signalCreate.mutate(); }}>
                <label htmlFor="signal-title">Signal title</label><input id="signal-title" required value={signalForm.title} onChange={(event) => setSignalForm({ ...signalForm, title: event.target.value })} />
                <label htmlFor="signal-summary">What is changing?</label><textarea id="signal-summary" rows={4} required value={signalForm.summary} onChange={(event) => setSignalForm({ ...signalForm, summary: event.target.value })} />
                <label htmlFor="signal-implication">Why could it matter?</label><textarea id="signal-implication" rows={4} required value={signalForm.future_implication} onChange={(event) => setSignalForm({ ...signalForm, future_implication: event.target.value })} />
                <label htmlFor="signal-source">Structured source</label><select id="signal-source" value={signalForm.source_id} onChange={(event) => setSignalForm({ ...signalForm, source_id: event.target.value })}><option value="">No linked source yet</option>{sources.data?.filter((item) => item.status === "active").map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                <div className="form-row"><div><label htmlFor="signal-steep">STEEP category</label><select id="signal-steep" value={signalForm.steep_category} onChange={(event) => setSignalForm({ ...signalForm, steep_category: event.target.value })}>{steepCategories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div><div><label htmlFor="signal-horizon">Time horizon</label><select id="signal-horizon" value={signalForm.time_horizon} onChange={(event) => setSignalForm({ ...signalForm, time_horizon: event.target.value })}><option value="near">0–2 years</option><option value="medium">3–5 years</option><option value="long">6+ years</option></select></div></div>
                <div className="form-row"><div><label htmlFor="signal-maturity">Maturity</label><select id="signal-maturity" value={signalForm.maturity} onChange={(event) => setSignalForm({ ...signalForm, maturity: event.target.value })}><option value="weak">Weak signal</option><option value="emerging">Emerging pattern</option><option value="established">Established trend</option></select></div><div><label htmlFor="signal-polarity">Potential</label><select id="signal-polarity" value={signalForm.polarity} onChange={(event) => setSignalForm({ ...signalForm, polarity: event.target.value })}><option value="unclear">Unclear</option><option value="opportunity">Opportunity</option><option value="threat">Threat</option><option value="both">Both</option></select></div></div>
                <div className="form-row"><div><label htmlFor="signal-impact">Impact: {signalForm.impact}/5</label><input id="signal-impact" type="range" min="1" max="5" value={signalForm.impact} onChange={(event) => setSignalForm({ ...signalForm, impact: Number(event.target.value) })} /></div><div><label htmlFor="signal-uncertainty">Uncertainty: {signalForm.uncertainty}/5</label><input id="signal-uncertainty" type="range" min="1" max="5" value={signalForm.uncertainty} onChange={(event) => setSignalForm({ ...signalForm, uncertainty: Number(event.target.value) })} /></div></div>
                <label htmlFor="signal-domain">Domain</label><input id="signal-domain" placeholder="Agriculture, regulation, talent…" value={signalForm.domain} onChange={(event) => setSignalForm({ ...signalForm, domain: event.target.value })} />
                <label htmlFor="signal-geography">Geography</label><input id="signal-geography" placeholder="Global, Ireland, West Africa…" value={signalForm.geography} onChange={(event) => setSignalForm({ ...signalForm, geography: event.target.value })} />
                <label htmlFor="signal-owner">Accountable owner</label><select id="signal-owner" value={signalForm.owner_id} onChange={(event) => setSignalForm({ ...signalForm, owner_id: event.target.value })}><option value="">Me</option>{memberships.data?.filter((item) => item.status === "active").map((item) => <option key={item.user.id} value={item.user.id}>{personName(item.user)}</option>)}</select>
                <button className="button button--primary button--full" disabled={signalCreate.isPending} type="submit">{signalCreate.isPending ? "Saving…" : "Capture signal"}</button>
              </form>
            )}
          </aside>
        </div>
      ) : null}

      {tab === "sources" ? (
        <div className="reasoning-grid foresight-workspace-grid">
          <section className="page-primary"><p className="eyebrow">Evidence base</p><h2>Source library</h2><p className="muted">Preserve where intelligence came from, how credible it is, and the original private files.</p>
          <details className="feed-panel" open={Boolean(feeds.data?.length)}>
            <summary><div><strong>RSS and Atom feeds</strong><span>{feeds.data?.length ?? 0} configured</span></div></summary>
            <div className="feed-panel__body">
              <p className="muted">Synchronisation imports feed entries as unassessed sources. A person must still interpret an item before creating a signal.</p>
              {feedMessage ? <StatusMessage kind="success">{feedMessage}</StatusMessage> : null}
              <div className="feed-list">
                {feeds.data?.map((feed) => (
                  <article key={feed.id}>
                    <div><strong>{feed.name}</strong><a href={feed.feed_url} target="_blank" rel="noreferrer">{feed.feed_url}</a><small>{feed.last_success_at ? `Last successful sync ${new Date(feed.last_success_at).toLocaleString("en-GB")}` : "Not synchronised yet"}</small>{feed.last_error ? <span className="feed-error">{feed.last_error}</span> : null}</div>
                    {feed.can_edit ? <button className="button button--secondary" type="button" disabled={feedSync.isPending} onClick={() => feedSync.mutate(feed.id)}>{feedSync.isPending ? "Synchronising…" : "Synchronise"}</button> : null}
                  </article>
                ))}
                {!feeds.data?.length ? <p className="muted">No feeds configured.</p> : null}
              </div>
              {canContribute ? <form className="feed-form" onSubmit={(event) => { event.preventDefault(); feedCreate.mutate(); }}><div><label htmlFor="feed-name">Feed name</label><input id="feed-name" required value={feedForm.name} onChange={(event) => setFeedForm({ ...feedForm, name: event.target.value })} /></div><div><label htmlFor="feed-url">Public RSS or Atom URL</label><input id="feed-url" type="url" required placeholder="https://example.org/feed.xml" value={feedForm.feed_url} onChange={(event) => setFeedForm({ ...feedForm, feed_url: event.target.value })} /></div><div><label htmlFor="feed-owner">Owner</label><select id="feed-owner" value={feedForm.owner_id} onChange={(event) => setFeedForm({ ...feedForm, owner_id: event.target.value })}><option value="">Me</option>{memberships.data?.filter((item) => item.status === "active").map((item) => <option key={item.user.id} value={item.user.id}>{personName(item.user)}</option>)}</select></div><button className="button button--primary" type="submit" disabled={feedCreate.isPending}>{feedCreate.isPending ? "Saving…" : "Add feed"}</button></form> : null}
            </div>
          </details>
          <div className="source-library">{sources.data?.map((source) => <article id={`source-${source.id}`} className={`source-card${focusedSourceId === source.id ? " is-focused" : ""}`} key={source.id}><div><div className="inline-badges"><span className="status-badge">{source.source_type_label}</span><span className="role-badge">{source.credibility_label} credibility</span></div><h3>{source.title}</h3><p>{[source.author, source.publisher, source.published_on].filter(Boolean).join(" · ") || source.reference}</p>{source.credibility_rationale ? <p className="muted">{source.credibility_rationale}</p> : null}</div><div className="source-card__links">{source.source_url ? <a className="button button--quiet" href={source.source_url} target="_blank" rel="noreferrer"><Icon name="external" /> Open source</a> : null}{source.attachments.map((file) => <a className="attachment-link" key={file.id} href={file.download_url}><Icon name="external" /><span><strong>{file.original_name}</strong><small>{formatBytes(file.size_bytes)} · private</small></span></a>)}</div></article>)}{sources.data?.length === 0 ? <div className="empty-state"><Icon name="layers" /><h3>No sources recorded</h3><p>Add the source before interpreting it as a signal.</p></div> : null}</div></section>
          <aside className="side-panel foresight-create-panel"><p className="eyebrow">Attributable intelligence</p><h2>Add source</h2>{!canContribute ? <p className="muted">Your organisation role is read-only.</p> : <form onSubmit={(event) => { event.preventDefault(); sourceCreate.mutate(); }}><label htmlFor="source-title">Title</label><input id="source-title" required value={sourceForm.title} onChange={(event) => setSourceForm({ ...sourceForm, title: event.target.value })} /><div className="form-row"><div><label htmlFor="source-type">Type</label><select id="source-type" value={sourceForm.source_type} onChange={(event) => setSourceForm({ ...sourceForm, source_type: event.target.value })}><option value="research">Research publication</option><option value="news">News or media</option><option value="government">Government or regulation</option><option value="internal">Internal record</option><option value="expert">Expert contribution</option><option value="stakeholder">Stakeholder contribution</option><option value="dataset">Dataset</option><option value="other">Other</option></select></div><div><label htmlFor="source-date">Published</label><input id="source-date" type="date" value={sourceForm.published_on} onChange={(event) => setSourceForm({ ...sourceForm, published_on: event.target.value })} /></div></div><label htmlFor="source-author">Author</label><input id="source-author" value={sourceForm.author} onChange={(event) => setSourceForm({ ...sourceForm, author: event.target.value })} /><label htmlFor="source-publisher">Publisher</label><input id="source-publisher" value={sourceForm.publisher} onChange={(event) => setSourceForm({ ...sourceForm, publisher: event.target.value })} /><label htmlFor="source-url">URL</label><input id="source-url" type="url" placeholder="https://…" value={sourceForm.source_url} onChange={(event) => setSourceForm({ ...sourceForm, source_url: event.target.value })} /><label htmlFor="source-reference">Reference</label><input id="source-reference" placeholder="Report ID, dataset version, interview…" value={sourceForm.reference} onChange={(event) => setSourceForm({ ...sourceForm, reference: event.target.value })} /><label htmlFor="source-credibility">Credibility assessment</label><select id="source-credibility" value={sourceForm.credibility} onChange={(event) => setSourceForm({ ...sourceForm, credibility: event.target.value })}><option value="unassessed">Not assessed</option><option value="low">Low</option><option value="moderate">Moderate</option><option value="high">High</option></select><label htmlFor="source-rationale">Assessment rationale</label><textarea id="source-rationale" rows={3} value={sourceForm.credibility_rationale} onChange={(event) => setSourceForm({ ...sourceForm, credibility_rationale: event.target.value })} /><label htmlFor="source-file">Private attachment</label><input id="source-file" type="file" accept=".pdf,.txt,.csv,.docx,.xlsx,.png,.jpg,.jpeg,.webp" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} /><small>Maximum 15 MB. Files are permission-controlled and never served as public media.</small><button className="button button--primary button--full" disabled={sourceCreate.isPending || (!sourceForm.source_url && !sourceForm.reference && !selectedFile)} type="submit">{sourceCreate.isPending ? "Saving…" : "Save source"}</button></form>}</aside>
        </div>
      ) : null}

      {tab === "watchlists" ? (
        <div className="reasoning-grid foresight-workspace-grid"><section className="page-primary"><p className="eyebrow">Persistent attention</p><h2>Strategic watchlists</h2><div className="watchlist-grid">{watchlists.data?.map((watchlist) => <article className="watchlist-card" key={watchlist.id}><div className="watchlist-card__heading"><div><h3>{watchlist.name}</h3><p>{watchlist.description || "No description recorded."}</p></div><span>{watchlist.signal_count}</span></div><p className="table-secondary">Owner: {personName(watchlist.owner)}</p><div className="watchlist-signals">{watchlist.signals.map((signal) => <button key={signal.id} type="button" onClick={() => { setSignalQuery(signal.title); setTab("signals"); }}><strong>{signal.title}</strong><small>{signal.steep_category} · {signal.time_horizon} · attention {signal.priority_score}</small></button>)}{!watchlist.signals.length ? <small>No signals added yet.</small> : null}</div></article>)}{watchlists.data?.length === 0 ? <div className="empty-state"><Icon name="activity" /><h3>No watchlists</h3><p>Create one for a strategic concern that needs continuing attention.</p></div> : null}</div></section><aside className="side-panel foresight-create-panel"><p className="eyebrow">Monitoring frame</p><h2>Create watchlist</h2>{!canContribute ? <p className="muted">Your organisation role is read-only.</p> : <form onSubmit={(event) => { event.preventDefault(); watchlistCreate.mutate(); }}><label htmlFor="watchlist-name">Name</label><input id="watchlist-name" required value={watchlistForm.name} onChange={(event) => setWatchlistForm({ ...watchlistForm, name: event.target.value })} /><label htmlFor="watchlist-description">What should this watchlist help the organisation notice?</label><textarea id="watchlist-description" rows={5} value={watchlistForm.description} onChange={(event) => setWatchlistForm({ ...watchlistForm, description: event.target.value })} /><label htmlFor="watchlist-owner">Accountable owner</label><select id="watchlist-owner" value={watchlistForm.owner_id} onChange={(event) => setWatchlistForm({ ...watchlistForm, owner_id: event.target.value })}><option value="">Me</option>{memberships.data?.filter((item) => item.status === "active").map((item) => <option key={item.user.id} value={item.user.id}>{personName(item.user)}</option>)}</select><button className="button button--primary button--full" disabled={watchlistCreate.isPending} type="submit">{watchlistCreate.isPending ? "Saving…" : "Create watchlist"}</button></form>}</aside></div>
      ) : null}
    </div>
  );
}
