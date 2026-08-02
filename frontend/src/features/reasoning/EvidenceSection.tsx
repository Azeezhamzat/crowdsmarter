import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getDecision } from "../decisions/api";
import { listSources } from "../foresight/api";
import {
  createEvidence,
  listEvidence,
  listOptions,
  updateEvidence,
} from "./api";

const evidenceSchema = z
  .object({
    source_id: z.string(),
    option_id: z.string(),
    title: z
      .string()
      .trim()
      .min(3, "Enter a concise evidence title.")
      .max(240),
    summary: z
      .string()
      .trim()
      .min(10, "Summarise what the evidence indicates.")
      .max(12000),
    source_type: z.enum([
      "research",
      "internal_data",
      "expert_judgement",
      "stakeholder_input",
      "policy",
      "other",
    ]),
    source_reference: z.string().trim().max(500),
    source_url: z.union([
      z.literal(""),
      z.string().url("Enter a complete URL, including https://"),
    ]),
    stance: z.enum(["supports", "challenges", "mixed", "context"]),
    strength: z.enum(["low", "moderate", "high"]),
  })
  .refine((value) => value.source_id || value.source_reference || value.source_url, {
    message: "Choose a structured source or provide a source reference or URL.",
    path: ["source_reference"],
  });

type EvidenceForm = z.infer<typeof evidenceSchema>;

type EvidenceSectionProps = {
  decisionId: string;
  canContribute: boolean;
};

export function EvidenceSection({
  decisionId,
  canContribute,
}: EvidenceSectionProps) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["decisions", decisionId, "evidence"],
    queryFn: () => listEvidence(decisionId),
  });
  const options = useQuery({
    queryKey: ["decisions", decisionId, "options"],
    queryFn: () => listOptions(decisionId),
  });
  const decision = useQuery({
    queryKey: ["decisions", decisionId],
    queryFn: () => getDecision(decisionId),
  });
  const structuredSources = useQuery({
    queryKey: ["organisations", decision.data?.organisation_id, "foresight", "sources"],
    queryFn: () => listSources(decision.data?.organisation_id ?? ""),
    enabled: Boolean(decision.data?.organisation_id),
  });
  const form = useForm<EvidenceForm>({
    resolver: zodResolver(evidenceSchema),
    defaultValues: {
      source_id: "",
      option_id: "",
      title: "",
      summary: "",
      source_type: "research",
      source_reference: "",
      source_url: "",
      stance: "context",
      strength: "moderate",
    },
  });

  const refresh = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["decisions", decisionId, "evidence"],
    });
    await queryClient.invalidateQueries({ queryKey: ["decisions", decisionId] });
  };

  const create = useMutation({
    mutationFn: (values: EvidenceForm) =>
      createEvidence(decisionId, {
        ...values,
        source_id: values.source_id || null,
        option_id: values.option_id || null,
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
    }) => updateEvidence(id, { status }),
    onSuccess: refresh,
  });
  const optionTitle = (id: string | null) =>
    options.data?.find((item) => item.id === id)?.title;

  return (
    <div className="reasoning-grid">
      <section className="page-primary">
        <p className="eyebrow">Traceable support</p>
        <h2>Evidence</h2>
        <p className="muted">
          Record what a source indicates, where it came from, and whether it
          supports or challenges an option.
        </p>
        {query.isPending ? <p>Loading evidence…</p> : null}
        {query.isError ? (
          <StatusMessage kind="error">Evidence could not be loaded.</StatusMessage>
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
                  <h3>{item.title}</h3>
                  <div className="inline-badges">
                    <span className="status-badge">{item.stance_label}</span>
                    <span className="role-badge">
                      {item.strength_label} strength
                    </span>
                  </div>
                </div>
                {item.can_edit ? (
                  <button
                    className="button button--quiet"
                    type="button"
                    disabled={changeStatus.isPending}
                    onClick={() =>
                      changeStatus.mutate({
                        id: item.id,
                        status:
                          item.status === "active" ? "withdrawn" : "active",
                      })
                    }
                  >
                    {item.status === "active" ? "Withdraw" : "Restore"}
                  </button>
                ) : null}
              </div>
              <p>{item.summary}</p>
              {optionTitle(item.option_id) ? (
                <p>
                  <strong>Related option:</strong> {optionTitle(item.option_id)}
                </p>
              ) : null}
              <p>
                <strong>Source:</strong>{" "}
                {item.source_id
                  ? structuredSources.data?.find((source) => source.id === item.source_id)?.title ?? "Structured source"
                  : item.source_reference || item.source_url}
              </p>
              {item.source_url ? (
                <a href={item.source_url} target="_blank" rel="noreferrer">
                  Open source
                </a>
              ) : null}
              <p className="table-secondary">
                {item.source_type_label} · added by {item.created_by.email}
              </p>
            </article>
          ))}
          {query.data?.length === 0 ? (
            <p className="muted">No evidence has been recorded.</p>
          ) : null}
        </div>
      </section>

      <aside className="side-panel">
        <p className="eyebrow">Attributable source</p>
        <h2>Add evidence</h2>
        {!canContribute ? (
          <p className="muted">
            New evidence cannot be added in this state by your role.
          </p>
        ) : (
          <form
            onSubmit={form.handleSubmit((values) => create.mutate(values))}
            noValidate
          >
            <label htmlFor="evidence-title">Title</label>
            <input id="evidence-title" {...form.register("title")} />
            <FieldError message={form.formState.errors.title?.message} />

            <label htmlFor="evidence-summary">Summary</label>
            <textarea
              id="evidence-summary"
              rows={5}
              {...form.register("summary")}
            />
            <FieldError message={form.formState.errors.summary?.message} />

            <label htmlFor="evidence-option">Related option</label>
            <select id="evidence-option" {...form.register("option_id")}>
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
                <label htmlFor="evidence-type">Source type</label>
                <select id="evidence-type" {...form.register("source_type")}>
                  <option value="research">Research</option>
                  <option value="internal_data">Internal data</option>
                  <option value="expert_judgement">Expert judgement</option>
                  <option value="stakeholder_input">Stakeholder input</option>
                  <option value="policy">Policy or regulation</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label htmlFor="evidence-stance">Stance</label>
                <select id="evidence-stance" {...form.register("stance")}>
                  <option value="supports">Supports</option>
                  <option value="challenges">Challenges</option>
                  <option value="mixed">Mixed</option>
                  <option value="context">Context</option>
                </select>
              </div>
            </div>

            <label htmlFor="evidence-strength">Strength</label>
            <select id="evidence-strength" {...form.register("strength")}>
              <option value="low">Low</option>
              <option value="moderate">Moderate</option>
              <option value="high">High</option>
            </select>

            <label htmlFor="evidence-structured-source">Structured source</label>
            <select id="evidence-structured-source" {...form.register("source_id")}>
              <option value="">Use a manual reference instead</option>
              {structuredSources.data
                ?.filter((source) => source.status === "active")
                .map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.title} · {source.credibility_label}
                  </option>
                ))}
            </select>
            {decision.data ? (
              <a className="table-secondary" href={`/organisations/${decision.data.organisation_id}/foresight`}>
                Manage the organisation source library
              </a>
            ) : null}

            <label htmlFor="evidence-reference">Source reference</label>
            <input
              id="evidence-reference"
              placeholder="Report title, dataset, interview, policy…"
              {...form.register("source_reference")}
            />
            <FieldError
              message={form.formState.errors.source_reference?.message}
            />

            <label htmlFor="evidence-url">Source URL</label>
            <input
              id="evidence-url"
              type="url"
              placeholder="https://…"
              {...form.register("source_url")}
            />
            <FieldError message={form.formState.errors.source_url?.message} />

            {create.error ? (
              <StatusMessage kind="error">
                {create.error instanceof ApiError
                  ? create.error.message
                  : "Evidence could not be saved."}
              </StatusMessage>
            ) : null}
            <button
              className="button button--primary button--full"
              type="submit"
              disabled={create.isPending}
            >
              {create.isPending ? "Saving…" : "Add evidence"}
            </button>
          </form>
        )}
      </aside>
    </div>
  );
}
