import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { fetchCurrentUser } from "../auth/api";
import {
  changePlatformInvitation,
  changePlatformOrganisationState,
  createSupportAccess,
  getPlatformOrganisation,
  listPlatformOrganisations,
  revokeSupportAccess,
  transferPlatformOwnership,
} from "./api";
import type { PlatformInvitation, PlatformOrganisationDetail } from "./types";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function SupportAccessGate({ organisationId, organisationName }: { organisationId: string; organisationName: string }) {
  const queryClient = useQueryClient();
  const [accessLevel, setAccessLevel] = useState<"read_only" | "operational">("read_only");
  const [duration, setDuration] = useState(2);
  const [reason, setReason] = useState("");
  const mutation = useMutation({
    mutationFn: () => createSupportAccess(organisationId, { access_level: accessLevel, reason, duration_hours: duration }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["platform-admin", "organisation", organisationId] });
    },
  });
  return <section className="card-panel platform-support-gate"><p className="eyebrow">Support-access gate</p><h1>Record access before opening {organisationName}</h1><p className="muted">Platform authority provides oversight, not invisible tenant membership. A grant records why access is needed, its scope, and when it expires.</p>{mutation.isError ? <StatusMessage kind="error">{mutation.error instanceof ApiError ? mutation.error.message : "Support access could not be created."}</StatusMessage> : null}<div className="form-grid form-grid--two"><label>Access level<select value={accessLevel} onChange={(event) => setAccessLevel(event.target.value as "read_only" | "operational")}><option value="read_only">Read-only support</option><option value="operational">Operational support</option></select><small>Operational access is required for ownership, account-state and invitation actions.</small></label><label>Duration<input type="number" min={1} max={72} value={duration} onChange={(event) => setDuration(Number(event.target.value))} /><small>Hours; the configured platform maximum is enforced by the server.</small></label></div><label>Specific reason<textarea rows={4} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Describe the customer request, incident, or operational task that justifies access." /></label><button className="button button--primary" type="button" disabled={reason.trim().length < 12 || mutation.isPending} onClick={() => mutation.mutate()}>{mutation.isPending ? "Recording access…" : "Open governed support workspace"}</button></section>;
}

function InvitationAction({ item, operational, onSuccess }: { item: PlatformInvitation; operational: boolean; onSuccess: () => Promise<void> }) {
  const [rationale, setRationale] = useState("");
  const mutation = useMutation({ mutationFn: (action: "resend" | "revoke") => changePlatformInvitation(item.id, { action, rationale }), onSuccess });
  return <details className="platform-action-details"><summary>Manage</summary><label>Rationale<textarea rows={2} value={rationale} onChange={(event) => setRationale(event.target.value)} /></label>{mutation.isError ? <StatusMessage kind="error">Invitation action failed.</StatusMessage> : null}<div className="button-row"><button className="button button--secondary button--compact" type="button" disabled={!operational || rationale.trim().length < 12 || item.effective_status !== "pending" || mutation.isPending} onClick={() => mutation.mutate("resend")}>Resend</button><button className="button button--danger button--compact" type="button" disabled={!operational || rationale.trim().length < 12 || item.effective_status !== "pending" || mutation.isPending} onClick={() => mutation.mutate("revoke")}>Revoke</button></div></details>;
}

function SupportWorkspace({ item }: { item: PlatformOrganisationDetail }) {
  const queryClient = useQueryClient();
  const grant = item.current_support_access;
  const operational = grant?.access_level === "operational";
  const [revokeRationale, setRevokeRationale] = useState("");
  const [ownership, setOwnership] = useState({ target_membership_id: "", rationale: "", confirmation: "", demote_existing_owners: true });
  const [stateChange, setStateChange] = useState({ rationale: "", confirmation: "" });
  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["platform-admin", "organisation", item.id] }),
      queryClient.invalidateQueries({ queryKey: ["platform-admin", "organisations"] }),
      queryClient.invalidateQueries({ queryKey: ["platform-admin", "overview"] }),
    ]);
  };
  const revoke = useMutation({ mutationFn: () => revokeSupportAccess(grant!.id, revokeRationale), onSuccess: refresh });
  const transfer = useMutation({ mutationFn: () => transferPlatformOwnership(item.id, ownership), onSuccess: async () => { setOwnership({ target_membership_id: "", rationale: "", confirmation: "", demote_existing_owners: true }); await refresh(); } });
  const stateMutation = useMutation({ mutationFn: () => changePlatformOrganisationState(item.id, { action: item.status === "active" ? "deactivate" : "reactivate", ...stateChange }), onSuccess: refresh });
  const ownerCandidates = item.memberships.filter((membership) => membership.status === "active");
  return <div className="platform-admin-stack">
    {grant ? <section className={`platform-support-banner platform-support-banner--${grant.access_level}`} role="status"><div><p className="eyebrow">Governed support access</p><h2>{grant.access_level === "operational" ? "Operational support session" : "Read-only support session"}</h2><p>{grant.reason}</p><small>Opened by {grant.administrator.email} · expires {formatDate(grant.expires_at)}</small></div><details className="platform-action-details platform-action-details--banner"><summary>End session</summary><label>Revocation rationale<textarea rows={2} value={revokeRationale} onChange={(event) => setRevokeRationale(event.target.value)} /></label><button className="button button--secondary button--compact" type="button" disabled={revokeRationale.trim().length < 12 || revoke.isPending} onClick={() => revoke.mutate()}>Revoke access</button></details></section> : null}
    <div className="platform-metric-grid"><article className="platform-metric"><strong>{item.member_count}</strong><span>Active members</span></article><article className="platform-metric"><strong>{item.active_owner_count}</strong><span>Active owners</span></article><article className="platform-metric"><strong>{item.workspace_count}</strong><span>Workspaces</span></article><article className="platform-metric"><strong>{item.active_decision_count}</strong><span>Active decisions</span></article></div>
    <div className="platform-admin-grid platform-admin-grid--two"><section className="card-panel"><p className="eyebrow">Tenant identity</p><h2>{item.brand_name || item.name}</h2><p>{item.description || "No organisation description."}</p><dl className="platform-definition-list"><div><dt>Slug</dt><dd>{item.slug}</dd></div><div><dt>Status</dt><dd>{item.status}</dd></div><div><dt>Website</dt><dd>{item.website_url ? <a href={item.website_url} target="_blank" rel="noreferrer">{item.website_url}</a> : "—"}</dd></div><div><dt>Retention</dt><dd>{item.retention_days ? `${item.retention_days} days` : "Default policy"}</dd></div></dl></section><section className="card-panel"><p className="eyebrow">Privacy boundary</p><h2>What this session permits</h2><p className="muted">This support workspace exposes administrative context without adding you to the organisation, workspaces, participants, evaluations, or contribution records.</p><ul className="platform-policy-list"><li>Every access session has a reason and expiry.</li><li>Operational actions require the stronger access level.</li><li>All actions are recorded in the append-only audit trail.</li><li>Client contributions are never attributed to the platform administrator.</li></ul></section></div>
    <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Membership</p><h2>Owners and members</h2></div></div><div className="table-wrap"><table><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Joined</th></tr></thead><tbody>{item.memberships.map((membership) => <tr key={membership.id}><td><strong>{membership.user.email}</strong><small className="table-subline">{[membership.user.first_name, membership.user.last_name].filter(Boolean).join(" ") || "No profile name"}</small></td><td>{membership.role}</td><td>{membership.status}</td><td>{formatDate(membership.created_at)}</td></tr>)}</tbody></table></div></section>
    <div className="platform-admin-grid platform-admin-grid--two"><section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Workspaces</p><h2>Decision areas</h2></div></div>{item.workspaces.length ? <div className="platform-list">{item.workspaces.map((workspace) => <article key={workspace.id}><strong>{workspace.name}</strong><span>{workspace.decision_count} decisions{workspace.is_default ? " · default" : ""}</span></article>)}</div> : <p className="muted">No workspaces.</p>}</section><section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Decision directory</p><h2>Recent decisions</h2></div></div>{item.decisions.length ? <div className="platform-list">{item.decisions.map((decision) => <article key={decision.id}><strong>{decision.title}</strong><span>{decision.status.replaceAll("_", " ")} · {decision.urgency}</span><small>Owner {decision.owner.email} · updated {formatDate(decision.updated_at)}</small></article>)}</div> : <p className="muted">No decisions.</p>}</section></div>
    <section className="card-panel"><div className="section-heading"><div><p className="eyebrow">Invitations</p><h2>Pending and historical invitations</h2><p className="muted">Resend and revoke are available only during an operational support session.</p></div></div>{item.invitations.length ? <div className="table-wrap"><table><thead><tr><th>Email</th><th>Role</th><th>Status</th><th>Expires</th><th>Sent</th><th /></tr></thead><tbody>{item.invitations.map((invitation) => <tr key={invitation.id}><td>{invitation.email}</td><td>{invitation.role}</td><td>{invitation.effective_status}</td><td>{formatDate(invitation.expires_at)}</td><td>{invitation.send_count}</td><td><InvitationAction item={invitation} operational={operational} onSuccess={refresh} /></td></tr>)}</tbody></table></div> : <p className="muted">No invitations.</p>}</section>
    <div className="platform-admin-grid platform-admin-grid--two"><section className="card-panel governance-danger-section"><p className="eyebrow">Ownership continuity</p><h2>Transfer organisation ownership</h2><p className="muted">This changes tenant authority, not platform membership. It requires operational support access, a named recipient, exact confirmation, and a durable rationale.</p><label>New owner<select value={ownership.target_membership_id} onChange={(event) => setOwnership({ ...ownership, target_membership_id: event.target.value })}><option value="">Choose an active member</option>{ownerCandidates.map((membership) => <option key={membership.id} value={membership.id}>{membership.user.email} · {membership.role}</option>)}</select></label><label className="checkbox-label"><input type="checkbox" checked={ownership.demote_existing_owners} onChange={(event) => setOwnership({ ...ownership, demote_existing_owners: event.target.checked })} />Demote other active owners to administrator</label><label>Rationale<textarea rows={3} value={ownership.rationale} onChange={(event) => setOwnership({ ...ownership, rationale: event.target.value })} /></label><label>Type {item.name}<input value={ownership.confirmation} onChange={(event) => setOwnership({ ...ownership, confirmation: event.target.value })} /></label>{transfer.isError ? <StatusMessage kind="error">{transfer.error instanceof ApiError ? transfer.error.message : "Ownership transfer failed."}</StatusMessage> : null}<button className="button button--danger" type="button" disabled={!operational || !ownership.target_membership_id || ownership.rationale.trim().length < 12 || ownership.confirmation !== item.name || transfer.isPending} onClick={() => transfer.mutate()}>{transfer.isPending ? "Transferring…" : "Transfer ownership"}</button></section><section className="card-panel governance-danger-section"><p className="eyebrow">Tenant state</p><h2>{item.status === "active" ? "Deactivate organisation" : "Reactivate organisation"}</h2><p className="muted">Deactivation still honours the ordinary closure blockers. Platform administration does not bypass unfinished decisions, contribution work, or pending invitations.</p><label>Rationale<textarea rows={3} value={stateChange.rationale} onChange={(event) => setStateChange({ ...stateChange, rationale: event.target.value })} /></label><label>Type {item.name}<input value={stateChange.confirmation} onChange={(event) => setStateChange({ ...stateChange, confirmation: event.target.value })} /></label>{stateMutation.isError ? <StatusMessage kind="error">{stateMutation.error instanceof ApiError ? stateMutation.error.message : "The organisation state could not be changed."}</StatusMessage> : null}<button className={item.status === "active" ? "button button--danger" : "button button--primary"} type="button" disabled={!operational || stateChange.rationale.trim().length < 12 || stateChange.confirmation !== item.name || stateMutation.isPending} onClick={() => stateMutation.mutate()}>{stateMutation.isPending ? "Checking safeguards…" : item.status === "active" ? "Deactivate organisation" : "Reactivate organisation"}</button></section></div>
  </div>;
}

export function PlatformOrganisationSupportPage() {
  const { organisationId = "" } = useParams<{ organisationId: string }>();
  const currentUser = useQuery({ queryKey: ["current-user"], queryFn: fetchCurrentUser, staleTime: 60_000 });
  const summaries = useQuery({ queryKey: ["platform-admin", "organisations", "support-summary"], queryFn: () => listPlatformOrganisations() });
  const detail = useQuery({ queryKey: ["platform-admin", "organisation", organisationId], queryFn: () => getPlatformOrganisation(organisationId), enabled: Boolean(organisationId), retry: false });
  if (currentUser.isPending || summaries.isPending) return <p>Checking support authority…</p>;
  if (!currentUser.data?.is_platform_administrator) return <StatusMessage kind="error">This workspace requires an active CrowdSmarter platform-administrator capability.</StatusMessage>;
  const summary = summaries.data?.find((item) => item.id === organisationId);
  if (!summary) return <StatusMessage kind="error">The organisation could not be found.</StatusMessage>;
  const deniedForGrant = detail.error instanceof ApiError && detail.error.status === 403;
  return <div className="platform-admin-page"><Link className="back-link" to="/platform-admin">← Platform administration</Link><div className="page-heading"><div><p className="eyebrow">Tenant support workspace</p><h1>{summary.name}</h1><p className="muted">Platform oversight without hidden project participation.</p></div><span className={`status-pill status-pill--${summary.status}`}>{summary.status}</span></div>{detail.isPending ? <p>Checking support-access grant…</p> : deniedForGrant ? <SupportAccessGate organisationId={organisationId} organisationName={summary.name} /> : detail.isError || !detail.data ? <StatusMessage kind="error">{detail.error instanceof ApiError ? detail.error.message : "The tenant support workspace could not be loaded."}</StatusMessage> : <SupportWorkspace item={detail.data} />}</div>;
}
