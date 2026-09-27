import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getAIReviewQualityMetrics } from "../ai-assistance/api";
import {
  changeOrganisationPlan,
  getOrganisationSubscription,
  listPlans,
  setOrganisationBillingContact,
} from "../billing/api";
import {
  clearDisbursementApiKey,
  getDisbursementConfiguration,
  setDisbursementApiKey,
  setDisbursementProvider,
  testDisbursementConnection,
} from "../disbursements/api";
import {
  clearLookupApiKey,
  getLookupConfiguration,
  setLookupApiKey,
  setLookupProvider,
  testLookupConnection,
} from "../org-enrichment/api";
import {
  cancelOrganisationDeletion,
  deactivateOrganisation,
  getOrganisation,
  listMembershipHistory,
  listMemberships,
  listOrganisationDeletionRequests,
  reactivateOrganisation,
  requestOrganisationDeletion,
  transferOrganisationOwnership,
  updateOrganisationAdministration,
} from "./api";

function formatDate(value: string | null): string {
  if (!value) return "N/A";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function OrganisationAdministrationPage() {
  const { organisationId = "" } = useParams<{ organisationId: string }>();
  const queryClient = useQueryClient();
  const organisation = useQuery({ queryKey: ["organisations", organisationId], queryFn: () => getOrganisation(organisationId), enabled: Boolean(organisationId) });
  const memberships = useQuery({ queryKey: ["organisations", organisationId, "memberships"], queryFn: () => listMemberships(organisationId), enabled: Boolean(organisationId) });
  const history = useQuery({ queryKey: ["organisations", organisationId, "membership-history"], queryFn: () => listMembershipHistory(organisationId), enabled: Boolean(organisationId) });
  const deletions = useQuery({ queryKey: ["organisations", organisationId, "deletion-requests"], queryFn: () => listOrganisationDeletionRequests(organisationId), enabled: Boolean(organisationId) && organisation.data?.current_user_role === "owner" });
  const aiQuality = useQuery({ queryKey: ["organisations", organisationId, "ai-review-quality"], queryFn: () => getAIReviewQualityMetrics(organisationId), enabled: Boolean(organisationId) && ["owner", "admin"].includes(organisation.data?.current_user_role ?? "") });
  const subscription = useQuery({ queryKey: ["organisations", organisationId, "subscription"], queryFn: () => getOrganisationSubscription(organisationId), enabled: Boolean(organisationId) && ["owner", "admin"].includes(organisation.data?.current_user_role ?? "") });
  const disbursementConfig = useQuery({ queryKey: ["organisations", organisationId, "disbursement-configuration"], queryFn: () => getDisbursementConfiguration(organisationId), enabled: Boolean(organisationId) && ["owner", "admin"].includes(organisation.data?.current_user_role ?? "") });
  const lookupConfig = useQuery({ queryKey: ["organisations", organisationId, "lookup-configuration"], queryFn: () => getLookupConfiguration(organisationId), enabled: Boolean(organisationId) && ["owner", "admin"].includes(organisation.data?.current_user_role ?? "") });
  const plans = useQuery({ queryKey: ["billing", "plans"], queryFn: () => listPlans(), enabled: Boolean(organisationId) && organisation.data?.current_user_role === "owner" });
  const [selectedPlanKey, setSelectedPlanKey] = useState("");
  const [settings, setSettings] = useState({ name: "", description: "", website_url: "", brand_name: "", primary_colour: "#315c54", invitation_policy: "owners_and_admins", default_invitation_role: "contributor", retention_days: "" });
  const [transfer, setTransfer] = useState({ target_membership_id: "", rationale: "" });
  const [deactivation, setDeactivation] = useState({ confirmation: "", reason: "" });
  const [reactivationRationale, setReactivationRationale] = useState("");
  const [deletion, setDeletion] = useState({ confirmation: "", reason: "" });
  const [disbursementProviderKey, setDisbursementProviderKey] = useState<"manual" | "stripe">("manual");
  const [stripeAccountId, setStripeAccountId] = useState("");
  const [disbursementCurrency, setDisbursementCurrency] = useState("USD");
  const [disbursementApiKeyInput, setDisbursementApiKeyInput] = useState("");
  const [connectionResult, setConnectionResult] = useState<{ ok: boolean; detail: string } | null>(null);
  const [lookupProviderKey, setLookupProviderKey] = useState<"manual" | "candid">("manual");
  const [lookupApiKeyInput, setLookupApiKeyInput] = useState("");
  const [lookupConnectionResult, setLookupConnectionResult] = useState<{ ok: boolean; detail: string } | null>(null);

  useEffect(() => {
    if (!organisation.data) return;
    setSettings({
      name: organisation.data.name,
      description: organisation.data.description,
      website_url: organisation.data.website_url,
      brand_name: organisation.data.brand_name,
      primary_colour: organisation.data.primary_colour,
      invitation_policy: organisation.data.invitation_policy,
      default_invitation_role: organisation.data.default_invitation_role,
      retention_days: organisation.data.retention_days?.toString() ?? "",
    });
  }, [organisation.data]);

  useEffect(() => {
    if (!subscription.data) return;
    setSelectedPlanKey(subscription.data.plan.key);
  }, [subscription.data]);

  useEffect(() => {
    if (!disbursementConfig.data) return;
    setDisbursementProviderKey(disbursementConfig.data.provider_key);
    setStripeAccountId(disbursementConfig.data.stripe_account_id);
    setDisbursementCurrency(disbursementConfig.data.currency);
  }, [disbursementConfig.data]);

  useEffect(() => {
    if (!lookupConfig.data) return;
    setLookupProviderKey(lookupConfig.data.provider_key);
  }, [lookupConfig.data]);

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId] }),
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "memberships"] }),
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "membership-history"] }),
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "deletion-requests"] }),
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "subscription"] }),
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "disbursement-configuration"] }),
      queryClient.invalidateQueries({ queryKey: ["organisations", organisationId, "lookup-configuration"] }),
      queryClient.invalidateQueries({ queryKey: ["organisations"] }),
    ]);
  };
  const save = useMutation({ mutationFn: () => updateOrganisationAdministration(organisationId, { ...settings, retention_days: settings.retention_days ? Number(settings.retention_days) : null }), onSuccess: refresh });
  const transferOwner = useMutation({ mutationFn: () => transferOrganisationOwnership(organisationId, transfer), onSuccess: async () => { setTransfer({ target_membership_id: "", rationale: "" }); await refresh(); } });
  const deactivate = useMutation({ mutationFn: () => deactivateOrganisation(organisationId, deactivation), onSuccess: refresh });
  const reactivate = useMutation({ mutationFn: () => reactivateOrganisation(organisationId, reactivationRationale), onSuccess: refresh });
  const requestDeletion = useMutation({ mutationFn: () => requestOrganisationDeletion(organisationId, deletion), onSuccess: refresh });
  const cancelDeletion = useMutation({ mutationFn: ({ id, rationale }: { id: string; rationale: string }) => cancelOrganisationDeletion(id, rationale), onSuccess: refresh });
  const changePlan = useMutation({ mutationFn: () => changeOrganisationPlan(organisationId, { plan_key: selectedPlanKey }), onSuccess: refresh });
  const setBillingContact = useMutation({ mutationFn: (userId: string) => setOrganisationBillingContact(organisationId, { user_id: userId || null }), onSuccess: refresh });
  const saveDisbursementProvider = useMutation({
    mutationFn: () => setDisbursementProvider(organisationId, { provider_key: disbursementProviderKey, stripe_account_id: stripeAccountId, currency: disbursementCurrency }),
    onSuccess: async () => { setConnectionResult(null); await refresh(); },
  });
  const saveDisbursementApiKey = useMutation({
    mutationFn: () => setDisbursementApiKey(organisationId, disbursementApiKeyInput),
    onSuccess: async () => { setDisbursementApiKeyInput(""); setConnectionResult(null); await refresh(); },
  });
  const removeDisbursementApiKey = useMutation({ mutationFn: () => clearDisbursementApiKey(organisationId), onSuccess: async () => { setConnectionResult(null); await refresh(); } });
  const checkDisbursementConnection = useMutation({
    mutationFn: () => testDisbursementConnection(organisationId),
    onSuccess: (result) => setConnectionResult({ ok: result.ok, detail: result.detail }),
  });
  const saveLookupProvider = useMutation({
    mutationFn: () => setLookupProvider(organisationId, { provider_key: lookupProviderKey }),
    onSuccess: async () => { setLookupConnectionResult(null); await refresh(); },
  });
  const saveLookupApiKey = useMutation({
    mutationFn: () => setLookupApiKey(organisationId, lookupApiKeyInput),
    onSuccess: async () => { setLookupApiKeyInput(""); setLookupConnectionResult(null); await refresh(); },
  });
  const removeLookupApiKey = useMutation({ mutationFn: () => clearLookupApiKey(organisationId), onSuccess: async () => { setLookupConnectionResult(null); await refresh(); } });
  const checkLookupConnection = useMutation({
    mutationFn: () => testLookupConnection(organisationId),
    onSuccess: (result) => setLookupConnectionResult({ ok: result.ok, detail: result.detail }),
  });

  if (organisation.isPending || memberships.isPending) return <p>Loading organisation administration…</p>;
  if (organisation.isError || !organisation.data) return <StatusMessage kind="error">Organisation administration could not be loaded.</StatusMessage>;
  const isOwner = organisation.data.current_user_role === "owner";
  const canManage = ["owner", "admin"].includes(organisation.data.current_user_role);
  const ownerCandidates = memberships.data?.filter((item) => item.status === "active" && item.role !== "owner") ?? [];
  const mutationError = save.error || transferOwner.error || deactivate.error || reactivate.error || requestDeletion.error || cancelDeletion.error || changePlan.error || setBillingContact.error || saveDisbursementProvider.error || saveDisbursementApiKey.error || removeDisbursementApiKey.error || saveLookupProvider.error || saveLookupApiKey.error || removeLookupApiKey.error;

  return (
    <div className="organisation-admin-page">
      <Link className="back-link" to={`/organisations/${organisationId}`}>← {organisation.data.name}</Link>
      <div className="page-heading"><div><p className="eyebrow">Organisation administration</p><h1>Identity, policy and account safeguards</h1><p className="muted">Manage the customer account without bypassing tenant ownership, audit or data-retention controls.</p></div><span className={`status-pill status-pill--${organisation.data.status}`}>{organisation.data.status}</span></div>
      {mutationError ? <StatusMessage kind="error">{mutationError instanceof ApiError ? mutationError.message : "The administrative action failed."}</StatusMessage> : null}

      <div className="admin-settings-grid">
        <section className="card-panel">
          <div className="section-heading"><div><p className="eyebrow">Profile and branding</p><h2>Customer-facing identity</h2></div><span className="brand-colour-preview" style={{ background: settings.primary_colour }} role="img" aria-label={`Brand colour ${settings.primary_colour}`} /></div>
          <div className="form-grid form-grid--two"><label>Organisation name<input value={settings.name} disabled={!canManage || organisation.data.status === "deactivated"} onChange={(event) => setSettings({ ...settings, name: event.target.value })} /></label><label>Brand name<input value={settings.brand_name} disabled={!canManage || organisation.data.status === "deactivated"} onChange={(event) => setSettings({ ...settings, brand_name: event.target.value })} /></label><label>Website<input type="url" value={settings.website_url} disabled={!canManage || organisation.data.status === "deactivated"} onChange={(event) => setSettings({ ...settings, website_url: event.target.value })} /></label><label>Primary colour<input type="text" pattern="#[0-9A-Fa-f]{6}" value={settings.primary_colour} disabled={!canManage || organisation.data.status === "deactivated"} onChange={(event) => setSettings({ ...settings, primary_colour: event.target.value })} /></label></div><label>Description<textarea rows={4} value={settings.description} disabled={!canManage || organisation.data.status === "deactivated"} onChange={(event) => setSettings({ ...settings, description: event.target.value })} /></label>
        </section>

        <section className="card-panel">
          <div><p className="eyebrow">Access policy</p><h2>Invitations and retention</h2><p className="muted">Owners control sensitive tenant policy; administrators can manage ordinary profile fields.</p></div>
          <label>Who may invite members<select value={settings.invitation_policy} disabled={!isOwner || organisation.data.status === "deactivated"} onChange={(event) => setSettings({ ...settings, invitation_policy: event.target.value })}><option value="owners_and_admins">Owners and administrators</option><option value="owners_only">Owners only</option></select></label>
          <label>Default invitation role<select value={settings.default_invitation_role} disabled={!canManage || organisation.data.status === "deactivated"} onChange={(event) => setSettings({ ...settings, default_invitation_role: event.target.value })}><option value="admin">Administrator</option><option value="contributor">Contributor</option><option value="viewer">Viewer</option></select></label>
          <label>Retention period after deletion request<input type="number" min={30} max={3650} value={settings.retention_days} disabled={!isOwner || organisation.data.status === "deactivated"} onChange={(event) => setSettings({ ...settings, retention_days: event.target.value })} /><small>Blank uses the protected 30-day minimum.</small></label>
          {canManage && organisation.data.status === "active" ? <button className="button button--primary" type="button" disabled={save.isPending} onClick={() => save.mutate()}>{save.isPending ? "Saving…" : "Save administration settings"}</button> : null}
        </section>
      </div>

      {canManage ? (
        <section className="card-panel">
          <div className="section-heading"><div><p className="eyebrow">Plan and billing</p><h2>Packaging tier and usage</h2><p className="muted">CrowdSmarter does not process payments in this environment (see ADR 0031) - plan changes here are recorded immediately without any charge.</p></div></div>
          {subscription.isError ? <StatusMessage kind="error">Plan and billing details require an owner or administrator role.</StatusMessage> : null}
          {subscription.data ? (
            <>
              <div className="ai-quality-metrics">
                <article><strong>{subscription.data.plan.name}</strong><span>Current plan ({subscription.data.status_label}{subscription.data.status === "trialing" && subscription.data.trial_ends_at ? `, ends ${formatDate(subscription.data.trial_ends_at)}` : ""})</span></article>
                <article><strong>{subscription.data.active_decision_count}{subscription.data.plan.max_active_decisions != null ? ` / ${subscription.data.plan.max_active_decisions}` : ""}</strong><span>Active decisions</span></article>
                <article><strong>{subscription.data.active_member_count}{subscription.data.plan.max_active_members != null ? ` / ${subscription.data.plan.max_active_members}` : ""}</strong><span>Active members</span></article>
                <article><strong>{subscription.data.billing_contact ? subscription.data.billing_contact.email : "N/A"}</strong><span>Billing contact</span></article>
              </div>
              {isOwner ? (
                <div className="form-grid form-grid--two">
                  <label>Change plan
                    <select value={selectedPlanKey} onChange={(event) => setSelectedPlanKey(event.target.value)}>
                      {(plans.data ?? [subscription.data.plan]).map((item) => <option key={item.key} value={item.key}>{item.name}</option>)}
                    </select>
                  </label>
                  <label>Billing contact
                    <select value={subscription.data.billing_contact?.id ?? ""} onChange={(event) => setBillingContact.mutate(event.target.value)}>
                      <option value="">No billing contact</option>
                      {(memberships.data ?? []).filter((item) => item.status === "active").map((item) => <option key={item.user.id} value={item.user.id}>{item.user.email}</option>)}
                    </select>
                  </label>
                </div>
              ) : null}
              {isOwner ? <button className="button button--primary" type="button" disabled={changePlan.isPending || selectedPlanKey === subscription.data.plan.key} onClick={() => changePlan.mutate()}>{changePlan.isPending ? "Changing plan…" : "Change plan"}</button> : null}
            </>
          ) : null}
        </section>
      ) : null}

      {isOwner && organisation.data.status === "active" ? <section className="card-panel governance-danger-section"><div><p className="eyebrow">Ownership</p><h2>Transfer accountable ownership</h2><p className="muted">The new owner gains owner authority. Your membership becomes administrator. The event is permanent in membership history.</p></div><div className="form-grid form-grid--two"><label>New owner<select value={transfer.target_membership_id} onChange={(event) => setTransfer({ ...transfer, target_membership_id: event.target.value })}><option value="">Choose an active member</option>{ownerCandidates.map((item) => <option key={item.id} value={item.id}>{item.user.email} · {item.role}</option>)}</select></label><label>Rationale<textarea rows={3} value={transfer.rationale} onChange={(event) => setTransfer({ ...transfer, rationale: event.target.value })} /></label></div><button className="button button--secondary" type="button" disabled={!transfer.target_membership_id || transferOwner.isPending} onClick={() => { if (window.confirm("Transfer organisation ownership and become an administrator?")) transferOwner.mutate(); }}>{transferOwner.isPending ? "Transferring…" : "Transfer ownership"}</button></section> : null}

      <section className="card-panel">
        <div className="section-heading"><div><p className="eyebrow">Membership history</p><h2>Attributable administrative record</h2></div></div>
        {history.isError ? <StatusMessage kind="error">Membership history requires an owner or administrator role.</StatusMessage> : null}
        {history.data?.length ? <div className="table-wrap"><table><thead><tr><th>Event</th><th>Member</th><th>Change</th><th>Note</th><th>Actor</th><th>Date</th></tr></thead><tbody>{history.data.map((item) => <tr key={item.id}><td>{item.kind_label}</td><td>{item.user.email}</td><td>{[item.previous_role, item.new_role].filter(Boolean).join(" → ") || "N/A"}</td><td>{item.note || "N/A"}</td><td>{item.actor.email}</td><td>{formatDate(item.created_at)}</td></tr>)}</tbody></table></div> : <p className="muted">No membership history is available.</p>}
      </section>

      {canManage ? (
        <section className="card-panel">
          <div className="section-heading"><div><p className="eyebrow">Evaluation harness</p><h2>AI review quality</h2><p className="muted">How often humans confirm vs. dismiss the advisory rule engine's output - a rising dismissal rate is a signal to review the rules, not to trust them less by default.</p></div></div>
          {aiQuality.isError ? <StatusMessage kind="error">AI review quality metrics require an owner or administrator role.</StatusMessage> : null}
          {aiQuality.data ? (
            <div className="ai-quality-metrics">
              <article><strong>{aiQuality.data.total_completed}</strong><span>Completed reviews</span></article>
              <article><strong>{aiQuality.data.reviewed_count}</strong><span>Confirmed by a human</span></article>
              <article><strong>{aiQuality.data.dismissed_count}</strong><span>Dismissed by a human</span></article>
              <article><strong>{aiQuality.data.pending_disposition_count}</strong><span>Awaiting human disposition</span></article>
              <article><strong>{aiQuality.data.correction_rate != null ? `${aiQuality.data.correction_rate}%` : "N/A"}</strong><span>Correction rate</span></article>
            </div>
          ) : <p className="muted">No completed AI reviews are recorded yet.</p>}
        </section>
      ) : null}

      {canManage ? (
        <section className="card-panel">
          <div className="section-heading"><div><p className="eyebrow">Grant payments</p><h2>Disbursement provider</h2><p className="muted">Funded applications default to a manual ledger - mark a payment made outside the platform. Connect Stripe to issue transfers directly once you have your own account.</p></div></div>
          {disbursementConfig.isError ? <StatusMessage kind="error">Disbursement configuration requires an owner or administrator role.</StatusMessage> : null}
          {disbursementConfig.data ? (
            <div className="form-grid form-grid--two">
              <label>Provider
                <select value={disbursementProviderKey} onChange={(event) => setDisbursementProviderKey(event.target.value as "manual" | "stripe")}>
                  <option value="manual">Manual ledger</option>
                  <option value="stripe">Stripe Connect</option>
                </select>
              </label>
              <label>Currency (ISO 4217)
                <input value={disbursementCurrency} maxLength={3} onChange={(event) => setDisbursementCurrency(event.target.value.toUpperCase())} placeholder="USD" />
              </label>
              {disbursementProviderKey === "stripe" ? (
                <label>Stripe connected account ID
                  <input value={stripeAccountId} onChange={(event) => setStripeAccountId(event.target.value)} placeholder="acct_..." />
                </label>
              ) : null}
              <div className="form-actions">
                <button className="button button--secondary" type="button" disabled={saveDisbursementProvider.isPending} onClick={() => saveDisbursementProvider.mutate()}>{saveDisbursementProvider.isPending ? "Saving…" : "Save provider"}</button>
              </div>
              {disbursementProviderKey === "stripe" ? (
                <>
                  <label>Stripe API key
                    <input type="password" value={disbursementApiKeyInput} onChange={(event) => setDisbursementApiKeyInput(event.target.value)} placeholder={disbursementConfig.data.api_key_is_set ? "•••• already set" : "sk_live_..."} />
                  </label>
                  <div className="form-actions">
                    <button className="button button--secondary" type="button" disabled={saveDisbursementApiKey.isPending || !disbursementApiKeyInput.trim()} onClick={() => saveDisbursementApiKey.mutate()}>{saveDisbursementApiKey.isPending ? "Saving…" : "Save key"}</button>
                    {disbursementConfig.data.api_key_is_set ? <button className="button button--quiet" type="button" disabled={removeDisbursementApiKey.isPending} onClick={() => removeDisbursementApiKey.mutate()}>Clear key</button> : null}
                    <button className="button button--quiet" type="button" disabled={checkDisbursementConnection.isPending} onClick={() => checkDisbursementConnection.mutate()}>{checkDisbursementConnection.isPending ? "Testing…" : "Test connection"}</button>
                  </div>
                </>
              ) : null}
              {connectionResult ? <StatusMessage kind={connectionResult.ok ? "success" : "error"}>{connectionResult.detail}</StatusMessage> : null}
            </div>
          ) : null}
        </section>
      ) : null}

      {canManage ? (
        <section className="card-panel">
          <div className="section-heading"><div><p className="eyebrow">Applicant verification</p><h2>Organisation lookup</h2><p className="muted">Manual verification requires no setup. Connect Candid to pre-fill an applicant's legal name, EIN/charity number, and standing while reviewing submissions.</p></div></div>
          {lookupConfig.isError ? <StatusMessage kind="error">Lookup configuration requires an owner or administrator role.</StatusMessage> : null}
          {lookupConfig.data ? (
            <div className="form-grid form-grid--two">
              <label>Provider
                <select value={lookupProviderKey} onChange={(event) => setLookupProviderKey(event.target.value as "manual" | "candid")}>
                  <option value="manual">Manual verification</option>
                  <option value="candid">Candid (GuideStar)</option>
                </select>
              </label>
              <div className="form-actions">
                <button className="button button--secondary" type="button" disabled={saveLookupProvider.isPending} onClick={() => saveLookupProvider.mutate()}>{saveLookupProvider.isPending ? "Saving…" : "Save provider"}</button>
              </div>
              {lookupProviderKey === "candid" ? (
                <>
                  <label>Candid API key
                    <input type="password" value={lookupApiKeyInput} onChange={(event) => setLookupApiKeyInput(event.target.value)} placeholder={lookupConfig.data.api_key_is_set ? "•••• already set" : "Subscription key"} />
                  </label>
                  <div className="form-actions">
                    <button className="button button--secondary" type="button" disabled={saveLookupApiKey.isPending || !lookupApiKeyInput.trim()} onClick={() => saveLookupApiKey.mutate()}>{saveLookupApiKey.isPending ? "Saving…" : "Save key"}</button>
                    {lookupConfig.data.api_key_is_set ? <button className="button button--quiet" type="button" disabled={removeLookupApiKey.isPending} onClick={() => removeLookupApiKey.mutate()}>Clear key</button> : null}
                    <button className="button button--quiet" type="button" disabled={checkLookupConnection.isPending} onClick={() => checkLookupConnection.mutate()}>{checkLookupConnection.isPending ? "Testing…" : "Test connection"}</button>
                  </div>
                </>
              ) : null}
              {lookupConnectionResult ? <StatusMessage kind={lookupConnectionResult.ok ? "success" : "error"}>{lookupConnectionResult.detail}</StatusMessage> : null}
            </div>
          ) : null}
        </section>
      ) : null}

      {isOwner ? <section className="card-panel governance-danger-section">
        <div><p className="eyebrow">Account state</p><h2>{organisation.data.status === "active" ? "Deactivate this organisation" : "Reactivate this organisation"}</h2><p className="muted">Deactivation requires all decisions to be archived, invitations resolved, and contribution work closed. It does not delete customer data.</p></div>
        {organisation.data.status === "active" ? <><label>Type the organisation name<input value={deactivation.confirmation} onChange={(event) => setDeactivation({ ...deactivation, confirmation: event.target.value })} /></label><label>Reason<textarea rows={3} value={deactivation.reason} onChange={(event) => setDeactivation({ ...deactivation, reason: event.target.value })} /></label><button className="button button--danger" type="button" disabled={deactivate.isPending} onClick={() => { if (window.confirm("Deactivate this organisation after the server verifies all closure safeguards?")) deactivate.mutate(); }}>{deactivate.isPending ? "Checking safeguards…" : "Deactivate organisation"}</button></> : <><label>Reactivation rationale<textarea rows={3} value={reactivationRationale} onChange={(event) => setReactivationRationale(event.target.value)} /></label><button className="button button--primary" type="button" disabled={reactivate.isPending} onClick={() => reactivate.mutate()}>{reactivate.isPending ? "Reactivating…" : "Reactivate organisation"}</button></>}
      </section> : null}

      {isOwner && organisation.data.status === "deactivated" ? <section className="card-panel governance-danger-section governance-danger-section--critical"><div><p className="eyebrow">Deletion safeguard</p><h2>Request delayed manual deletion</h2><p className="muted">CrowdSmarter never deletes the tenant immediately. A request creates an auditable waiting period and requires later manual completion.</p></div><label>Type DELETE {organisation.data.name}<input value={deletion.confirmation} onChange={(event) => setDeletion({ ...deletion, confirmation: event.target.value })} /></label><label>Reason<textarea rows={3} value={deletion.reason} onChange={(event) => setDeletion({ ...deletion, reason: event.target.value })} /></label><button className="button button--danger" type="button" disabled={requestDeletion.isPending} onClick={() => requestDeletion.mutate()}>{requestDeletion.isPending ? "Requesting…" : "Request deletion"}</button>{deletions.data?.map((item) => <article className="deletion-request" key={item.id}><strong>{item.status}</strong><span>Earliest deletion: {formatDate(item.earliest_deletion_at)}</span><p>{item.reason}</p>{item.status === "pending" ? <button className="button button--secondary" type="button" onClick={() => { const rationale = window.prompt("Why should the deletion request be cancelled?"); if (rationale) cancelDeletion.mutate({ id: item.id, rationale }); }}>Cancel request</button> : null}</article>)}</section> : null}
    </div>
  );
}
