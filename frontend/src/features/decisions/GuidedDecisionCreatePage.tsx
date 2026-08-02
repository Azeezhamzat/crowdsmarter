import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { DecisionMethod, DecisionTemplate } from "../../lib/types";
import { fetchCurrentUser } from "../auth/api";
import { listMemberships } from "../organisations/api";
import { listDecisionMethods } from "../organisations/methodology-api";
import { getWorkspace } from "../workspaces/api";
import { createDecision, listDecisionTemplates } from "./api";

const schema = z.object({
  template_key: z.string(),
  method_version_id: z.string(),
  title: z.string().trim().min(3, "Enter a clear working title.").max(240),
  decision_question: z
    .string()
    .trim()
    .min(12, "Write a specific question that a human authority can answer.")
    .max(4000),
  purpose: z.string().trim().min(12, "Explain the outcome this decision should enable.").max(8000),
  context: z.string().trim().min(12, "Describe why this decision is needed now.").max(12000),
  scope: z.string().trim().min(12, "Define what is included and excluded.").max(8000),
  contribution_guidance: z
    .string()
    .trim()
    .min(12, "Tell contributors what evidence and boundaries matter.")
    .max(8000),
  urgency: z.enum(["low", "normal", "high", "critical"]),
  target_decision_date: z.string(),
  contribution_deadline: z.string(),
  owner_id: z.string().uuid("Choose an active organisation member."),
}).refine((values) => Boolean(values.template_key || values.method_version_id), {
  message: "Choose a built-in template or an approved organisation method.",
  path: ["template_key"],
});

type FormInput = z.infer<typeof schema>;

const STEPS = ["Choose a template", "Frame the decision", "Set boundaries", "Assign authority", "Review"];

function memberName(firstName: string, lastName: string, email: string) {
  return `${firstName} ${lastName}`.trim() || email;
}

function TemplateCard({ template, selected, onSelect }: {
  template: DecisionTemplate;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      className={`template-card${selected ? " template-card--selected" : ""}`}
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
    >
      <span className="template-card__name">{template.name}</span>
      <span>{template.summary}</span>
      <small>{template.best_for}</small>
    </button>
  );
}

export function GuidedDecisionCreatePage() {
  const { workspaceId: routeWorkspaceId } = useParams<{ workspaceId: string }>();
  const workspaceId = routeWorkspaceId ?? "";
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const workspace = useQuery({
    queryKey: ["workspaces", workspaceId],
    queryFn: () => getWorkspace(workspaceId),
    enabled: Boolean(workspaceId),
  });
  const templates = useQuery({ queryKey: ["decision-templates"], queryFn: listDecisionTemplates });
  const methods = useQuery({
    queryKey: ["decision-methods", workspace.data?.organisation_id],
    queryFn: () => listDecisionMethods(workspace.data?.organisation_id ?? ""),
    enabled: Boolean(workspace.data?.organisation_id),
  });
  const currentUser = useQuery({ queryKey: ["auth", "me"], queryFn: fetchCurrentUser });
  const memberships = useQuery({
    queryKey: ["organisations", workspace.data?.organisation_id, "memberships"],
    queryFn: () => listMemberships(workspace.data?.organisation_id ?? ""),
    enabled: Boolean(workspace.data?.organisation_id),
  });
  const form = useForm<FormInput>({
    resolver: zodResolver(schema),
    defaultValues: {
      template_key: "blank",
      method_version_id: "",
      title: "",
      decision_question: "",
      purpose: "",
      context: "",
      scope: "",
      contribution_guidance: "",
      urgency: "normal",
      target_decision_date: "",
      contribution_deadline: "",
      owner_id: "",
    },
  });

  useEffect(() => {
    if (currentUser.data && !form.getValues("owner_id")) {
      form.setValue("owner_id", currentUser.data.id);
    }
  }, [currentUser.data, form]);

  const actorMembership = memberships.data?.find(
    (item) => item.user.id === currentUser.data?.id && item.status === "active",
  );
  const ownerChoices = (memberships.data ?? []).filter(
    (item) =>
      item.status === "active" &&
      (actorMembership?.role !== "contributor" || item.user.id === currentUser.data?.id),
  );

  const selectedTemplateKey = form.watch("template_key");
  const selectedMethodVersionId = form.watch("method_version_id");
  const approvedMethods = (methods.data ?? []).filter((item) => item.status === "approved" && item.current_version);
  const selectedMethod = approvedMethods.find((item) => item.current_version?.id === selectedMethodVersionId);
  const selectedTemplate = useMemo(
    () => {
      const builtIn = templates.data?.find((item) => item.key === selectedTemplateKey);
      if (builtIn) return builtIn;
      if (!selectedMethod?.current_version) return undefined;
      return {
        key: `method:${selectedMethod.current_version.id}`,
        name: selectedMethod.name,
        summary: selectedMethod.summary,
        best_for: selectedMethod.best_for,
        question_prompt: selectedMethod.current_version.question_prompt,
        purpose_prompt: selectedMethod.current_version.purpose_prompt,
        context_prompt: selectedMethod.current_version.context_prompt,
        scope_prompt: selectedMethod.current_version.scope_prompt,
        contribution_prompt: selectedMethod.current_version.contribution_prompt,
        suggested_urgency: selectedMethod.current_version.suggested_urgency,
        checklist: selectedMethod.current_version.checklist,
        version: selectedMethod.current_version.version,
      } satisfies DecisionTemplate;
    },
    [selectedMethod, selectedTemplateKey, templates.data],
  );

  const create = useMutation({
    mutationFn: (values: FormInput) =>
      createDecision(workspaceId, {
        ...values,
        method_version_id: values.method_version_id || null,
        target_decision_date: values.target_decision_date || null,
        contribution_deadline: values.contribution_deadline
          ? new Date(values.contribution_deadline).toISOString()
          : null,
      }),
    onSuccess: (decision) => navigate(`/decisions/${decision.id}`),
  });

  const chooseTemplate = (template: DecisionTemplate) => {
    form.setValue("template_key", template.key, { shouldDirty: true });
    form.setValue("method_version_id", "", { shouldDirty: true });
    form.setValue("urgency", template.suggested_urgency, { shouldDirty: true });
  };

  const chooseMethod = (method: DecisionMethod) => {
    if (!method.current_version) return;
    form.setValue("template_key", "", { shouldDirty: true });
    form.setValue("method_version_id", method.current_version.id, { shouldDirty: true });
    form.setValue("urgency", method.current_version.suggested_urgency, { shouldDirty: true });
  };

  const validateStep = async () => {
    const fields: Array<keyof FormInput>[] = [
      ["template_key", "method_version_id"],
      ["title", "decision_question", "purpose", "context"],
      ["scope", "contribution_guidance"],
      ["owner_id", "urgency", "target_decision_date", "contribution_deadline"],
      [],
    ];
    return form.trigger(fields[step] ?? []);
  };

  const next = async () => {
    if (await validateStep()) setStep((value) => Math.min(value + 1, STEPS.length - 1));
  };

  if (
    workspace.isPending ||
    templates.isPending ||
    (Boolean(workspace.data?.organisation_id) && methods.isPending) ||
    currentUser.isPending ||
    (Boolean(workspace.data?.organisation_id) && memberships.isPending)
  ) {
    return <p>Preparing guided decision creation…</p>;
  }
  if (workspace.isError || templates.isError || methods.isError || currentUser.isError || !workspace.data) {
    return <StatusMessage kind="error">Guided decision creation could not be loaded.</StatusMessage>;
  }
  if (!workspace.data.can_create_decisions) {
    return (
      <StatusMessage kind="error">
        Your organisation role cannot create decisions in this workspace.
      </StatusMessage>
    );
  }

  const values = form.watch();

  return (
    <div className="guided-create">
      <Link className="back-link" to={`/workspaces/${workspaceId}`}>← {workspace.data.name}</Link>
      <div className="page-heading guided-create__heading">
        <div>
          <p className="eyebrow">Guided decision creation</p>
          <h1>Start with a clear, governable question</h1>
          <p className="muted">Templates provide prompts, not answers. Every field remains editable and every decision remains human-owned.</p>
        </div>
        <span className="role-badge">Step {step + 1} of {STEPS.length}</span>
      </div>

      <ol className="creation-steps" aria-label="Decision creation progress">
        {STEPS.map((label, index) => (
          <li className={index === step ? "is-current" : index < step ? "is-complete" : ""} key={label}>
            <span>{index + 1}</span>{label}
          </li>
        ))}
      </ol>

      {create.error ? (
        <StatusMessage kind="error">
          {create.error instanceof ApiError ? create.error.message : "The decision could not be created."}
        </StatusMessage>
      ) : null}

      <form onSubmit={form.handleSubmit((input) => create.mutate(input))} noValidate>
        {step === 0 ? (
          <section className="creation-panel" aria-labelledby="template-title">
            <p className="eyebrow">Decision pattern</p>
            <h2 id="template-title">Choose the closest starting point</h2>
            {approvedMethods.length ? (
              <>
                <div className="method-selection-heading"><strong>Approved organisation methods</strong><span>Governed by {workspace.data.organisation_id}</span></div>
                <div className="template-grid">
                  {approvedMethods.map((method) => method.current_version ? (
                    <button
                      className={`template-card template-card--organisation${values.method_version_id === method.current_version.id ? " template-card--selected" : ""}`}
                      type="button"
                      key={method.id}
                      onClick={() => chooseMethod(method)}
                      aria-pressed={values.method_version_id === method.current_version.id}
                    >
                      <span className="template-card__name">{method.name}</span>
                      <span>{method.summary}</span>
                      <small>Organisation method · version {method.current_version.version}</small>
                    </button>
                  ) : null)}
                </div>
              </>
            ) : null}
            <div className="method-selection-heading"><strong>Built-in starting patterns</strong><span>Provider-neutral defaults</span></div>
            <div className="template-grid">
              {templates.data?.map((template) => (
                <TemplateCard
                  key={template.key}
                  template={template}
                  selected={values.template_key === template.key && !values.method_version_id}
                  onSelect={() => chooseTemplate(template)}
                />
              ))}
            </div>
            <FieldError message={form.formState.errors.template_key?.message} />
          </section>
        ) : null}

        {step === 1 ? (
          <section className="creation-panel" aria-labelledby="frame-title">
            <p className="eyebrow">Question and purpose</p>
            <h2 id="frame-title">Frame the choice before collecting opinions</h2>
            <div className="prompt-box"><strong>Template guidance</strong><p>{selectedTemplate?.question_prompt}</p></div>
            <label htmlFor="create-title">Working title</label>
            <input id="create-title" {...form.register("title")} />
            <FieldError message={form.formState.errors.title?.message} />
            <label htmlFor="create-question">Decision question</label>
            <textarea id="create-question" rows={3} {...form.register("decision_question")} />
            <FieldError message={form.formState.errors.decision_question?.message} />
            <p className="field-guidance">{selectedTemplate?.purpose_prompt}</p>
            <label htmlFor="create-purpose">Purpose</label>
            <textarea id="create-purpose" rows={3} {...form.register("purpose")} />
            <FieldError message={form.formState.errors.purpose?.message} />
            <p className="field-guidance">{selectedTemplate?.context_prompt}</p>
            <label htmlFor="create-context">Context</label>
            <textarea id="create-context" rows={5} {...form.register("context")} />
            <FieldError message={form.formState.errors.context?.message} />
          </section>
        ) : null}

        {step === 2 ? (
          <section className="creation-panel" aria-labelledby="boundaries-title">
            <p className="eyebrow">Boundaries</p>
            <h2 id="boundaries-title">Make the decision small enough to govern</h2>
            <p className="field-guidance">{selectedTemplate?.scope_prompt}</p>
            <label htmlFor="create-scope">Scope and exclusions</label>
            <textarea id="create-scope" rows={5} {...form.register("scope")} />
            <FieldError message={form.formState.errors.scope?.message} />
            <p className="field-guidance">{selectedTemplate?.contribution_prompt}</p>
            <label htmlFor="create-guidance">Contribution boundaries</label>
            <textarea id="create-guidance" rows={5} {...form.register("contribution_guidance")} />
            <FieldError message={form.formState.errors.contribution_guidance?.message} />
            {selectedTemplate?.checklist.length ? (
              <div className="template-checklist">
                <strong>Remember to cover</strong>
                <ul>{selectedTemplate.checklist.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
            ) : null}
          </section>
        ) : null}

        {step === 3 ? (
          <section className="creation-panel" aria-labelledby="authority-title">
            <p className="eyebrow">Authority and timing</p>
            <h2 id="authority-title">Name accountability before the work begins</h2>
            {memberships.isError ? <StatusMessage kind="error">Organisation members could not be loaded.</StatusMessage> : null}
            <label htmlFor="create-owner">Decision owner</label>
            <select id="create-owner" {...form.register("owner_id")}>
              {ownerChoices.map((item) => (
                <option key={item.id} value={item.user.id}>{memberName(item.user.first_name, item.user.last_name, item.user.email)}</option>
              ))}
            </select>
            <FieldError message={form.formState.errors.owner_id?.message} />
            <div className="form-row">
              <div>
                <label htmlFor="create-urgency">Urgency</label>
                <select id="create-urgency" {...form.register("urgency")}>
                  <option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option><option value="critical">Critical</option>
                </select>
              </div>
              <div>
                <label htmlFor="create-target">Target decision date</label>
                <input id="create-target" type="date" {...form.register("target_decision_date")} />
              </div>
            </div>
            <label htmlFor="create-deadline">Contribution deadline</label>
            <input id="create-deadline" type="datetime-local" {...form.register("contribution_deadline")} />
            <p className="muted compact-note">The deadline is optional while drafting, but must be in the future before contribution opens.</p>
          </section>
        ) : null}

        {step === 4 ? (
          <section className="creation-panel creation-review" aria-labelledby="review-title">
            <p className="eyebrow">Review before creation</p>
            <h2 id="review-title">Does this record describe one real decision?</h2>
            <dl className="review-grid">
              <div><dt>Template</dt><dd>{selectedTemplate?.name}</dd></div>
              <div><dt>Owner</dt><dd>{memberships.data?.find((item) => item.user.id === values.owner_id)?.user.email}</dd></div>
              <div className="review-grid__wide"><dt>Title</dt><dd>{values.title}</dd></div>
              <div className="review-grid__wide"><dt>Question</dt><dd>{values.decision_question}</dd></div>
              <div><dt>Urgency</dt><dd>{values.urgency}</dd></div>
              <div><dt>Target date</dt><dd>{values.target_decision_date || "Not set"}</dd></div>
            </dl>
            <div className="review-callout">
              <strong>This creates a draft, not a decision outcome.</strong>
              <p>You can continue editing the frame, add participants, and then advance the lifecycle with a recorded human rationale.</p>
            </div>
          </section>
        ) : null}

        <div className="creation-actions">
          {step > 0 ? <button className="button button--secondary" type="button" onClick={() => setStep((value) => value - 1)}>Back</button> : <span />}
          {step < STEPS.length - 1 ? (
            <button className="button button--primary" type="button" onClick={next}>Continue</button>
          ) : (
            <button className="button button--primary" type="submit" disabled={create.isPending}>{create.isPending ? "Creating draft…" : "Create decision draft"}</button>
          )}
        </div>
      </form>
    </div>
  );
}
