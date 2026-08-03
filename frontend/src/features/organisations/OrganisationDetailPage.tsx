import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { StatusMessage } from "../../components/StatusMessage";
import {
  createInvitation,
  listInvitations,
  resendInvitation,
  revokeInvitation,
} from "../invitations/api";
import { ApiError } from "../../lib/api";
import type { OrganisationRole } from "../../lib/types";
import {
  changeMembershipRole,
  getOrganisation,
  listMemberships,
  removeMembership,
} from "./api";

const invitationSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  role: z.enum(["owner", "admin", "contributor", "viewer"]),
});

type InvitationInput = z.infer<typeof invitationSchema>;

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function OrganisationDetailPage() {
  const { organisationId: routeOrganisationId } = useParams<{ organisationId: string }>();
  const organisationId = routeOrganisationId ?? "";
  const queryClient = useQueryClient();
  const [latestAcceptanceUrl, setLatestAcceptanceUrl] = useState<string | null>(null);
  const [latestDeliveryStatus, setLatestDeliveryStatus] = useState<"sent" | "failed" | null>(null);
  const form = useForm<InvitationInput>({
    resolver: zodResolver(invitationSchema),
    defaultValues: { email: "", role: "contributor" },
  });

  const organisation = useQuery({
    queryKey: ["organisations", organisationId],
    queryFn: () => getOrganisation(organisationId),
    enabled: Boolean(organisationId),
  });
  const memberships = useQuery({
    queryKey: ["organisations", organisationId, "memberships"],
    queryFn: () => listMemberships(organisationId),
    enabled: Boolean(organisationId),
  });

  const currentRole = organisation.data?.current_user_role;
  const canManage = ["owner", "admin"].includes(currentRole ?? "");
  const canManageInvitations = currentRole === "owner" || (
    currentRole === "admin" && organisation.data?.invitation_policy === "owners_and_admins"
  );
  useEffect(() => {
    if (organisation.data && !form.formState.isDirty) {
      form.setValue("role", organisation.data.default_invitation_role);
    }
  }, [form, organisation.data]);
  const invitations = useQuery({
    queryKey: ["organisations", organisationId, "invitations"],
    queryFn: () => listInvitations(organisationId),
    enabled: Boolean(organisationId) && canManageInvitations,
  });

  const refreshMemberships = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["organisations", organisationId, "memberships"],
    });
  };
  const refreshInvitations = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["organisations", organisationId, "invitations"],
    });
  };

  const invite = useMutation({
    mutationFn: (input: InvitationInput) => createInvitation(organisationId, input),
    onSuccess: async (dispatch) => {
      form.reset({ email: "", role: organisation.data?.default_invitation_role ?? "contributor" });
      setLatestAcceptanceUrl(dispatch.delivery.acceptance_url);
      setLatestDeliveryStatus(dispatch.delivery.status);
      await refreshInvitations();
    },
  });
  const resend = useMutation({
    mutationFn: resendInvitation,
    onSuccess: async (dispatch) => {
      setLatestAcceptanceUrl(dispatch.delivery.acceptance_url);
      setLatestDeliveryStatus(dispatch.delivery.status);
      await refreshInvitations();
    },
  });
  const revoke = useMutation({
    mutationFn: revokeInvitation,
    onSuccess: refreshInvitations,
  });
  const changeRole = useMutation({
    mutationFn: ({ membershipId, role }: { membershipId: string; role: OrganisationRole }) =>
      changeMembershipRole(membershipId, role),
    onSuccess: refreshMemberships,
  });
  const remove = useMutation({
    mutationFn: removeMembership,
    onSuccess: refreshMemberships,
  });

  const assignableRoles: OrganisationRole[] =
    currentRole === "owner"
      ? ["owner", "admin", "contributor", "viewer"]
      : ["admin", "contributor", "viewer"];

  const invitationError = invite.error || resend.error || revoke.error;

  return (
    <div>
      <Link className="back-link" to="/app">← Organisations</Link>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Organisation governance</p>
          <h1>{organisation.data?.name ?? "Organisation"}</h1>
          <p className="muted">Manage who may enter this tenant and what authority they hold.</p>
        </div>
        <div className="heading-actions organisation-heading-actions">
          {organisation.data ? <span className="role-badge">{organisation.data.current_user_role}</span> : null}
        </div>
      </div>

      {organisation.isError || memberships.isError ? (
        <StatusMessage kind="error">The organisation could not be loaded.</StatusMessage>
      ) : null}

      <nav className="organisation-action-nav" aria-label="Organisation sections">
        <Link to={`/organisations/${organisationId}/workspaces`}><span><Icon name="layers" /></span><div><strong>Workspaces</strong><small>Create and organise decisions</small></div><Icon name="arrow-right" size={17} /></Link>
        <Link to={`/organisations/${organisationId}/portfolio`}><span><Icon name="decision" /></span><div><strong>Portfolio</strong><small>See decision flow and priorities</small></div><Icon name="arrow-right" size={17} /></Link>
        <Link to={`/organisations/${organisationId}/prioritisation`}><span><Icon name="analytics" /></span><div><strong>Prioritisation</strong><small>Evaluate and select under constraints</small></div><Icon name="arrow-right" size={17} /></Link>
        <Link to={`/organisations/${organisationId}/foresight`}><span><Icon name="spark" /></span><div><strong>Foresight</strong><small>Signals, systems maps and future implications</small></div><Icon name="arrow-right" size={17} /></Link>
        <Link to={`/organisations/${organisationId}/search`}><span><Icon name="search" /></span><div><strong>Knowledge search</strong><small>Find evidence and lessons</small></div><Icon name="arrow-right" size={17} /></Link>
        <Link to={`/organisations/${organisationId}/analytics`}><span><Icon name="analytics" /></span><div><strong>Analytics</strong><small>Review decision-system health</small></div><Icon name="arrow-right" size={17} /></Link>
        {canManage ? <Link to={`/organisations/${organisationId}/methods`}><span><Icon name="layers" /></span><div><strong>Decision methods</strong><small>Govern templates, prompts and methodology versions</small></div><Icon name="arrow-right" size={17} /></Link> : null}
        {canManage ? <Link to={`/organisations/${organisationId}/administration`}><span><Icon name="shield" /></span><div><strong>Administration</strong><small>Branding, access policy, ownership and retention</small></div><Icon name="arrow-right" size={17} /></Link> : null}
        {canManage ? <Link to={`/organisations/${organisationId}/audit`}><span><Icon name="shield" /></span><div><strong>Audit log</strong><small>Inspect attributable actions</small></div><Icon name="arrow-right" size={17} /></Link> : null}
        {canManage ? <Link to={`/organisations/${organisationId}/export`}><span><Icon name="external" /></span><div><strong>Data export</strong><small>Download the complete tenant record</small></div><Icon name="arrow-right" size={17} /></Link> : null}
      </nav>

      <div className="page-grid">
        <section className="page-primary" aria-labelledby="members-title">
          <h2 id="members-title">Members</h2>
          {memberships.isPending ? <p>Loading members…</p> : null}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Person</th>
                  <th scope="col">Role</th>
                  {canManage ? <th scope="col"><span className="visually-hidden">Actions</span></th> : null}
                </tr>
              </thead>
              <tbody>
                {memberships.data?.map((membership) => (
                  <tr key={membership.id}>
                    <td>
                      <strong>{membership.user.first_name || membership.user.last_name ? `${membership.user.first_name} ${membership.user.last_name}`.trim() : membership.user.email}</strong>
                      {(membership.user.first_name || membership.user.last_name) ? <span className="table-secondary">{membership.user.email}</span> : null}
                    </td>
                    <td>
                      {canManage && (currentRole === "owner" || membership.role !== "owner") ? (
                        <select
                          aria-label={`Role for ${membership.user.email}`}
                          value={membership.role}
                          disabled={changeRole.isPending}
                          onChange={(event) => {
                            const role = event.target.value as OrganisationRole;
                            const changesOwnership = membership.role === "owner" || role === "owner";
                            if (!changesOwnership || window.confirm("Confirm this change to organisation ownership.")) {
                              changeRole.mutate({ membershipId: membership.id, role });
                            }
                          }}
                        >
                          {assignableRoles.map((role) => <option value={role} key={role}>{role}</option>)}
                        </select>
                      ) : (
                        <span className="role-badge">{membership.role}</span>
                      )}
                    </td>
                    {canManage ? (
                      <td className="table-action">
                        {currentRole === "owner" || membership.role !== "owner" ? (
                          <button
                            className="button button--danger-quiet"
                            type="button"
                            disabled={remove.isPending}
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Remove ${membership.user.email} from this organisation? ` +
                                    "Their non-owner decision assignments will be closed. " +
                                    "Unfinished decision ownership must be transferred first.",
                                )
                              ) {
                                remove.mutate(membership.id);
                              }
                            }}
                          >
                            Remove
                          </button>
                        ) : null}
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {changeRole.error || remove.error ? (
            <StatusMessage kind="error">
              {(changeRole.error instanceof ApiError && changeRole.error.message) ||
                (remove.error instanceof ApiError && remove.error.message) ||
                "The membership change failed."}
            </StatusMessage>
          ) : null}

          {canManageInvitations ? (
            <div className="section-block" aria-labelledby="invitations-title">
              <h2 id="invitations-title">Invitations</h2>
              <p className="muted">Pending invitations can be resent with a newly rotated link or revoked immediately.</p>
              {invitations.isPending ? <p>Loading invitations…</p> : null}
              {invitations.isError ? <StatusMessage kind="error">Invitations could not be loaded.</StatusMessage> : null}
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Email</th>
                      <th scope="col">Role</th>
                      <th scope="col">Status</th>
                      <th scope="col">Expires</th>
                      <th scope="col"><span className="visually-hidden">Actions</span></th>
                    </tr>
                  </thead>
                  <tbody>
                    {invitations.data?.map((item) => (
                      <tr key={item.id}>
                        <td>{item.email}</td>
                        <td>{item.role_label}</td>
                        <td><span className="role-badge">{item.status}</span></td>
                        <td>{formatDate(item.expires_at)}</td>
                        <td className="table-action">
                          {item.status === "pending" || item.status === "expired" ? (
                            <div className="inline-actions">
                              <button
                                className="button button--secondary"
                                type="button"
                                disabled={resend.isPending}
                                onClick={() => resend.mutate(item.id)}
                              >
                                Resend
                              </button>
                              <button
                                className="button button--danger-quiet"
                                type="button"
                                disabled={revoke.isPending}
                                onClick={() => {
                                  if (window.confirm(`Revoke the invitation for ${item.email}?`)) {
                                    revoke.mutate(item.id);
                                  }
                                }}
                              >
                                Revoke
                              </button>
                            </div>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </section>

        {canManageInvitations ? (
          <aside className="side-panel" aria-labelledby="invite-person-title">
            <h2 id="invite-person-title">Invite a person</h2>
            <p className="muted">They will create their own password through a secure, expiring link.</p>
            {invitationError ? (
              <StatusMessage kind="error">
                {invitationError instanceof ApiError ? invitationError.message : "The invitation action failed."}
              </StatusMessage>
            ) : null}
            {latestDeliveryStatus === "sent" ? (
              <StatusMessage kind="success">
                Invitation sent.
                {latestAcceptanceUrl ? (
                  <>
                    For local testing, copy this link and send it to the invited person:
                    <span className="copyable-link">{latestAcceptanceUrl}</span>
                  </>
                ) : null}
              </StatusMessage>
            ) : null}
            {latestDeliveryStatus === "failed" ? (
              <StatusMessage kind="error">
                The invitation was saved, but email delivery failed. Configure email and resend it.
                {latestAcceptanceUrl ? (
                  <>
                    The local development link is still available:
                    <span className="copyable-link">{latestAcceptanceUrl}</span>
                  </>
                ) : null}
              </StatusMessage>
            ) : null}
            <form onSubmit={form.handleSubmit((values) => invite.mutate(values))} noValidate>
              <label htmlFor="invitation-email">Email address</label>
              <input id="invitation-email" type="email" autoComplete="email" {...form.register("email")} />
              <FieldError message={form.formState.errors.email?.message} />

              <label htmlFor="invitation-role">Role</label>
              <select id="invitation-role" {...form.register("role")}>
                {assignableRoles.map((role) => <option value={role} key={role}>{role}</option>)}
              </select>

              <button className="button button--primary button--full" type="submit" disabled={invite.isPending}>
                {invite.isPending ? "Sending invitation…" : "Send invitation"}
              </button>
            </form>
          </aside>
        ) : null}
      </div>
    </div>
  );
}
