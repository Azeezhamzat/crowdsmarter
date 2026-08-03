import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { contactChannels } from "../../config/contact";
import { fetchCurrentUser } from "../auth/api";
import {
  changePlatformAdministrator,
  changePlatformUserState,
  clearAIProviderAPIKey,
  getPlatformConfiguration,
  getPlatformOverview,
  listPlatformAudit,
  listPlatformDemoRequests,
  listPlatformOrganisations,
  listPlatformUsers,
  setAIProvider,
  setAIProviderAPIKey,
  updatePlatformConfiguration,
  updatePlatformDemoRequestStatus,
} from "./api";
import type { AIProviderKey, PlatformContactSettings, PlatformDemoRequest, PlatformUser } from "./types";

type AdminTab = "overview" | "organisations" | "users" | "demos" | "configuration" | "audit";

const tabs: Array<{ id: AdminTab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "organisations", label: "Organisations" },
  { id: "users", label: "Users" },
  { id: "demos", label: "Demo requests" },
  { id: "configuration", label: "Platform settings" },
  { id: "audit", label: "Audit" },
];

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function OverviewPanel() {
  const overview = useQuery({ queryKey: ["platform-admin", "overview"], queryFn: getPlatformOverview });
  if (overview.isPending) return <p>Loading platform overview…</p>;
  if (overview.isError || !overview.data) return <StatusMessage kind="error">The platform overview could not be loaded.</StatusMessage>;
  const counts = overview.data.counts;
  const metrics = [
    ["Organisations", counts.organisations],
    ["Active decisions", counts.active_decisions],
    ["Active users", counts.active_users],
    ["New demo requests", counts.new_demo_requests],
    ["Pending invitations", counts.pending_invitations],
    ["Active support sessions", counts.active_support_access],
  ];
  return <div className="platform-admin-stack">
    <div className="platform-metric-grid">{metrics.map(([label, value]) => <article className="platform-metric" key={String(label)}><strong>{value}</strong><span>{label}</span></article>)}</div>
    <div className="platform-admin-grid platform-admin-grid--two">
      <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Support access</p><h2>Active tenant sessions</h2></div></div>{overview.data.active_support_access.length ? <div className="platform-list">{overview.data.active_support_access.map((item) => <article key={item.id}><strong>{item.organisation_name}</strong><span>{item.administrator.email} · {item.access_level.replace("_", " ")}</span><small>Expires {formatDate(item.expires_at)}</small></article>)}</div> : <p className="muted">No active support-access sessions.</p>}</section>
      <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Prospective clients</p><h2>Recent demo requests</h2></div></div>{overview.data.recent_demo_requests.length ? <div className="platform-list">{overview.data.recent_demo_requests.map((item) => <article key={item.id}><strong>{item.organisation_name}</strong><span>{item.full_name} · {item.primary_need_label}</span><small>{item.status} · {formatDate(item.created_at)}</small></article>)}</div> : <p className="muted">No demo requests have been received.</p>}</section>
    </div>
    <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Audit</p><h2>Recent platform and tenant events</h2></div></div><div className="table-wrap"><table><thead><tr><th>Action</th><th>Actor</th><th>Object</th><th>Date</th></tr></thead><tbody>{overview.data.recent_audit_events.map((item) => <tr key={item.id}><td><code>{item.action}</code></td><td>{item.actor?.email ?? "System"}</td><td>{item.object_type} / {item.object_id.slice(0, 8)}</td><td>{formatDate(item.created_at)}</td></tr>)}</tbody></table></div></section>
  </div>;
}

function OrganisationsPanel() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const organisations = useQuery({ queryKey: ["platform-admin", "organisations", query, status], queryFn: () => listPlatformOrganisations({ q: query, status }) });
  return <section className="card-panel">
    <div className="section-heading"><div><p className="eyebrow">Tenant directory</p><h2>All organisations</h2><p className="muted">Summary visibility does not create membership. Opening tenant details requires a recorded, expiring support-access grant.</p></div></div>
    <div className="platform-filter-row"><label>Search<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name, slug, owner email" /></label><label>Status<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All</option><option value="active">Active</option><option value="deactivated">Deactivated</option></select></label></div>
    {organisations.isPending ? <p>Loading organisations…</p> : organisations.isError ? <StatusMessage kind="error">The organisation directory could not be loaded.</StatusMessage> : <div className="table-wrap"><table><thead><tr><th>Organisation</th><th>Owners</th><th>Members</th><th>Decisions</th><th>Status</th><th /></tr></thead><tbody>{organisations.data?.map((item) => <tr key={item.id}><td><strong>{item.name}</strong><small className="table-subline">{item.slug}</small></td><td>{item.owners.map((owner) => owner.email).join(", ") || "No active owner"}</td><td>{item.member_count}</td><td>{item.active_decision_count} active / {item.decision_count} total</td><td><span className={`status-pill status-pill--${item.status}`}>{item.status}</span></td><td><Link className="button button--secondary button--compact" to={`/platform-admin/organisations/${item.id}`}>Open support workspace</Link></td></tr>)}</tbody></table></div>}
  </section>;
}

function UserAction({ user }: { user: PlatformUser }) {
  const queryClient = useQueryClient();
  const [rationale, setRationale] = useState("");
  const stateMutation = useMutation({ mutationFn: () => changePlatformUserState(user.id, { is_active: !user.is_active, rationale }), onSuccess: async () => { setRationale(""); await queryClient.invalidateQueries({ queryKey: ["platform-admin"] }); } });
  const adminMutation = useMutation({ mutationFn: (action: "grant" | "suspend") => changePlatformAdministrator(user.id, { action, rationale }), onSuccess: async () => { setRationale(""); await queryClient.invalidateQueries({ queryKey: ["platform-admin"] }); } });
  const error = stateMutation.error || adminMutation.error;
  return <details className="platform-action-details"><summary>Manage</summary><label>Recorded rationale<textarea rows={2} value={rationale} onChange={(event) => setRationale(event.target.value)} placeholder="Why is this change required?" /></label>{error ? <StatusMessage kind="error">The user change failed.</StatusMessage> : null}<div className="button-row"><button className="button button--secondary button--compact" type="button" disabled={rationale.trim().length < 12 || stateMutation.isPending} onClick={() => stateMutation.mutate()}>{user.is_active ? "Suspend account" : "Reactivate account"}</button><button className="button button--secondary button--compact" type="button" disabled={rationale.trim().length < 12 || adminMutation.isPending} onClick={() => adminMutation.mutate(user.is_platform_administrator ? "suspend" : "grant")}>{user.is_platform_administrator ? "Suspend platform capability" : "Grant platform capability"}</button></div></details>;
}

function UsersPanel() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState("");
  const users = useQuery({ queryKey: ["platform-admin", "users", query, state], queryFn: () => listPlatformUsers({ q: query, state }) });
  return <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Identity administration</p><h2>User accounts and platform capability</h2><p className="muted">Django staff and superuser flags remain visible but are not the CrowdSmarter product-authority model.</p></div></div><div className="platform-filter-row"><label>Search<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Email or name" /></label><label>State<select value={state} onChange={(event) => setState(event.target.value)}><option value="">All</option><option value="active">Active</option><option value="suspended">Suspended</option><option value="platform_admin">Platform administrators</option></select></label></div>{users.isPending ? <p>Loading users…</p> : users.isError ? <StatusMessage kind="error">The user directory could not be loaded.</StatusMessage> : <div className="table-wrap"><table><thead><tr><th>User</th><th>Tenant roles</th><th>Platform authority</th><th>Technical flags</th><th>Status</th><th /></tr></thead><tbody>{users.data?.map((user) => <tr key={user.id}><td><strong>{user.email}</strong><small className="table-subline">{[user.first_name, user.last_name].filter(Boolean).join(" ") || "No profile name"}</small></td><td>{user.organisation_count} organisations · {user.active_owned_organisation_count} owned</td><td>{user.is_platform_administrator ? <span className="status-pill status-pill--active">Platform administrator</span> : "Standard user"}</td><td>{user.is_staff ? "staff" : "—"}{user.is_superuser ? " · superuser" : ""}</td><td>{user.is_active ? "active" : "suspended"}</td><td><UserAction user={user} /></td></tr>)}</tbody></table></div>}</section>;
}

function DemoAction({ item }: { item: PlatformDemoRequest }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<PlatformDemoRequest["status"]>(item.status);
  const [rationale, setRationale] = useState("");
  const mutation = useMutation({ mutationFn: () => updatePlatformDemoRequestStatus(item.id, { status, rationale }), onSuccess: async () => { setRationale(""); await queryClient.invalidateQueries({ queryKey: ["platform-admin"] }); } });
  return <details className="platform-action-details"><summary>Update</summary><label>Status<select value={status} onChange={(event) => setStatus(event.target.value as PlatformDemoRequest["status"])}><option value="new">New</option><option value="contacted">Contacted</option><option value="qualified">Qualified</option><option value="closed">Closed</option></select></label><label>Rationale<textarea rows={2} value={rationale} onChange={(event) => setRationale(event.target.value)} /></label><button className="button button--secondary button--compact" type="button" disabled={rationale.trim().length < 12 || mutation.isPending} onClick={() => mutation.mutate()}>Save status</button></details>;
}

function DemoRequestsPanel() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const demos = useQuery({ queryKey: ["platform-admin", "demos", query, status], queryFn: () => listPlatformDemoRequests({ q: query, status }) });
  return <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Commercial operations</p><h2>Demo requests</h2></div></div><div className="platform-filter-row"><label>Search<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Person, email or organisation" /></label><label>Status<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All</option><option value="new">New</option><option value="contacted">Contacted</option><option value="qualified">Qualified</option><option value="closed">Closed</option></select></label></div>{demos.isPending ? <p>Loading demo requests…</p> : demos.isError ? <StatusMessage kind="error">Demo requests could not be loaded.</StatusMessage> : <div className="table-wrap"><table><thead><tr><th>Prospect</th><th>Need</th><th>Context</th><th>Status</th><th>Received</th><th /></tr></thead><tbody>{demos.data?.map((item) => <tr key={item.id}><td><strong>{item.organisation_name}</strong><small className="table-subline">{item.full_name} · <a href={`mailto:${item.work_email}`}>{item.work_email}</a></small></td><td>{item.primary_need_label}<small className="table-subline">{item.organisation_size_label}</small></td><td className="platform-table-context">{item.message || "No additional context"}</td><td>{item.status}</td><td>{formatDate(item.created_at)}</td><td><DemoAction item={item} /></td></tr>)}</tbody></table></div>}</section>;
}

function ConfigurationPanel() {
  const queryClient = useQueryClient();
  const configuration = useQuery({ queryKey: ["platform-admin", "configuration"], queryFn: getPlatformConfiguration });
  const [form, setForm] = useState<(PlatformContactSettings & { rationale: string }) | null>(null);
  useEffect(() => { if (configuration.data) setForm({ public_contact_email: configuration.data.public_contact_email, demo_email: configuration.data.demo_email, support_email: configuration.data.support_email, privacy_email: configuration.data.privacy_email, security_email: configuration.data.security_email, notification_sender_email: configuration.data.notification_sender_email, support_access_max_hours: configuration.data.support_access_max_hours, rationale: "" }); }, [configuration.data]);
  const mutation = useMutation({ mutationFn: () => updatePlatformConfiguration(form!), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["platform-admin", "configuration"] }); } });
  if (configuration.isPending || !form) return <p>Loading platform settings…</p>;
  if (configuration.isError) return <StatusMessage kind="error">Platform settings could not be loaded.</StatusMessage>;
  const emailFields: Array<[keyof Omit<PlatformContactSettings, "support_access_max_hours">, string]> = [["public_contact_email", "General enquiries"], ["demo_email", "Demo requests"], ["support_email", "Customer support"], ["privacy_email", "Privacy requests"], ["security_email", "Security reports"], ["notification_sender_email", "Notification sender"]];
  return <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Official channels</p><h2>Contact and support policy</h2><p className="muted">These values are centrally governed and exposed through the public configuration endpoint. All aliases may initially route to hello@crowdsmarter.com.</p></div></div>{mutation.isSuccess ? <StatusMessage kind="success">Platform settings saved.</StatusMessage> : null}{mutation.isError ? <StatusMessage kind="error">Platform settings could not be saved.</StatusMessage> : null}<div className="form-grid form-grid--two">{emailFields.map(([field, label]) => <label key={field}>{label}<input type="email" value={String(form[field])} onChange={(event) => setForm({ ...form, [field]: event.target.value })} /></label>)}<label>Maximum support-access duration<input type="number" min={1} max={72} value={form.support_access_max_hours} onChange={(event) => setForm({ ...form, support_access_max_hours: Number(event.target.value) })} /><small>Hours; each access still requires a recorded reason.</small></label><label>Change rationale<textarea rows={3} value={form.rationale} onChange={(event) => setForm({ ...form, rationale: event.target.value })} /></label></div><button className="button button--primary" type="button" disabled={form.rationale.trim().length < 12 || mutation.isPending} onClick={() => mutation.mutate()}>{mutation.isPending ? "Saving…" : "Save platform settings"}</button></section>;
}

function AIProviderPanel() {
  const queryClient = useQueryClient();
  const configuration = useQuery({ queryKey: ["platform-admin", "configuration"], queryFn: getPlatformConfiguration });
  const [providerKey, setProviderKey] = useState<AIProviderKey>("rules");
  const [model, setModel] = useState("claude-sonnet-5");
  const [providerRationale, setProviderRationale] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [keyRationale, setKeyRationale] = useState("");
  const [clearRationale, setClearRationale] = useState("");
  useEffect(() => { if (configuration.data) { setProviderKey(configuration.data.ai_provider_key); setModel(configuration.data.ai_provider_model); } }, [configuration.data]);
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["platform-admin", "configuration"] });
  const providerMutation = useMutation({ mutationFn: () => setAIProvider({ provider_key: providerKey, model, rationale: providerRationale }), onSuccess: async () => { setProviderRationale(""); await refresh(); } });
  const keyMutation = useMutation({ mutationFn: () => setAIProviderAPIKey({ api_key: apiKey, rationale: keyRationale }), onSuccess: async () => { setApiKey(""); setKeyRationale(""); await refresh(); } });
  const clearMutation = useMutation({ mutationFn: () => clearAIProviderAPIKey({ rationale: clearRationale }), onSuccess: async () => { setClearRationale(""); await refresh(); } });
  if (configuration.isPending) return <p>Loading AI provider settings…</p>;
  if (configuration.isError || !configuration.data) return <StatusMessage kind="error">AI provider settings could not be loaded.</StatusMessage>;
  const data = configuration.data;
  return <section className="card-panel">
    <div className="section-heading"><div><p className="eyebrow">Decision reviews</p><h2>AI provider</h2><p className="muted">The rule-based reviewer needs no external service or key. Switching to a real model sends decision content to that provider and requires an API key.</p></div></div>
    {providerMutation.isError ? <StatusMessage kind="error">The provider choice could not be saved.</StatusMessage> : null}
    {keyMutation.isError ? <StatusMessage kind="error">The API key could not be saved.</StatusMessage> : null}
    {clearMutation.isError ? <StatusMessage kind="error">The API key could not be removed.</StatusMessage> : null}
    {keyMutation.isSuccess ? <StatusMessage kind="success">API key saved.</StatusMessage> : null}
    <div className="ai-quality-metrics">
      <article><strong>{data.ai_provider_key_label}</strong><span>Active provider</span></article>
      <article><strong>{data.ai_provider_api_key_is_set ? "Configured" : "Not set"}</strong><span>API key</span></article>
      <article><strong>{data.ai_provider_model}</strong><span>Model</span></article>
    </div>
    <div className="form-grid form-grid--two">
      <label>Provider<select value={providerKey} onChange={(event) => setProviderKey(event.target.value as AIProviderKey)}><option value="rules">Transparent rules (no external service)</option><option value="anthropic">Anthropic Claude</option></select></label>
      <label>Model identifier<input value={model} onChange={(event) => setModel(event.target.value)} placeholder="claude-sonnet-5" /><small>e.g. claude-sonnet-5, claude-haiku-4-5-20251001</small></label>
      <label>Change rationale<textarea rows={2} value={providerRationale} onChange={(event) => setProviderRationale(event.target.value)} /></label>
    </div>
    {providerKey === "anthropic" && !data.ai_provider_api_key_is_set ? <p className="field-hint">Set an API key below before selecting Anthropic.</p> : null}
    <button className="button button--primary" type="button" disabled={providerRationale.trim().length < 12 || providerMutation.isPending} onClick={() => providerMutation.mutate()}>{providerMutation.isPending ? "Saving…" : "Save provider choice"}</button>

    <div className="section-heading"><div><p className="eyebrow">Credential</p><h2>Anthropic API key</h2><p className="muted">Stored encrypted. It is never shown again once saved, including to other platform administrators.</p></div></div>
    <div className="form-grid form-grid--two">
      <label>API key<input type="password" autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder={data.ai_provider_api_key_is_set ? "Already configured — enter a new key to replace it" : "sk-ant-…"} /></label>
      <label>Change rationale<textarea rows={2} value={keyRationale} onChange={(event) => setKeyRationale(event.target.value)} /></label>
    </div>
    <button className="button button--secondary" type="button" disabled={!apiKey.trim() || keyRationale.trim().length < 12 || keyMutation.isPending} onClick={() => keyMutation.mutate()}>{keyMutation.isPending ? "Saving…" : "Set API key"}</button>

    {data.ai_provider_api_key_is_set ? <>
      <div className="form-grid form-grid--two">
        <label>Reason for removing the key<textarea rows={2} value={clearRationale} onChange={(event) => setClearRationale(event.target.value)} /></label>
      </div>
      <button className="button button--danger" type="button" disabled={clearRationale.trim().length < 12 || clearMutation.isPending} onClick={() => { if (window.confirm("Remove the configured API key? This reverts to the rules-based reviewer if Anthropic is active.")) clearMutation.mutate(); }}>{clearMutation.isPending ? "Removing…" : "Remove API key"}</button>
    </> : null}
  </section>;
}

function AuditPanel() {
  const [query, setQuery] = useState("");
  const audit = useQuery({ queryKey: ["platform-admin", "audit", query], queryFn: () => listPlatformAudit({ q: query }) });
  return <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Accountability</p><h2>Platform and tenant audit</h2><p className="muted">Support access, ownership, user-state and configuration changes are attributable and append-only.</p></div></div><label className="platform-search-label">Search audit<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Action, actor, organisation or object" /></label>{audit.isPending ? <p>Loading audit events…</p> : audit.isError ? <StatusMessage kind="error">Audit events could not be loaded.</StatusMessage> : <div className="table-wrap"><table><thead><tr><th>Action</th><th>Actor</th><th>Object</th><th>Metadata</th><th>Date</th></tr></thead><tbody>{audit.data?.map((item) => <tr key={item.id}><td><code>{item.action}</code></td><td>{item.actor?.email ?? "System"}</td><td>{item.object_type}<small className="table-subline">{item.object_id}</small></td><td className="platform-audit-metadata">{JSON.stringify(item.metadata)}</td><td>{formatDate(item.created_at)}</td></tr>)}</tbody></table></div>}</section>;
}

export function PlatformAdminPage() {
  const currentUser = useQuery({ queryKey: ["current-user"], queryFn: fetchCurrentUser, staleTime: 60_000 });
  const [activeTab, setActiveTab] = useState<AdminTab>("overview");
  if (currentUser.isPending) return <p>Checking platform authority…</p>;
  if (currentUser.isError || !currentUser.data?.is_platform_administrator) return <StatusMessage kind="error">This workspace requires an active CrowdSmarter platform-administrator capability.</StatusMessage>;
  return <div className="platform-admin-page"><div className="page-heading"><div><p className="eyebrow">Platform administration</p><h1>Tenant governance and operational control</h1><p className="muted">Manage the service without silently joining client decisions. Tenant detail access is reasoned, time-bounded and audited.</p></div><a className="button button--secondary" href={contactChannels.adminUrl} target="_blank" rel="noreferrer">Technical Django admin</a></div><nav className="platform-admin-tabs" aria-label="Platform administration sections">{tabs.map((tab) => <button key={tab.id} className={activeTab === tab.id ? "is-active" : ""} type="button" aria-current={activeTab === tab.id ? "page" : undefined} onClick={() => setActiveTab(tab.id)}>{tab.label}</button>)}</nav>{activeTab === "overview" ? <OverviewPanel /> : null}{activeTab === "organisations" ? <OrganisationsPanel /> : null}{activeTab === "users" ? <UsersPanel /> : null}{activeTab === "demos" ? <DemoRequestsPanel /> : null}{activeTab === "configuration" ? <><ConfigurationPanel /><AIProviderPanel /></> : null}{activeTab === "audit" ? <AuditPanel /> : null}</div>;
}
