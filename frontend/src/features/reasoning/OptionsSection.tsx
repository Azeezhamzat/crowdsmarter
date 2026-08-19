import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getTerminology } from "../../lib/terminology";
import { createOption, listOptions, updateOption } from "./api";

const optionSchema = z
  .object({
    title: z.string().trim().min(3, "Enter a clear option title.").max(240),
    description: z
      .string()
      .trim()
      .min(10, "Describe what this option involves.")
      .max(12000),
    expected_benefits: z.string().trim().max(8000),
    tradeoffs: z.string().trim().max(8000),
    is_status_quo: z.boolean(),
    estimated_cost: z.string().trim(),
    cost_notes: z.string().trim().max(4000),
    resource_notes: z.string().trim().max(4000),
    implementation_time_estimate: z.string().trim().max(120),
    reversibility: z.enum([
      "",
      "easily_reversible",
      "partially_reversible",
      "difficult_to_reverse",
      "irreversible",
    ]),
    is_experiment: z.boolean(),
    experiment_notes: z.string().trim().max(4000),
    depends_on_ids: z.array(z.string()),
    mutually_exclusive_with_ids: z.array(z.string()),
  })
  .superRefine((value, context) => {
    if (value.is_experiment && !value.experiment_notes) {
      context.addIssue({
        code: "custom",
        path: ["experiment_notes"],
        message: "Describe the bounded experiment this option represents.",
      });
    }
  });

type OptionForm = z.infer<typeof optionSchema>;

type OptionsSectionProps = {
  decisionId: string;
  canContribute: boolean;
  templateKey?: string | null;
};

export function OptionsSection({
  decisionId,
  canContribute,
  templateKey,
}: OptionsSectionProps) {
  const terms = getTerminology(templateKey);
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["decisions", decisionId, "options"],
    queryFn: () => listOptions(decisionId),
  });
  const form = useForm<OptionForm>({
    resolver: zodResolver(optionSchema),
    defaultValues: {
      title: "",
      description: "",
      expected_benefits: "",
      tradeoffs: "",
      is_status_quo: false,
      estimated_cost: "",
      cost_notes: "",
      resource_notes: "",
      implementation_time_estimate: "",
      reversibility: "",
      is_experiment: false,
      experiment_notes: "",
      depends_on_ids: [],
      mutually_exclusive_with_ids: [],
    },
  });

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["decisions", decisionId, "options"],
    });
    await queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] });
  };

  const create = useMutation({
    mutationFn: (values: OptionForm) =>
      createOption(decisionId, {
        ...values,
        estimated_cost: values.estimated_cost ? Number(values.estimated_cost) : null,
        reversibility: values.reversibility || undefined,
      }),
    onSuccess: async () => {
      form.reset();
      await refresh();
    },
  });
  const changeStatus = useMutation({
    mutationFn: ({
      id,
      status,
    }: {
      id: string;
      status: "active" | "withdrawn";
    }) => updateOption(id, { status }),
    onSuccess: refresh,
  });

  const activeOptions = (query.data ?? []).filter((item) => item.status === "active");
  const titleFor = (id: string) => query.data?.find((item) => item.id === id)?.title ?? id;

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <p className="eyebrow">Alternatives</p>
        <h2>{terms.optionNounPlural}</h2>
        <p className="muted">
          Preserve credible alternatives, including the status quo where it is a
          real choice.
        </p>
        {query.isPending ? <p>Loading {terms.optionNounPlural.toLowerCase()}…</p> : null}
        {query.isError ? (
          <StatusMessage kind="error">{terms.optionNounPlural} could not be loaded.</StatusMessage>
        ) : null}
        <div className="reasoning-list">
          {query.data?.map((option) => (
            <article
              className={`reasoning-card${
                option.status !== "active" ? " reasoning-card--inactive" : ""
              }`}
              key={option.id}
            >
              <div className="reasoning-card__heading">
                <div>
                  <h3>{option.title}</h3>
                  <div className="inline-badges">
                    <span className="status-badge">{option.status_label}</span>
                    {option.is_status_quo ? (
                      <span className="role-badge">Status quo</span>
                    ) : null}
                    {option.is_experiment ? (
                      <span className="role-badge">Experiment</span>
                    ) : null}
                    {option.reversibility ? (
                      <span className="status-badge">{option.reversibility_label}</span>
                    ) : null}
                  </div>
                </div>
                {option.can_edit ? (
                  <button
                    className="button button--quiet"
                    type="button"
                    disabled={changeStatus.isPending}
                    onClick={() =>
                      changeStatus.mutate({
                        id: option.id,
                        status:
                          option.status === "active" ? "withdrawn" : "active",
                      })
                    }
                  >
                    {option.status === "active" ? "Withdraw" : "Restore"}
                  </button>
                ) : null}
              </div>
              <p>{option.description}</p>
              {option.expected_benefits ? (
                <div>
                  <strong>Expected benefits</strong>
                  <p>{option.expected_benefits}</p>
                </div>
              ) : null}
              {option.tradeoffs ? (
                <div>
                  <strong>Trade-offs</strong>
                  <p>{option.tradeoffs}</p>
                </div>
              ) : null}
              {option.estimated_cost ? (
                <p>
                  <strong>{terms.amountFieldLabel}:</strong> {option.estimated_cost}
                  {option.cost_notes ? ` — ${option.cost_notes}` : ""}
                </p>
              ) : null}
              {option.resource_notes ? (
                <p>
                  <strong>Resources:</strong> {option.resource_notes}
                </p>
              ) : null}
              {option.implementation_time_estimate ? (
                <p>
                  <strong>Implementation time:</strong> {option.implementation_time_estimate}
                </p>
              ) : null}
              {option.is_experiment && option.experiment_notes ? (
                <p>
                  <strong>Experiment:</strong> {option.experiment_notes}
                </p>
              ) : null}
              {option.depends_on_ids.length ? (
                <p>
                  <strong>Depends on:</strong>{" "}
                  {option.depends_on_ids.map(titleFor).join(", ")}
                </p>
              ) : null}
              {option.mutually_exclusive_with_ids.length ? (
                <p>
                  <strong>Cannot combine with:</strong>{" "}
                  {option.mutually_exclusive_with_ids.map(titleFor).join(", ")}
                </p>
              ) : null}
              <p className="table-secondary">
                Proposed by {option.proposed_by.email}
              </p>
            </article>
          ))}
          {query.data?.length === 0 ? (
            <p className="muted">No {terms.optionNounPlural.toLowerCase()} have been recorded.</p>
          ) : null}
        </div>
      </section>

      <aside className="side-panel">
        <p className="eyebrow">Human contribution</p>
        <h2>{terms.addOptionCta}</h2>
        {!canContribute ? (
          <p className="muted">
            Your role or the current lifecycle state does not permit new {terms.optionNounPlural.toLowerCase()}.
          </p>
        ) : (
          <form
            onSubmit={form.handleSubmit((values) => create.mutate(values))}
            noValidate
          >
            <label htmlFor="option-title">Title</label>
            <input id="option-title" {...form.register("title")} />
            <FieldError message={form.formState.errors.title?.message} />

            <label htmlFor="option-description">Description</label>
            <textarea
              id="option-description"
              rows={5}
              {...form.register("description")}
            />
            <FieldError message={form.formState.errors.description?.message} />

            <label htmlFor="option-benefits">Expected benefits</label>
            <textarea
              id="option-benefits"
              rows={3}
              {...form.register("expected_benefits")}
            />

            <label htmlFor="option-tradeoffs">Trade-offs</label>
            <textarea
              id="option-tradeoffs"
              rows={3}
              {...form.register("tradeoffs")}
            />

            <div className="form-row">
              <div>
                <label htmlFor="option-cost">{terms.amountFieldLabel}</label>
                <input
                  id="option-cost"
                  type="number"
                  min={0}
                  step="0.01"
                  {...form.register("estimated_cost")}
                />
              </div>
              <div>
                <label htmlFor="option-implementation-time">Implementation time</label>
                <input
                  id="option-implementation-time"
                  placeholder="e.g. 3-6 months"
                  {...form.register("implementation_time_estimate")}
                />
              </div>
            </div>

            <label htmlFor="option-cost-notes">Cost notes</label>
            <textarea id="option-cost-notes" rows={2} {...form.register("cost_notes")} />

            <label htmlFor="option-resources">Resources required</label>
            <textarea id="option-resources" rows={2} {...form.register("resource_notes")} />

            <label htmlFor="option-reversibility">Reversibility</label>
            <select id="option-reversibility" {...form.register("reversibility")}>
              <option value="">Not assessed</option>
              <option value="easily_reversible">Easily reversible</option>
              <option value="partially_reversible">Partially reversible</option>
              <option value="difficult_to_reverse">Difficult to reverse</option>
              <option value="irreversible">Irreversible</option>
            </select>

            <label className="checkbox-row" htmlFor="option-is-experiment">
              <input
                id="option-is-experiment"
                type="checkbox"
                {...form.register("is_experiment")}
              />
              This is a minimum-viable experiment, not the full commitment
            </label>
            <label htmlFor="option-experiment-notes">Experiment scope</label>
            <textarea
              id="option-experiment-notes"
              rows={2}
              {...form.register("experiment_notes")}
            />
            <FieldError message={form.formState.errors.experiment_notes?.message} />

            {activeOptions.length ? (
              <>
                <label htmlFor="option-depends-on">Depends on</label>
                <select
                  id="option-depends-on"
                  multiple
                  size={Math.min(4, activeOptions.length)}
                  value={form.watch("depends_on_ids")}
                  onChange={(event) =>
                    form.setValue(
                      "depends_on_ids",
                      Array.from(event.target.selectedOptions, (item) => item.value),
                    )
                  }
                >
                  {activeOptions.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.title}
                    </option>
                  ))}
                </select>

                <label htmlFor="option-mutually-exclusive">Cannot be combined with</label>
                <select
                  id="option-mutually-exclusive"
                  multiple
                  size={Math.min(4, activeOptions.length)}
                  value={form.watch("mutually_exclusive_with_ids")}
                  onChange={(event) =>
                    form.setValue(
                      "mutually_exclusive_with_ids",
                      Array.from(event.target.selectedOptions, (item) => item.value),
                    )
                  }
                >
                  {activeOptions.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.title}
                    </option>
                  ))}
                </select>
              </>
            ) : null}

            <label className="checkbox-row" htmlFor="option-status-quo">
              <input
                id="option-status-quo"
                type="checkbox"
                {...form.register("is_status_quo")}
              />
              This represents continuing the current approach
            </label>

            {create.error ? (
              <StatusMessage kind="error">
                {create.error instanceof ApiError
                  ? create.error.message
                  : `The ${terms.optionNoun.toLowerCase()} could not be saved.`}
              </StatusMessage>
            ) : null}
            <button
              className="button button--primary button--full"
              type="submit"
              disabled={create.isPending}
            >
              {create.isPending ? "Saving…" : `Add ${terms.optionNoun.toLowerCase()}`}
            </button>
          </form>
        )}
      </aside>
    </div>
  );
}
