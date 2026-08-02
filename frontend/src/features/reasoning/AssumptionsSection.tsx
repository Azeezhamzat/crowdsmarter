import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { Assumption, Membership } from "../../lib/types";
import {
  createAssumption,
  listAssumptions,
  listOptions,
  updateAssumption,
} from "./api";

const assumptionSchema = z.object({
  option_id: z.string(),
  statement: z.string().trim().min(8, "State the assumption clearly.").max(12000),
  rationale: z.string().trim().max(8000),
  impact_if_false: z
    .string()
    .trim()
    .min(8, "Explain what changes if this is false.")
    .max(8000),
  confidence: z.enum(["low", "medium", "high"]),
  owner_id: z.string(),
  review_date: z.string(),
});

type AssumptionForm = z.infer<typeof assumptionSchema>;

type AssumptionsSectionProps = {
  decisionId: string;
  canContribute: boolean;
  memberships: Membership[];
};

function memberName(membership: Membership): string {
  const fullName = `${membership.user.first_name} ${membership.user.last_name}`.trim();
  return fullName || membership.user.email;
}

function VerificationEditor({
  item,
  isSaving,
  onSave,
}: {
  item: Assumption;
  isSaving: boolean;
  onSave: (input: {
    verification_status:
      | "unverified"
      | "partially_verified"
      | "verified"
      | "invalidated";
    verification_notes: string;
  }) => void;
}) {
  const [status, setStatus] = useState(item.verification_status);
  const [notes, setNotes] = useState(item.verification_notes);

  return (
    <details className="record-actions">
      <summary>Update verification</summary>
      <div className="compact-form-row">
        <select
          aria-label={`Verification status for ${item.statement}`}
          value={status}
          onChange={(event) => setStatus(event.target.value as typeof status)}
        >
          <option value="unverified">Unverified</option>
          <option value="partially_verified">Partially verified</option>
          <option value="verified">Verified</option>
          <option value="invalidated">Invalidated</option>
        </select>
        <input
          aria-label={`Verification notes for ${item.statement}`}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="What was checked and what was found?"
        />
        <button
          className="button button--quiet"
          type="button"
          disabled={isSaving}
          onClick={() =>
            onSave({
              verification_status: status,
              verification_notes: notes,
            })
          }
        >
          Save verification
        </button>
      </div>
    </details>
  );
}

export function AssumptionsSection({
  decisionId,
  canContribute,
  memberships,
}: AssumptionsSectionProps) {
  const activeMemberships = memberships.filter((item) => item.status === "active");
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["decisions", decisionId, "assumptions"],
    queryFn: () => listAssumptions(decisionId),
  });
  const options = useQuery({
    queryKey: ["decisions", decisionId, "options"],
    queryFn: () => listOptions(decisionId),
  });
  const form = useForm<AssumptionForm>({
    resolver: zodResolver(assumptionSchema),
    defaultValues: {
      option_id: "",
      statement: "",
      rationale: "",
      impact_if_false: "",
      confidence: "medium",
      owner_id: "",
      review_date: "",
    },
  });

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["decisions", decisionId, "assumptions"],
    });
    await queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] });
  };

  const create = useMutation({
    mutationFn: (values: AssumptionForm) =>
      createAssumption(decisionId, {
        ...values,
        option_id: values.option_id || null,
        owner_id: values.owner_id || undefined,
        review_date: values.review_date || null,
      }),
    onSuccess: async () => {
      form.reset();
      await refresh();
    },
  });

  const update = useMutation({
    mutationFn: ({
      id,
      input,
    }: {
      id: string;
      input: Parameters<typeof updateAssumption>[1];
    }) => updateAssumption(id, input),
    onSuccess: refresh,
  });

  const optionTitle = (id: string | null) =>
    options.data?.find((item) => item.id === id)?.title;

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <p className="eyebrow">Exposed beliefs</p>
        <h2>Assumptions</h2>
        <p className="muted">
          Make consequential beliefs visible so they can be tested, challenged, and reviewed.
        </p>
        {query.isPending ? <p>Loading assumptions…</p> : null}
        {query.isError ? (
          <StatusMessage kind="error">Assumptions could not be loaded.</StatusMessage>
        ) : null}
        <div className="reasoning-list">
          {query.data?.map((item) => (
            <article
              className={`reasoning-card${
                item.status !== "active" ? " reasoning-card--inactive" : ""
              }`}
              key={item.id}
            >
              <div className="reasoning-card__heading">
                <div>
                  <h3>{item.statement}</h3>
                  <div className="inline-badges">
                    <span className="status-badge">
                      {item.verification_status_label}
                    </span>
                    <span className="role-badge">
                      {item.confidence_label} confidence
                    </span>
                  </div>
                </div>
                {item.can_edit ? (
                  <button
                    className="button button--quiet"
                    type="button"
                    disabled={update.isPending}
                    onClick={() =>
                      update.mutate({
                        id: item.id,
                        input: {
                          status: item.status === "active" ? "retired" : "active",
                        },
                      })
                    }
                  >
                    {item.status === "active" ? "Retire" : "Restore"}
                  </button>
                ) : null}
              </div>
              {item.rationale ? (
                <p>
                  <strong>Why it is believed:</strong> {item.rationale}
                </p>
              ) : null}
              <p>
                <strong>If false:</strong> {item.impact_if_false}
              </p>
              {optionTitle(item.option_id) ? (
                <p>
                  <strong>Related option:</strong> {optionTitle(item.option_id)}
                </p>
              ) : null}
              {item.verification_notes ? (
                <p>
                  <strong>Verification notes:</strong> {item.verification_notes}
                </p>
              ) : null}
              <p className="table-secondary">
                Owner: {item.owner.email}
                {item.review_date ? ` · review by ${item.review_date}` : ""}
              </p>
              {item.can_edit ? (
                <label className="inline-owner-control">
                  Accountable owner
                  <select
                    aria-label={`Accountable owner for ${item.statement}`}
                    value={item.owner.id}
                    disabled={update.isPending}
                    onChange={(event) =>
                      update.mutate({
                        id: item.id,
                        input: { owner_id: event.target.value },
                      })
                    }
                  >
                    {!activeMemberships.some(
                      (membership) => membership.user.id === item.owner.id,
                    ) ? (
                      <option value={item.owner.id}>{item.owner.email}</option>
                    ) : null}
                    {activeMemberships.map((membership) => (
                      <option key={membership.user.id} value={membership.user.id}>
                        {memberName(membership)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
              {item.can_edit && item.status === "active" ? (
                <VerificationEditor
                  item={item}
                  isSaving={update.isPending}
                  onSave={(input) => update.mutate({ id: item.id, input })}
                />
              ) : null}
            </article>
          ))}
          {query.data?.length === 0 ? (
            <p className="muted">No assumptions have been recorded.</p>
          ) : null}
        </div>
      </section>

      <aside className="side-panel">
        <p className="eyebrow">Testable belief</p>
        <h2>Add an assumption</h2>
        {!canContribute ? (
          <p className="muted">
            New assumptions cannot be added in this state by your role.
          </p>
        ) : (
          <form
            onSubmit={form.handleSubmit((values) => create.mutate(values))}
            noValidate
          >
            <label htmlFor="assumption-statement">Assumption</label>
            <textarea
              id="assumption-statement"
              rows={4}
              {...form.register("statement")}
            />
            <FieldError message={form.formState.errors.statement?.message} />

            <label htmlFor="assumption-rationale">Why do we believe this?</label>
            <textarea
              id="assumption-rationale"
              rows={3}
              {...form.register("rationale")}
            />

            <label htmlFor="assumption-impact">What changes if it is false?</label>
            <textarea
              id="assumption-impact"
              rows={4}
              {...form.register("impact_if_false")}
            />
            <FieldError message={form.formState.errors.impact_if_false?.message} />

            <label htmlFor="assumption-option">Related option</label>
            <select id="assumption-option" {...form.register("option_id")}>
              <option value="">Whole decision</option>
              {options.data
                ?.filter((item) => item.status === "active")
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))}
            </select>

            <label htmlFor="assumption-owner">Accountable owner</label>
            <select id="assumption-owner" {...form.register("owner_id")}>
              <option value="">Me</option>
              {activeMemberships.map((membership) => (
                <option key={membership.user.id} value={membership.user.id}>
                  {memberName(membership)}
                </option>
              ))}
            </select>

            <div className="form-row">
              <div>
                <label htmlFor="assumption-confidence">Confidence</label>
                <select
                  id="assumption-confidence"
                  {...form.register("confidence")}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div>
                <label htmlFor="assumption-review-date">Review date</label>
                <input
                  id="assumption-review-date"
                  type="date"
                  {...form.register("review_date")}
                />
              </div>
            </div>

            {create.error ? (
              <StatusMessage kind="error">
                {create.error instanceof ApiError
                  ? create.error.message
                  : "The assumption could not be saved."}
              </StatusMessage>
            ) : null}
            <button
              className="button button--primary button--full"
              type="submit"
              disabled={create.isPending}
            >
              {create.isPending ? "Saving…" : "Add assumption"}
            </button>
          </form>
        )}
      </aside>
    </div>
  );
}
