import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router-dom";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import { getOrganisation } from "../organisations/api";
import { createWorkspace, listWorkspaces } from "./api";

const workspaceSchema = z.object({
  name: z.string().trim().min(2, "Enter a workspace name.").max(160),
  slug: z
    .string()
    .trim()
    .min(2, "Enter a URL identifier.")
    .max(80)
    .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, "Use lowercase letters, numbers, and hyphens."),
  description: z.string().trim().max(2000),
});

type WorkspaceInput = z.infer<typeof workspaceSchema>;

export function WorkspaceListPage() {
  const { organisationId: routeOrganisationId } = useParams<{ organisationId: string }>();
  const organisationId = routeOrganisationId ?? "";
  const queryClient = useQueryClient();
  const organisation = useQuery({
    queryKey: ["organisations", organisationId],
    queryFn: () => getOrganisation(organisationId),
    enabled: Boolean(organisationId),
  });
  const workspaces = useQuery({
    queryKey: ["organisations", organisationId, "workspaces"],
    queryFn: () => listWorkspaces(organisationId),
    enabled: Boolean(organisationId),
  });
  const form = useForm<WorkspaceInput>({
    resolver: zodResolver(workspaceSchema),
    defaultValues: { name: "", slug: "", description: "" },
  });
  const create = useMutation({
    mutationFn: (input: WorkspaceInput) => createWorkspace(organisationId, input),
    onSuccess: async () => {
      form.reset();
      await queryClient.invalidateQueries({
        queryKey: ["organisations", organisationId, "workspaces"],
      });
    },
  });

  const canManage = ["owner", "admin"].includes(
    organisation.data?.current_user_role ?? "",
  );

  return (
    <div>
      <Link className="back-link" to={`/organisations/${organisationId}`}>
        ← Organisation
      </Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Decision structure</p>
          <h1>{organisation.data?.name ?? "Workspaces"}</h1>
          <p className="muted">
            Keep related important decisions together without turning the platform into a project tracker.
          </p>
        </div>
      </div>

      <div className="page-grid">
        <section className="page-primary" aria-labelledby="workspaces-title">
          <h2 id="workspaces-title">Decision workspaces</h2>
          {workspaces.isPending ? <p>Loading workspaces…</p> : null}
          {workspaces.isError || organisation.isError ? (
            <StatusMessage kind="error">The workspaces could not be loaded.</StatusMessage>
          ) : null}
          <div className="card-list">
            {workspaces.data?.map((workspace) => (
              <Link
                className="organisation-card"
                to={`/workspaces/${workspace.id}`}
                key={workspace.id}
              >
                <div>
                  <div className="inline-heading">
                    <h2>{workspace.name}</h2>
                    {workspace.is_default ? <span className="role-badge">default</span> : null}
                  </div>
                  <p className="muted">
                    {workspace.description || "A focused area for related decisions."}
                  </p>
                </div>
                <span aria-hidden="true">→</span>
              </Link>
            ))}
          </div>
        </section>

        {canManage ? (
          <aside className="side-panel" aria-labelledby="create-workspace-title">
            <h2 id="create-workspace-title">Create a workspace</h2>
            <p className="muted">Add one only when a distinct decision area will reduce confusion.</p>
            {create.error ? (
              <StatusMessage kind="error">
                {create.error instanceof ApiError
                  ? create.error.message
                  : "The workspace could not be created."}
              </StatusMessage>
            ) : null}
            <form onSubmit={form.handleSubmit((values) => create.mutate(values))} noValidate>
              <label htmlFor="workspace-name">Name</label>
              <input id="workspace-name" {...form.register("name")} />
              <FieldError message={form.formState.errors.name?.message} />

              <label htmlFor="workspace-slug">URL identifier</label>
              <input id="workspace-slug" {...form.register("slug")} />
              <FieldError message={form.formState.errors.slug?.message} />

              <label htmlFor="workspace-description">Description</label>
              <textarea id="workspace-description" rows={4} {...form.register("description")} />
              <FieldError message={form.formState.errors.description?.message} />

              <button className="button button--primary button--full" type="submit" disabled={create.isPending}>
                {create.isPending ? "Creating…" : "Create workspace"}
              </button>
            </form>
          </aside>
        ) : null}
      </div>
    </div>
  );
}
