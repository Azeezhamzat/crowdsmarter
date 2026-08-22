import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { LogoMark } from "../../components/Logo";
import { StatusMessage } from "../../components/StatusMessage";
import { ApiError } from "../../lib/api";
import type { MyApplication } from "../../lib/types";
import {
  clearApplicantToken,
  consumeMagicLink,
  getMyApplications,
  getStoredApplicantToken,
  requestMagicLink,
  submitProgressReport,
} from "./api";

const requestSchema = z.object({
  email: z.string().trim().email("Enter a valid email address."),
  name: z.string().trim().max(200),
});
type RequestForm = z.infer<typeof requestSchema>;

const reportSchema = z.object({
  body: z.string().trim().min(1, "Write an update first.").max(8000),
});
type ReportForm = z.infer<typeof reportSchema>;

function ProgressReportForm({ ideaId, onSubmit, isPending }: { ideaId: string; onSubmit: (body: string) => void; isPending: boolean }) {
  const form = useForm<ReportForm>({ resolver: zodResolver(reportSchema), defaultValues: { body: "" } });
  return (
    <form
      className="application-card__report-form"
      onSubmit={form.handleSubmit((values) => {
        onSubmit(values.body);
        form.reset();
      })}
      noValidate
    >
      <label htmlFor={`report-${ideaId}`}>Post a progress update</label>
      <textarea id={`report-${ideaId}`} rows={2} {...form.register("body")} />
      <FieldError message={form.formState.errors.body?.message} />
      <button className="button button--secondary button--compact" type="submit" disabled={isPending}>
        {isPending ? "Posting…" : "Post update"}
      </button>
    </form>
  );
}

function ApplicationCard({
  application,
  onSubmitReport,
  reportPending,
}: {
  application: MyApplication;
  onSubmitReport: (ideaId: string, body: string) => void;
  reportPending: boolean;
}) {
  return (
    <li className="application-card">
      <div className="application-card__header">
        <h3>{application.title}</h3>
        <span className="muted">
          {application.organisation_name} · {application.session_title}
        </span>
      </div>
      {application.requested_amount ? (
        <p className="muted">Requested: {application.requested_amount}</p>
      ) : null}
      {application.outcome ? (
        <div className="application-card__status">
          <span className={`status-badge status-badge--${application.outcome.eligibility_status}`}>
            {application.outcome.eligibility_status_label}
          </span>
          <span className={`status-badge status-badge--${application.outcome.outcome_status}`}>
            {application.outcome.outcome_status_label}
            {application.outcome.outcome_status === "funded" && application.outcome.awarded_amount
              ? ` · ${application.outcome.awarded_amount}`
              : ""}
          </span>
          {application.outcome.outcome_note ? <p className="muted">{application.outcome.outcome_note}</p> : null}
        </div>
      ) : (
        <span className="status-badge">{application.status_label}</span>
      )}

      {application.progress_reports.length > 0 ? (
        <ul className="application-card__reports">
          {application.progress_reports.map((report) => (
            <li key={report.id}>
              <small className="muted">{new Date(report.created_at).toLocaleDateString()}</small>
              <p>{report.body}</p>
            </li>
          ))}
        </ul>
      ) : null}

      {application.can_submit_progress_report ? (
        <ProgressReportForm
          ideaId={application.id}
          onSubmit={(body) => onSubmitReport(application.id, body)}
          isPending={reportPending}
        />
      ) : null}
    </li>
  );
}

export function MyApplicationsPage() {
  const queryClient = useQueryClient();
  const queryKey = ["my-applications"];
  const location = useLocation();
  const navigate = useNavigate();
  const [hasToken, setHasToken] = useState(() => Boolean(getStoredApplicantToken()));
  const [linkRequested, setLinkRequested] = useState(false);

  const consume = useMutation({
    mutationFn: (token: string) => consumeMagicLink(token),
    onSuccess: async () => {
      setHasToken(true);
      navigate(location.pathname, { replace: true });
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  useEffect(() => {
    const match = location.hash.match(/token=([^&]+)/);
    if (match?.[1]) {
      consume.mutate(decodeURIComponent(match[1]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.hash]);

  const applications = useQuery({
    queryKey,
    queryFn: getMyApplications,
    enabled: hasToken,
  });

  const requestForm = useForm<RequestForm>({ resolver: zodResolver(requestSchema), defaultValues: { email: "", name: "" } });
  const request = useMutation({
    mutationFn: (values: RequestForm) => requestMagicLink(values),
    onSuccess: () => setLinkRequested(true),
  });

  const report = useMutation({
    mutationFn: ({ ideaId, body }: { ideaId: string; body: string }) => submitProgressReport(ideaId, body),
    onSuccess: (data) => queryClient.setQueryData(queryKey, data),
  });

  const signOut = () => {
    clearApplicantToken();
    setHasToken(false);
    queryClient.removeQueries({ queryKey });
  };

  return (
    <main id="main-content" className="my-applications-page" tabIndex={-1}>
      <header className="demo-request-header">
        <Link className="public-brand" to="/" aria-label="CrowdSmarter home">
          <LogoMark size={38} />
          <span><strong>CrowdSmarter</strong><small>Foresight. Collective intelligence. Decisions.</small></span>
        </Link>
      </header>

      <section className="open-session-intro">
        <p className="public-eyebrow">Applicant portal</p>
        <h1>My applications</h1>
        <p className="muted">
          Every application you've submitted, across every round and every funder, in one place.
        </p>
      </section>

      {consume.isPending ? <p>Signing you in…</p> : null}
      {consume.isError ? (
        <StatusMessage kind="error">
          {consume.error instanceof ApiError ? consume.error.message : "That sign-in link is invalid or has expired."}
        </StatusMessage>
      ) : null}

      {!hasToken && !consume.isPending ? (
        <section className="open-session-join" aria-label="Sign in to view your applications">
          {linkRequested ? (
            <StatusMessage kind="info">
              If that email has any applications on record, a sign-in link is on its way. It expires in 30 minutes.
            </StatusMessage>
          ) : (
            <>
              <h2>Sign in with email</h2>
              <p className="muted">No password — we'll email you a one-time link.</p>
              {request.isError ? (
                <StatusMessage kind="error">
                  {request.error instanceof ApiError ? request.error.message : "Could not send that link."}
                </StatusMessage>
              ) : null}
              <form onSubmit={requestForm.handleSubmit((values) => request.mutate(values))} noValidate>
                <label htmlFor="applicant-email">Email</label>
                <input id="applicant-email" type="email" autoComplete="email" {...requestForm.register("email")} />
                <FieldError message={requestForm.formState.errors.email?.message} />
                <label htmlFor="applicant-name">Name (optional)</label>
                <input id="applicant-name" autoComplete="name" {...requestForm.register("name")} />
                <button className="button button--primary" type="submit" disabled={request.isPending}>
                  {request.isPending ? "Sending…" : "Email me a link"}
                </button>
              </form>
            </>
          )}
        </section>
      ) : null}

      {hasToken ? (
        <>
          <div className="my-applications-page__toolbar">
            <button className="button button--link button--compact" type="button" onClick={signOut}>
              Sign out
            </button>
          </div>
          {applications.isPending ? <p>Loading your applications…</p> : null}
          {applications.isError ? (
            <StatusMessage kind="error">
              {applications.error instanceof ApiError && applications.error.status === 403
                ? "Your session expired. Sign in again."
                : "Could not load your applications."}
            </StatusMessage>
          ) : null}
          {applications.data ? (
            <section aria-label="Your applications">
              {applications.data.applications.length === 0 ? (
                <p className="muted">No applications found for this email yet.</p>
              ) : (
                <ul className="application-list">
                  {applications.data.applications.map((application) => (
                    <ApplicationCard
                      key={application.id}
                      application={application}
                      onSubmitReport={(ideaId, body) => report.mutate({ ideaId, body })}
                      reportPending={report.isPending}
                    />
                  ))}
                </ul>
              )}
            </section>
          ) : null}
        </>
      ) : null}
    </main>
  );
}
