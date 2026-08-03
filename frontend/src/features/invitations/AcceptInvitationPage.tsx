import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { StatusMessage } from "../../components/StatusMessage";
import { logoutSession } from "../auth/api";
import { ApiError } from "../../lib/api";
import { acceptInvitation, getInvitation } from "./api";

const accountSchema = z
  .object({
    first_name: z.string().max(150),
    last_name: z.string().max(150),
    password: z.string().min(8, "Use at least eight characters."),
    password_confirm: z.string(),
  })
  .refine((values) => values.password === values.password_confirm, {
    message: "The passwords do not match.",
    path: ["password_confirm"],
  });

type AccountInput = z.infer<typeof accountSchema>;

export function AcceptInvitationPage() {
  const location = useLocation();
  const rawToken = new URLSearchParams(location.hash.slice(1)).get("token") ?? "";
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const form = useForm<AccountInput>({
    resolver: zodResolver(accountSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      password: "",
      password_confirm: "",
    },
  });

  const invitation = useQuery({
    queryKey: ["invitation", rawToken],
    queryFn: () => getInvitation(rawToken),
    enabled: Boolean(rawToken),
    retry: false,
  });

  const accept = useMutation({
    mutationFn: (input: Partial<AccountInput>) => acceptInvitation(rawToken, input),
    onSuccess: async (result) => {
      queryClient.setQueryData(["current-user"], result.user);
      await navigate(`/organisations/${result.membership.organisation_id}`, {
        replace: true,
      });
    },
  });

  const signOut = useMutation({
    mutationFn: logoutSession,
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: ["current-user"] });
      await invitation.refetch();
    },
  });

  if (!rawToken) {
    return (
      <main id="main-content" className="auth-layout" tabIndex={-1}>
        <section className="auth-card">
          <StatusMessage kind="error">The invitation link is incomplete.</StatusMessage>
        </section>
      </main>
    );
  }

  if (invitation.isPending) {
    return <main id="main-content" className="centred-state" tabIndex={-1} aria-busy="true">Checking your invitation…</main>;
  }

  if (invitation.isError || !invitation.data) {
    return (
      <main id="main-content" className="auth-layout" tabIndex={-1}>
        <section className="auth-card">
          <h1>Invitation unavailable</h1>
          <StatusMessage kind="error">
            {invitation.error instanceof ApiError
              ? invitation.error.message
              : "This invitation could not be verified."}
          </StatusMessage>
        </section>
      </main>
    );
  }

  const details = invitation.data;
  const canAcceptAsCurrentUser =
    details.current_user_email?.toLowerCase() === details.email.toLowerCase();
  const signedInAsDifferentUser =
    details.current_user_email !== null && !canAcceptAsCurrentUser;
  const loginNext = `/accept-invitation#token=${encodeURIComponent(rawToken)}`;

  return (
    <main id="main-content" className="auth-layout" tabIndex={-1}>
      <section className="auth-introduction" aria-labelledby="invitation-heading">
        <p className="eyebrow">Organisation invitation</p>
        <h1 id="invitation-heading">Join {details.organisation_name}</h1>
        <p>
          You have been invited as <strong>{details.role_label}</strong>. Membership is
          created only after you accept.
        </p>
      </section>
      <section className="auth-card" aria-labelledby="accept-title">
        <h2 id="accept-title">Accept invitation</h2>
        <p className="muted">Invited email: {details.email}</p>

        {details.status !== "pending" ? (
          <StatusMessage kind="error">
            This invitation is {details.status}. Ask an organisation manager for a new link.
          </StatusMessage>
        ) : null}

        {accept.error ? (
          <StatusMessage kind="error">
            {accept.error instanceof ApiError
              ? accept.error.message
              : "The invitation could not be accepted."}
          </StatusMessage>
        ) : null}

        {details.status === "pending" && signedInAsDifferentUser ? (
          <div>
            <StatusMessage kind="error">
              You are signed in as {details.current_user_email}. Sign out before accepting an
              invitation sent to {details.email}.
            </StatusMessage>
            <button
              className="button button--secondary button--full"
              type="button"
              disabled={signOut.isPending}
              onClick={() => signOut.mutate()}
            >
              {signOut.isPending ? "Signing out…" : "Sign out"}
            </button>
          </div>
        ) : null}

        {details.status === "pending" && details.account_exists && !details.current_user_email ? (
          <div>
            <p>An account already exists for this email. Sign in, then return here to accept.</p>
            <Link
              className="button button--primary button--full button-link"
              to={`/login?next=${encodeURIComponent(loginNext)}`}
            >
              Sign in to accept
            </Link>
          </div>
        ) : null}

        {details.status === "pending" && canAcceptAsCurrentUser ? (
          <button
            className="button button--primary button--full"
            type="button"
            disabled={accept.isPending}
            onClick={() => accept.mutate({})}
          >
            {accept.isPending ? "Accepting…" : `Accept and join ${details.organisation_name}`}
          </button>
        ) : null}

        {details.status === "pending" && !details.account_exists && !details.current_user_email ? (
          <form
            onSubmit={form.handleSubmit((values) => accept.mutate(values))}
            noValidate
          >
            <label htmlFor="first-name">First name</label>
            <input id="first-name" autoComplete="given-name" {...form.register("first_name")} />
            <FieldError message={form.formState.errors.first_name?.message} />

            <label htmlFor="last-name">Last name</label>
            <input id="last-name" autoComplete="family-name" {...form.register("last_name")} />
            <FieldError message={form.formState.errors.last_name?.message} />

            <label htmlFor="new-password">Create password</label>
            <input
              id="new-password"
              type="password"
              autoComplete="new-password"
              {...form.register("password")}
            />
            <FieldError message={form.formState.errors.password?.message} />

            <label htmlFor="confirm-password">Confirm password</label>
            <input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              {...form.register("password_confirm")}
            />
            <FieldError message={form.formState.errors.password_confirm?.message} />

            <button
              className="button button--primary button--full"
              type="submit"
              disabled={accept.isPending}
            >
              {accept.isPending ? "Creating account…" : "Create account and accept"}
            </button>
          </form>
        ) : null}
      </section>
    </main>
  );
}
