import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { Membership } from "../../lib/types";
import { createCriterion, listCriteria, updateCriterion } from "./api";

const criterionSchema = z
  .object({
    title: z.string().trim().min(3, "Enter a concise criterion title.").max(240),
    description: z
      .string()
      .trim()
      .min(10, "Explain what this criterion measures and why it matters.")
      .max(12000),
    measurement_note: z.string().trim().max(4000),
    direction: z.enum(["maximize", "minimize"]),
    weight: z.number().int().min(0).max(100),
    weight_rationale: z.string().trim().max(4000),
    is_must_have: z.boolean(),
    threshold_note: z.string().trim().max(4000),
    owner_id: z.string(),
  })
  .superRefine((value, context) => {
    if (value.is_must_have && !value.threshold_note) {
      context.addIssue({
        code: "custom",
        path: ["threshold_note"],
        message: "A must-have criterion requires a stated threshold.",
      });
    }
  });

type CriterionForm = z.infer<typeof criterionSchema>;

type CriteriaSectionProps = {
  decisionId: string;
  canContribute: boolean;
  memberships: Membership[];
};

function memberName(membership: Membership): string {
  const fullName = `${membership.user.first_name} ${membership.user.last_name}`.trim();
  return fullName || membership.user.email;
}

export function CriteriaSection({
  decisionId,
  canContribute,
  memberships,
}: CriteriaSectionProps) {
  const activeMemberships = memberships.filter((item) => item.status === "active");
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["decisions", decisionId, "criteria"],
    queryFn: () => listCriteria(decisionId),
  });
  const form = useForm<CriterionForm>({
    resolver: zodResolver(criterionSchema),
    defaultValues: {
      title: "",
      description: "",
      measurement_note: "",
      direction: "maximize",
      weight: 20,
      weight_rationale: "",
      is_must_have: false,
      threshold_note: "",
      owner_id: "",
    },
  });

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["decisions", decisionId, "criteria"],
    });
    await queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] });
  };

  const create = useMutation({
    mutationFn: (values: CriterionForm) =>
      createCriterion(decisionId, {
        ...values,
        owner_id: values.owner_id || undefined,
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
      input: Parameters<typeof updateCriterion>[1];
    }) => updateCriterion(id, input),
    onSuccess: refresh,
  });

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <p className="eyebrow">What matters, and how much</p>
        <h2>Criteria</h2>
        <p className="muted">
          Agree what will be compared and how heavily it counts before scoring any option.
          A criterion can be marked must-have to rule out options that fail its threshold.
        </p>
        {query.isPending ? <p>Loading criteria…</p> : null}
        {query.isError ? (
          <StatusMessage kind="error">Criteria could not be loaded.</StatusMessage>
        ) : null}
        <div className="reasoning-list">
          {query.data?.map((item) => (
            <article className="reasoning-card" key={item.id}>
              <div className="reasoning-card__heading">
                <div>
                  <h3>{item.title}</h3>
                  <div className="inline-badges">
                    <span className="status-badge">Weight {item.weight}</span>
                    <span className="status-badge">{item.direction_label}</span>
                    {item.is_must_have ? <span className="role-badge">Must-have</span> : null}
                    <span className="status-badge">{item.status_label}</span>
                  </div>
                </div>
                {item.can_edit ? (
                  <select
                    aria-label={`Status for ${item.title}`}
                    value={item.status}
                    disabled={update.isPending}
                    onChange={(event) =>
                      update.mutate({
                        id: item.id,
                        input: { status: event.target.value as "active" | "retired" },
                      })
                    }
                  >
                    <option value="active">Active</option>
                    <option value="retired">Retired</option>
                  </select>
                ) : null}
              </div>
              <p>{item.description}</p>
              {item.measurement_note ? (
                <p>
                  <strong>Measured by:</strong> {item.measurement_note}
                </p>
              ) : null}
              {item.is_must_have && item.threshold_note ? (
                <p>
                  <strong>Threshold:</strong> {item.threshold_note}
                </p>
              ) : null}
              {item.weight_rationale ? (
                <p>
                  <strong>Why this weight:</strong> {item.weight_rationale}
                </p>
              ) : null}
              <p className="table-secondary">Owner: {item.owner.email}</p>
              {item.can_edit ? (
                <label className="inline-owner-control">
                  Accountable owner
                  <select
                    aria-label={`Accountable owner for ${item.title}`}
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
            </article>
          ))}
          {query.data?.length === 0 ? (
            <p className="muted">No criteria have been recorded.</p>
          ) : null}
        </div>
      </section>

      <aside className="side-panel">
        <p className="eyebrow">Human-agreed basis for comparison</p>
        <h2>Add a criterion</h2>
        {!canContribute ? (
          <p className="muted">New criteria cannot be added in this state by your role.</p>
        ) : (
          <form
            onSubmit={form.handleSubmit((values) => create.mutate(values))}
            noValidate
          >
            <label htmlFor="criterion-title">Title</label>
            <input id="criterion-title" {...form.register("title")} />
            <FieldError message={form.formState.errors.title?.message} />

            <label htmlFor="criterion-description">Description</label>
            <textarea
              id="criterion-description"
              rows={4}
              {...form.register("description")}
            />
            <FieldError message={form.formState.errors.description?.message} />

            <label htmlFor="criterion-measurement">Measurement scale or unit</label>
            <textarea
              id="criterion-measurement"
              rows={2}
              {...form.register("measurement_note")}
            />

            <div className="form-row">
              <div>
                <label htmlFor="criterion-direction">Direction of preference</label>
                <select id="criterion-direction" {...form.register("direction")}>
                  <option value="maximize">Higher is better</option>
                  <option value="minimize">Lower is better</option>
                </select>
              </div>
              <div>
                <label htmlFor="criterion-weight">Weight (0-100)</label>
                <input
                  id="criterion-weight"
                  type="number"
                  min={0}
                  max={100}
                  {...form.register("weight", { valueAsNumber: true })}
                />
              </div>
            </div>

            <label htmlFor="criterion-weight-rationale">Why this weight</label>
            <textarea
              id="criterion-weight-rationale"
              rows={2}
              {...form.register("weight_rationale")}
            />

            <label className="checkbox-row" htmlFor="criterion-must-have">
              <input
                id="criterion-must-have"
                type="checkbox"
                {...form.register("is_must_have")}
              />
              This is a must-have: options failing it cannot be selected
            </label>

            <label htmlFor="criterion-threshold">Minimum acceptable bar</label>
            <textarea
              id="criterion-threshold"
              rows={2}
              {...form.register("threshold_note")}
            />
            <FieldError message={form.formState.errors.threshold_note?.message} />

            <label htmlFor="criterion-owner">Accountable owner</label>
            <select id="criterion-owner" {...form.register("owner_id")}>
              <option value="">Me</option>
              {activeMemberships.map((membership) => (
                <option key={membership.user.id} value={membership.user.id}>
                  {memberName(membership)}
                </option>
              ))}
            </select>

            {create.error ? (
              <StatusMessage kind="error">
                {create.error instanceof ApiError
                  ? create.error.message
                  : "The criterion could not be saved."}
              </StatusMessage>
            ) : null}
            <button
              className="button button--primary button--full"
              type="submit"
              disabled={create.isPending}
            >
              {create.isPending ? "Saving…" : "Add criterion"}
            </button>
          </form>
        )}
      </aside>
    </div>
  );
}
