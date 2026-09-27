import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import type { Decision, Membership } from "../../lib/types";
import type { DecisionUpdateInput } from "./api";

const framingSchema = z.object({
  title: z.string().trim().min(3, "Enter a clear title.").max(240),
  decision_question: z.string().trim().max(4000),
  purpose: z.string().trim().max(8000),
  context: z.string().trim().max(12000),
  scope: z.string().trim().max(8000),
  contribution_guidance: z.string().trim().max(8000),
  urgency: z.enum(["low", "normal", "high", "critical"]),
  target_decision_date: z.string(),
  contribution_deadline: z.string(),
  owner_id: z.string().uuid(),
});

type FramingInput = z.infer<typeof framingSchema>;

function toLocalDateTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function formValues(decision: Decision): FramingInput {
  return {
    title: decision.title,
    decision_question: decision.decision_question,
    purpose: decision.purpose,
    context: decision.context,
    scope: decision.scope,
    contribution_guidance: decision.contribution_guidance,
    urgency: decision.urgency,
    target_decision_date: decision.target_decision_date ?? "",
    contribution_deadline: toLocalDateTime(decision.contribution_deadline),
    owner_id: decision.owner.id,
  };
}

export function DecisionFramingForm({
  decision,
  isSaving,
  onSave,
  memberships,
}: {
  decision: Decision;
  isSaving: boolean;
  onSave: (input: DecisionUpdateInput) => void;
  memberships: Membership[];
}) {
  const form = useForm<FramingInput>({
    resolver: zodResolver(framingSchema),
    defaultValues: formValues(decision),
  });

  useEffect(() => {
    form.reset(formValues(decision));
  }, [decision, form]);

  const submit = (values: FramingInput) => {
    onSave({
      title: values.title,
      decision_question: values.decision_question,
      purpose: values.purpose,
      context: values.context,
      scope: values.scope,
      contribution_guidance: values.contribution_guidance,
      urgency: values.urgency,
      target_decision_date: values.target_decision_date || null,
      contribution_deadline: values.contribution_deadline
        ? new Date(values.contribution_deadline).toISOString()
        : null,
      owner_id: values.owner_id,
    });
  };

  return (
    <form className="framing-form" onSubmit={form.handleSubmit(submit)} noValidate>
      <div className="form-row">
        <div>
          <label htmlFor="framing-title">Working title</label>
          <input
            id="framing-title"
            {...form.register("title")}
            disabled={!decision.can_edit}
          />
          <FieldError message={form.formState.errors.title?.message} />
        </div>
        <div>
          <label htmlFor="framing-urgency">Urgency</label>
          <select
            id="framing-urgency"
            {...form.register("urgency")}
            disabled={!decision.can_edit}
          >
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <label htmlFor="decision-owner">Decision owner</label>
      <select
        id="decision-owner"
        {...form.register("owner_id")}
        disabled={!decision.can_edit}
      >
        {!memberships.some(
          (membership) =>
            membership.status === "active" &&
            membership.user.id === decision.owner.id,
        ) ? (
          <option value={decision.owner.id}>
            {decision.owner.first_name || decision.owner.last_name
              ? `${decision.owner.first_name} ${decision.owner.last_name}`.trim()
              : decision.owner.email}
          </option>
        ) : null}
        {memberships
          .filter((membership) => membership.status === "active")
          .map((membership) => (
            <option value={membership.user.id} key={membership.id}>
              {membership.user.first_name || membership.user.last_name
                ? `${membership.user.first_name} ${membership.user.last_name}`.trim()
                : membership.user.email}
            </option>
          ))}
      </select>
      <FieldError message={form.formState.errors.owner_id?.message} />

      <label htmlFor="framing-question">Decision question</label>
      <textarea id="framing-question" rows={3} {...form.register("decision_question")} disabled={!decision.can_edit} />
      <FieldError message={form.formState.errors.decision_question?.message} />

      <label htmlFor="framing-purpose">Purpose</label>
      <textarea id="framing-purpose" rows={3} {...form.register("purpose")} disabled={!decision.can_edit} />
      <FieldError message={form.formState.errors.purpose?.message} />

      <label htmlFor="framing-context">Context</label>
      <textarea id="framing-context" rows={5} {...form.register("context")} disabled={!decision.can_edit} />
      <FieldError message={form.formState.errors.context?.message} />

      <label htmlFor="framing-scope">Scope</label>
      <textarea id="framing-scope" rows={3} {...form.register("scope")} disabled={!decision.can_edit} />
      <FieldError message={form.formState.errors.scope?.message} />

      <label htmlFor="framing-guidance">Contribution boundaries</label>
      <textarea
        id="framing-guidance"
        rows={4}
        {...form.register("contribution_guidance")}
        disabled={!decision.can_edit}
      />
      <FieldError message={form.formState.errors.contribution_guidance?.message} />

      <div className="form-row">
        <div>
          <label htmlFor="target-decision-date">Target decision date</label>
          <input
            id="target-decision-date"
            type="date"
            {...form.register("target_decision_date")}
            disabled={!decision.can_edit}
          />
        </div>
        <div>
          <label htmlFor="contribution-deadline">Contribution deadline</label>
          <input
            id="contribution-deadline"
            type="datetime-local"
            {...form.register("contribution_deadline")}
            disabled={!decision.can_edit}
          />
        </div>
      </div>

      {decision.can_edit ? (
        <button className="button button--primary" type="submit" disabled={isSaving}>
          {isSaving ? "Saving…" : "Save framing"}
        </button>
      ) : (
        <p className="muted compact-note">Framing fields are read-only in this lifecycle state.</p>
      )}
    </form>
  );
}
