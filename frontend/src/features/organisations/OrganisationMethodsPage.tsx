import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { DecisionMethod, DecisionMethodVersion } from "../../lib/types";
import { listDecisionTemplates } from "../decisions/api";
import { getOrganisation } from "./api";
import {
  approveMethodVersion,
  cloneBuiltInMethod,
  createDecisionMethod,
  createMethodVersion,
  listDecisionMethods,
  listDecisionMethodUsage,
  retireDecisionMethod,
  updateMethodVersion,
} from "./methodology-api";

const REQUIRED_FIELDS = [
  ["decision_question", "Decision question"],
  ["purpose", "Purpose"],
  ["context", "Context"],
  ["scope", "Scope"],
  ["contribution_guidance", "Contribution guidance"],
] as const;

function lines(value: string): string[] {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function VersionEditor({ method, version, canApprove, onSaved }: {
  method: DecisionMethod;
  version: DecisionMethodVersion;
  canApprove: boolean;
  onSaved: () => Promise<void>;
}) {
  const [values, setValues] = useState({
    question_prompt: version.question_prompt,
    purpose_prompt: version.purpose_prompt,
    context_prompt: version.context_prompt,
    scope_prompt: version.scope_prompt,
    contribution_prompt: version.contribution_prompt,
    suggested_urgency: version.suggested_urgency,
    required_fields: version.required_fields,
    checklist: version.checklist.join("\n"),
    evidence_prompts: version.evidence_prompts.join("\n"),
    assumption_prompts: version.assumption_prompts.join("\n"),
    risk_prompts: version.risk_prompts.join("\n"),
    stakeholder_prompts: version.stakeholder_prompts.join("\n"),
    lifecycle_expectations: version.lifecycle_expectations.join("\n"),
  });
  const save = useMutation({
    mutationFn: () => updateMethodVersion(version.id, {
      ...values,
      checklist: lines(values.checklist),
      evidence_prompts: lines(values.evidence_prompts),
      assumption_prompts: lines(values.assumption_prompts),
      risk_prompts: lines(values.risk_prompts),
      stakeholder_prompts: lines(values.stakeholder_prompts),
      lifecycle_expectations: lines(values.lifecycle_expectations),
    }),
    onSuccess: onSaved,
  });
  const approve = useMutation({ mutationFn: () => approveMethodVersion(version.id), onSuccess: onSaved });

  return (
    <section className="method-editor" aria-labelledby={`method-version-${version.id}`}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Draft version {version.version}</p>
          <h3 id={`method-version-${version.id}`}>{method.name}</h3>
          <p className="muted">Edit the process guidance. Approval freezes this version and makes it available for new decisions.</p>
        </div>
        <span className="role-badge">{version.status}</span>
      </div>
      {(save.error || approve.error) ? (
        <StatusMessage kind="error">
          {(save.error instanceof ApiError && save.error.message) || (approve.error instanceof ApiError && approve.error.message) || "The method could not be updated."}
        </StatusMessage>
      ) : null}
      <div className="form-grid form-grid--two">
        <label>Decision-question prompt<textarea rows={3} value={values.question_prompt} onChange={(event) => setValues({ ...values, question_prompt: event.target.value })} /></label>
        <label>Purpose prompt<textarea rows={3} value={values.purpose_prompt} onChange={(event) => setValues({ ...values, purpose_prompt: event.target.value })} /></label>
        <label>Context prompt<textarea rows={3} value={values.context_prompt} onChange={(event) => setValues({ ...values, context_prompt: event.target.value })} /></label>
        <label>Scope prompt<textarea rows={3} value={values.scope_prompt} onChange={(event) => setValues({ ...values, scope_prompt: event.target.value })} /></label>
      </div>
      <label>Contribution prompt<textarea rows={3} value={values.contribution_prompt} onChange={(event) => setValues({ ...values, contribution_prompt: event.target.value })} /></label>
      <div className="form-grid form-grid--two">
        <label>Suggested urgency<select value={values.suggested_urgency} onChange={(event) => setValues({ ...values, suggested_urgency: event.target.value as typeof values.suggested_urgency })}><option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option><option value="critical">Critical</option></select></label>
        <fieldset className="method-required-fields"><legend>Required framing</legend>{REQUIRED_FIELDS.map(([key, label]) => <label key={key}><input type="checkbox" checked={values.required_fields.includes(key)} onChange={(event) => setValues({ ...values, required_fields: event.target.checked ? [...values.required_fields, key] : values.required_fields.filter((item) => item !== key) })} />{label}</label>)}</fieldset>
      </div>
      <div className="form-grid form-grid--two">
        <label>Decision-quality checklist<textarea rows={5} value={values.checklist} onChange={(event) => setValues({ ...values, checklist: event.target.value })} /><small>One expectation per line.</small></label>
        <label>Evidence prompts<textarea rows={5} value={values.evidence_prompts} onChange={(event) => setValues({ ...values, evidence_prompts: event.target.value })} /><small>One evidence category or question per line.</small></label>
        <label>Assumption prompts<textarea rows={5} value={values.assumption_prompts} onChange={(event) => setValues({ ...values, assumption_prompts: event.target.value })} /></label>
        <label>Risk prompts<textarea rows={5} value={values.risk_prompts} onChange={(event) => setValues({ ...values, risk_prompts: event.target.value })} /></label>
        <label>Stakeholder prompts<textarea rows={5} value={values.stakeholder_prompts} onChange={(event) => setValues({ ...values, stakeholder_prompts: event.target.value })} /></label>
        <label>Lifecycle expectations<textarea rows={5} value={values.lifecycle_expectations} onChange={(event) => setValues({ ...values, lifecycle_expectations: event.target.value })} /></label>
      </div>
      <div className="inline-actions method-editor__actions">
        <button className="button button--secondary" type="button" disabled={save.isPending} onClick={() => save.mutate()}>{save.isPending ? "Saving…" : "Save draft"}</button>
        {canApprove ? <button className="button button--primary" type="button" disabled={approve.isPending} onClick={() => { if (window.confirm("Approve and publish this immutable method version?")) approve.mutate(); }}>{approve.isPending ? "Approving…" : "Approve version"}</button> : null}
      </div>
    </section>
  );
}

export function OrganisationMethodsPage() {
  const { organisationId = "" } = useParams<{ organisationId: string }>();
  const queryClient = useQueryClient();
  const [cloneKey, setCloneKey] = useState("technology_adoption");
  const [customOpen, setCustomOpen] = useState(false);
  const [custom, setCustom] = useState({
    name: "", summary: "", best_for: "", question_prompt: "", purpose_prompt: "", context_prompt: "",
    scope_prompt: "", contribution_prompt: "", suggested_urgency: "normal", checklist: "",
  });
  const organisation = useQuery({ queryKey: ["organisations", organisationId], queryFn: () => getOrganisation(organisationId), enabled: Boolean(organisationId) });
  const methods = useQuery({ queryKey: ["decision-methods", organisationId], queryFn: () => listDecisionMethods(organisationId), enabled: Boolean(organisationId) });
  const usage = useQuery({ queryKey: ["decision-method-usage", organisationId], queryFn: () => listDecisionMethodUsage(organisationId), enabled: Boolean(organisationId) });
  const builtIns = useQuery({ queryKey: ["decision-templates"], queryFn: listDecisionTemplates });
  const canManage = ["owner", "admin"].includes(organisation.data?.current_user_role ?? "");
  const canApprove = organisation.data?.current_user_role === "owner";
  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["decision-methods", organisationId] });
    await queryClient.invalidateQueries({ queryKey: ["decision-method-usage", organisationId] });
  };
  const clone = useMutation({ mutationFn: () => cloneBuiltInMethod(organisationId, { builtin_key: cloneKey }), onSuccess: refresh });
  const create = useMutation({
    mutationFn: () => createDecisionMethod(organisationId, {
      ...custom,
      checklist: lines(custom.checklist),
      required_fields: ["decision_question", "purpose", "context", "scope", "contribution_guidance"],
      evidence_prompts: [], assumption_prompts: [], risk_prompts: [], stakeholder_prompts: [], lifecycle_expectations: [],
    }),
    onSuccess: async () => { setCustomOpen(false); setCustom({ name: "", summary: "", best_for: "", question_prompt: "", purpose_prompt: "", context_prompt: "", scope_prompt: "", contribution_prompt: "", suggested_urgency: "normal", checklist: "" }); await refresh(); },
  });
  const newVersion = useMutation({ mutationFn: (methodId: string) => createMethodVersion(methodId), onSuccess: refresh });
  const retire = useMutation({ mutationFn: ({ id, reason }: { id: string; reason: string }) => retireDecisionMethod(id, reason), onSuccess: refresh });
  const draftEditors = useMemo(() => (methods.data ?? []).flatMap((method) => method.versions.filter((version) => version.status === "draft").map((version) => ({ method, version }))), [methods.data]);

  if (organisation.isPending || methods.isPending) return <p>Loading organisation methods…</p>;
  if (organisation.isError || methods.isError || !organisation.data) return <StatusMessage kind="error">Organisation methods could not be loaded.</StatusMessage>;

  return (
    <div className="methodology-page">
      <Link className="back-link" to={`/organisations/${organisationId}`}>← {organisation.data.name}</Link>
      <div className="page-heading">
        <div><p className="eyebrow">Organisation methodology</p><h1>Govern how important decisions are framed</h1><p className="muted">Create reusable prompts and process expectations without pre-deciding the outcome.</p></div>
        <span className="role-badge">{methods.data?.filter((item) => item.status === "approved").length ?? 0} approved</span>
      </div>

      {canManage ? <section className="methodology-starter card-panel">
        <div className="section-heading"><div><p className="eyebrow">Start safely</p><h2>Clone a proven built-in pattern</h2><p className="muted">The clone begins as a draft and must be approved by an owner.</p></div><button className="button button--secondary" type="button" onClick={() => setCustomOpen((value) => !value)}><Icon name="plus" size={17} />Custom method</button></div>
        <div className="method-clone-row"><select value={cloneKey} onChange={(event) => setCloneKey(event.target.value)}>{builtIns.data?.map((item) => <option key={item.key} value={item.key}>{item.name}</option>)}</select><button className="button button--primary" type="button" disabled={clone.isPending} onClick={() => clone.mutate()}>{clone.isPending ? "Cloning…" : "Clone as draft"}</button></div>
        {clone.error ? <StatusMessage kind="error">{clone.error instanceof ApiError ? clone.error.message : "The method could not be cloned."}</StatusMessage> : null}
        {customOpen ? <div className="method-custom-form"><h3>Create a method from a clean frame</h3><div className="form-grid form-grid--two"><label>Name<input value={custom.name} onChange={(event) => setCustom({ ...custom, name: event.target.value })} /></label><label>Best for<input value={custom.best_for} onChange={(event) => setCustom({ ...custom, best_for: event.target.value })} /></label></div><label>Summary<textarea rows={3} value={custom.summary} onChange={(event) => setCustom({ ...custom, summary: event.target.value })} /></label><div className="form-grid form-grid--two"><label>Question prompt<textarea rows={3} value={custom.question_prompt} onChange={(event) => setCustom({ ...custom, question_prompt: event.target.value })} /></label><label>Purpose prompt<textarea rows={3} value={custom.purpose_prompt} onChange={(event) => setCustom({ ...custom, purpose_prompt: event.target.value })} /></label><label>Context prompt<textarea rows={3} value={custom.context_prompt} onChange={(event) => setCustom({ ...custom, context_prompt: event.target.value })} /></label><label>Scope prompt<textarea rows={3} value={custom.scope_prompt} onChange={(event) => setCustom({ ...custom, scope_prompt: event.target.value })} /></label></div><label>Contribution prompt<textarea rows={3} value={custom.contribution_prompt} onChange={(event) => setCustom({ ...custom, contribution_prompt: event.target.value })} /></label><label>Checklist<textarea rows={4} value={custom.checklist} onChange={(event) => setCustom({ ...custom, checklist: event.target.value })} /></label>{create.error ? <StatusMessage kind="error">{create.error instanceof ApiError ? create.error.message : "Creation failed."}</StatusMessage> : null}<button className="button button--primary" type="button" disabled={create.isPending} onClick={() => create.mutate()}>{create.isPending ? "Creating…" : "Create draft method"}</button></div> : null}
      </section> : null}

      {draftEditors.map(({ method, version }) => <VersionEditor key={version.id} method={method} version={version} canApprove={canApprove} onSaved={refresh} />)}

      <section className="card-panel">
        <div className="section-heading"><div><p className="eyebrow">Method library</p><h2>Approved, draft and retired methods</h2></div></div>
        <div className="method-card-grid">{methods.data?.map((method) => <article className="method-card" key={method.id}><div className="method-card__heading"><span className={`status-pill status-pill--${method.status}`}>{method.status}</span><span>v{method.current_version?.version ?? method.versions[0]?.version ?? 1}</span></div><h3>{method.name}</h3><p>{method.summary}</p><small>{method.best_for}</small><div className="method-card__meta"><span>{method.current_version?.required_fields.length ?? 0} required framing fields</span><span>{method.current_version?.checklist.length ?? 0} checklist items</span></div>{canManage && method.status !== "retired" && !method.versions.some((version) => version.status === "draft") ? <button className="button button--secondary" type="button" disabled={newVersion.isPending} onClick={() => newVersion.mutate(method.id)}>Create next version</button> : null}{canApprove && method.status !== "retired" ? <button className="button button--danger-quiet" type="button" onClick={() => { const reason = window.prompt("Why is this method being retired?"); if (reason) retire.mutate({ id: method.id, reason }); }}>Retire</button> : null}</article>)}</div>
      </section>

      <section className="card-panel">
        <div className="section-heading"><div><p className="eyebrow">Usage history</p><h2>Decisions started from organisation methods</h2><p className="muted">Past decisions retain the exact approved version they used.</p></div></div>
        {usage.data?.length ? <div className="table-wrap"><table><thead><tr><th>Decision</th><th>Method</th><th>Applied by</th><th>Date</th></tr></thead><tbody>{usage.data.map((item) => <tr key={item.id}><td><Link to={`/decisions/${item.decision_id}`}>{item.decision_title}</Link></td><td>{item.method_name} v{item.method_version_number}</td><td>{item.applied_by_email}</td><td>{formatDate(item.created_at)}</td></tr>)}</tbody></table></div> : <p className="muted">No decisions have used an organisation method yet.</p>}
      </section>
    </div>
  );
}
