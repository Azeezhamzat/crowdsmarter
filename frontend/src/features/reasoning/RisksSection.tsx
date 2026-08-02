import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { Membership } from "../../lib/types";
import { createRisk, listOptions, listRisks, updateRisk } from "./api";

const riskSchema = z
  .object({
    option_id: z.string(),
    title: z.string().trim().min(3, "Enter a concise risk title.").max(240),
    description: z
      .string()
      .trim()
      .min(10, "Describe the uncertain event and consequence.")
      .max(12000),
    likelihood: z.number().int().min(1).max(5),
    impact: z.number().int().min(1).max(5),
    response_strategy: z.enum([
      "accept",
      "avoid",
      "mitigate",
      "transfer",
      "monitor",
    ]),
    mitigation_plan: z.string().trim().max(12000),
    owner_id: z.string(),
    review_date: z.string(),
  })
  .superRefine((value, context) => {
    const actionRequired = ["avoid", "mitigate", "transfer"].includes(
      value.response_strategy,
    );
    if (actionRequired && !value.mitigation_plan) {
      context.addIssue({
        code: "custom",
        path: ["mitigation_plan"],
        message: "This response strategy requires an action plan.",
      });
    }
  });

type RiskForm = z.infer<typeof riskSchema>;

type RisksSectionProps = {
  decisionId: string;
  canContribute: boolean;
  memberships: Membership[];
};

function memberName(membership: Membership): string {
  const fullName = `${membership.user.first_name} ${membership.user.last_name}`.trim();
  return fullName || membership.user.email;
}

export function RisksSection({
  decisionId,
  canContribute,
  memberships,
}: RisksSectionProps) {
  const activeMemberships = memberships.filter((item) => item.status === "active");
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["decisions", decisionId, "risks"],
    queryFn: () => listRisks(decisionId),
  });
  const options = useQuery({
    queryKey: ["decisions", decisionId, "options"],
    queryFn: () => listOptions(decisionId),
  });
  const form = useForm<RiskForm>({
    resolver: zodResolver(riskSchema),
    defaultValues: {
      option_id: "",
      title: "",
      description: "",
      likelihood: 3,
      impact: 3,
      response_strategy: "monitor",
      mitigation_plan: "",
      owner_id: "",
      review_date: "",
    },
  });

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["decisions", decisionId, "risks"],
    });
    await queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] });
  };

  const create = useMutation({
    mutationFn: (values: RiskForm) =>
      createRisk(decisionId, {
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
      input: Parameters<typeof updateRisk>[1];
    }) => updateRisk(id, input),
    onSuccess: refresh,
  });

  const optionTitle = (id: string | null) =>
    options.data?.find((item) => item.id === id)?.title;

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <p className="eyebrow">Uncertainty and response</p>
        <h2>Risks</h2>
        <p className="muted">
          Record uncertain events, their consequences, and the person accountable for the
          response.
        </p>
        {query.isPending ? <p>Loading risks…</p> : null}
        {query.isError ? (
          <StatusMessage kind="error">Risks could not be loaded.</StatusMessage>
        ) : null}
        <div className="reasoning-list">
          {query.data?.map((item) => (
            <article className="reasoning-card" key={item.id}>
              <div className="reasoning-card__heading">
                <div>
                  <h3>{item.title}</h3>
                  <div className="inline-badges">
                    <span className="risk-score">Score {item.score}/25</span>
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
                        input: {
                          status: event.target.value as
                            | "open"
                            | "monitoring"
                            | "mitigated"
                            | "accepted"
                            | "closed",
                        },
                      })
                    }
                  >
                    <option value="open">Open</option>
                    <option value="monitoring">Monitoring</option>
                    <option value="mitigated">Mitigated</option>
                    <option value="accepted">Accepted</option>
                    <option value="closed">Closed</option>
                  </select>
                ) : null}
              </div>
              <p>{item.description}</p>
              <p>
                <strong>Assessment:</strong> likelihood {item.likelihood}/5 · impact{
                  " "
                }
                {item.impact}/5
              </p>
              <p>
                <strong>Response:</strong> {item.response_strategy_label}
              </p>
              {item.mitigation_plan ? (
                <p>
                  <strong>Plan:</strong> {item.mitigation_plan}
                </p>
              ) : null}
              {optionTitle(item.option_id) ? (
                <p>
                  <strong>Related option:</strong> {optionTitle(item.option_id)}
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
            <p className="muted">No risks have been recorded.</p>
          ) : null}
        </div>
      </section>

      <aside className="side-panel">
        <p className="eyebrow">Human-owned response</p>
        <h2>Add a risk</h2>
        {!canContribute ? (
          <p className="muted">New risks cannot be added in this state by your role.</p>
        ) : (
          <form
            onSubmit={form.handleSubmit((values) => create.mutate(values))}
            noValidate
          >
            <label htmlFor="risk-title">Title</label>
            <input id="risk-title" {...form.register("title")} />
            <FieldError message={form.formState.errors.title?.message} />

            <label htmlFor="risk-description">Description and consequence</label>
            <textarea
              id="risk-description"
              rows={5}
              {...form.register("description")}
            />
            <FieldError message={form.formState.errors.description?.message} />

            <label htmlFor="risk-option">Related option</label>
            <select id="risk-option" {...form.register("option_id")}>
              <option value="">Whole decision</option>
              {options.data
                ?.filter((item) => item.status === "active")
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))}
            </select>

            <div className="form-row">
              <div>
                <label htmlFor="risk-likelihood">Likelihood (1–5)</label>
                <input
                  id="risk-likelihood"
                  type="number"
                  min={1}
                  max={5}
                  {...form.register("likelihood", { valueAsNumber: true })}
                />
              </div>
              <div>
                <label htmlFor="risk-impact">Impact (1–5)</label>
                <input
                  id="risk-impact"
                  type="number"
                  min={1}
                  max={5}
                  {...form.register("impact", { valueAsNumber: true })}
                />
              </div>
            </div>

            <label htmlFor="risk-response">Response strategy</label>
            <select id="risk-response" {...form.register("response_strategy")}>
              <option value="accept">Accept</option>
              <option value="avoid">Avoid</option>
              <option value="mitigate">Mitigate</option>
              <option value="transfer">Transfer</option>
              <option value="monitor">Monitor</option>
            </select>

            <label htmlFor="risk-plan">Response or mitigation plan</label>
            <textarea
              id="risk-plan"
              rows={4}
              {...form.register("mitigation_plan")}
            />
            <FieldError message={form.formState.errors.mitigation_plan?.message} />

            <label htmlFor="risk-owner">Accountable owner</label>
            <select id="risk-owner" {...form.register("owner_id")}>
              <option value="">Me</option>
              {activeMemberships.map((membership) => (
                <option key={membership.user.id} value={membership.user.id}>
                  {memberName(membership)}
                </option>
              ))}
            </select>

            <label htmlFor="risk-review-date">Review date</label>
            <input
              id="risk-review-date"
              type="date"
              {...form.register("review_date")}
            />

            {create.error ? (
              <StatusMessage kind="error">
                {create.error instanceof ApiError
                  ? create.error.message
                  : "The risk could not be saved."}
              </StatusMessage>
            ) : null}
            <button
              className="button button--primary button--full"
              type="submit"
              disabled={create.isPending}
            >
              {create.isPending ? "Saving…" : "Add risk"}
            </button>
          </form>
        )}
      </aside>
    </div>
  );
}
