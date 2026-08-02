import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { MyWorkPanel } from "../portfolio/MyWorkPanel";
import { createOrganisation, listOrganisations } from "./api";

const organisationSchema = z.object({
  name: z.string().trim().min(2, "Enter an organisation name.").max(200),
  slug: z
    .string()
    .trim()
    .min(2, "Enter a URL identifier.")
    .max(80)
    .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, "Use lowercase letters, numbers, and hyphens."),
});

type OrganisationInput = z.infer<typeof organisationSchema>;

export function OrganisationListPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const queryClient = useQueryClient();
  const organisations = useQuery({ queryKey: ["organisations"], queryFn: listOrganisations });
  const form = useForm<OrganisationInput>({
    resolver: zodResolver(organisationSchema),
    defaultValues: { name: "", slug: "" },
  });
  const create = useMutation({
    mutationFn: createOrganisation,
    onSuccess: async () => {
      form.reset();
      setCreateOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["organisations"] });
    },
  });

  useEffect(() => {
    if (!createOpen) return undefined;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setCreateOpen(false);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [createOpen]);

  return (
    <div className="home-dashboard">
      <MyWorkPanel />

      <section className="organisation-section" aria-labelledby="organisations-title">
        <div className="section-heading section-heading--polished">
          <div>
            <p className="eyebrow">Your decision environments</p>
            <h2 id="organisations-title">Organisations</h2>
            <p className="muted">Enter a governed tenant or create a new organisational boundary.</p>
          </div>
          <button className="button button--primary button--with-icon" type="button" onClick={() => setCreateOpen(true)}>
            <Icon name="plus" size={18} />
            <span>New organisation</span>
          </button>
        </div>

        {organisations.isError ? <StatusMessage kind="error">Your organisations could not be loaded.</StatusMessage> : null}
        {organisations.isPending ? <div className="organisation-grid"><span className="organisation-card-skeleton" /><span className="organisation-card-skeleton" /></div> : null}
        {organisations.data?.length === 0 ? (
          <div className="empty-state empty-state--polished">
            <span className="empty-state__icon"><Icon name="building" /></span>
            <h2>No organisations yet</h2>
            <p>Create the first tenant to establish its owner and governance boundary.</p>
            <button className="button button--primary button--with-icon" type="button" onClick={() => setCreateOpen(true)}><Icon name="plus" size={18} />Create organisation</button>
          </div>
        ) : null}
        <div className="organisation-grid">
          {organisations.data?.map((organisation) => (
            <Link className="organisation-card organisation-card--premium" to={`/organisations/${organisation.id}`} key={organisation.id}>
              <span className="organisation-card__avatar" aria-hidden="true">{organisation.name.slice(0, 1).toUpperCase()}</span>
              <div className="organisation-card__copy">
                <h3>{organisation.name}</h3>
                <p>/{organisation.slug}</p>
                <span className="role-badge role-badge--subtle">{organisation.current_user_role}</span>
              </div>
              <span className="organisation-card__arrow"><Icon name="arrow-right" /></span>
            </Link>
          ))}
        </div>
      </section>

      {createOpen ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.currentTarget === event.target) setCreateOpen(false);
        }}>
          <section className="modal-panel" role="dialog" aria-modal="true" aria-labelledby="create-organisation-title">
            <header className="modal-panel__header">
              <div><p className="eyebrow">New tenant</p><h2 id="create-organisation-title">Create an organisation</h2></div>
              <button className="icon-button" type="button" onClick={() => setCreateOpen(false)} aria-label="Close"><Icon name="close" /></button>
            </header>
            <p className="muted">You will become the first owner. Members and governance can be configured after creation.</p>
            {create.error ? <StatusMessage kind="error">{create.error instanceof ApiError ? create.error.message : "Creation failed."}</StatusMessage> : null}
            <form className="modal-form" onSubmit={form.handleSubmit((values) => create.mutate(values))} noValidate>
              <label htmlFor="organisation-name">Organisation name</label>
              <input id="organisation-name" autoFocus placeholder="e.g. AgriNova Decision Lab" {...form.register("name")} />
              <FieldError message={form.formState.errors.name?.message} />

              <label htmlFor="organisation-slug">URL identifier</label>
              <input id="organisation-slug" placeholder="e.g. agrinova-decision-lab" {...form.register("slug")} />
              <FieldError message={form.formState.errors.slug?.message} />
              <p className="field-hint">Lowercase letters, numbers, and hyphens only.</p>

              <div className="modal-actions">
                <button className="button button--secondary" type="button" onClick={() => setCreateOpen(false)}>Cancel</button>
                <button className="button button--primary" type="submit" disabled={create.isPending}>{create.isPending ? "Creating…" : "Create organisation"}</button>
              </div>
            </form>
          </section>
        </div>
      ) : null}
    </div>
  );
}
