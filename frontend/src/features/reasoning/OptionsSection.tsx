import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { createOption, listOptions, updateOption } from "./api";

const optionSchema = z.object({
  title: z.string().trim().min(3, "Enter a clear option title.").max(240),
  description: z
    .string()
    .trim()
    .min(10, "Describe what this option involves.")
    .max(12000),
  expected_benefits: z.string().trim().max(8000),
  tradeoffs: z.string().trim().max(8000),
  is_status_quo: z.boolean(),
});

type OptionForm = z.infer<typeof optionSchema>;

type OptionsSectionProps = {
  decisionId: string;
  canContribute: boolean;
};

export function OptionsSection({
  decisionId,
  canContribute,
}: OptionsSectionProps) {
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
    },
  });

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["decisions", decisionId, "options"],
    });
    await queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] });
  };

  const create = useMutation({
    mutationFn: (input: OptionForm) => createOption(decisionId, input),
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

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <p className="eyebrow">Alternatives</p>
        <h2>Decision options</h2>
        <p className="muted">
          Preserve credible alternatives, including the status quo where it is a
          real choice.
        </p>
        {query.isPending ? <p>Loading options…</p> : null}
        {query.isError ? (
          <StatusMessage kind="error">Options could not be loaded.</StatusMessage>
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
              <p className="table-secondary">
                Proposed by {option.proposed_by.email}
              </p>
            </article>
          ))}
          {query.data?.length === 0 ? (
            <p className="muted">No options have been recorded.</p>
          ) : null}
        </div>
      </section>

      <aside className="side-panel">
        <p className="eyebrow">Human contribution</p>
        <h2>Add an option</h2>
        {!canContribute ? (
          <p className="muted">
            Your role or the current lifecycle state does not permit new options.
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
                  : "The option could not be saved."}
              </StatusMessage>
            ) : null}
            <button
              className="button button--primary button--full"
              type="submit"
              disabled={create.isPending}
            >
              {create.isPending ? "Saving…" : "Add option"}
            </button>
          </form>
        )}
      </aside>
    </div>
  );
}
