import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link } from "react-router";
import { z } from "zod";

import { FieldError } from "../../components/FieldError";
import { Icon } from "../../components/Icon";
import { LogoMark } from "../../components/Logo";
import { StatusMessage } from "../../components/StatusMessage";
import { buildMailto, contactChannels } from "../../config/contact";
import { ApiError } from "../../lib/api";
import { submitDemoRequest } from "./api";

const demoRequestSchema = z.object({
  full_name: z.string().trim().min(2, "Enter your full name.").max(160),
  work_email: z.string().trim().email("Enter a valid work email address."),
  organisation_name: z.string().trim().min(2, "Enter your organisation name.").max(200),
  job_title: z.string().trim().max(160),
  organisation_size: z.enum(["1-10", "11-50", "51-200", "201-1000", "1000+", "not_sure"]),
  primary_need: z.enum([
    "strategic_foresight",
    "decision_governance",
    "collective_intelligence",
    "portfolio_prioritisation",
    "organisational_learning",
    "other",
  ]),
  message: z.string().trim().max(2000, "Keep the context below 2,000 characters."),
  consent_to_contact: z.boolean().refine((value) => value, { message: "Please confirm that we may contact you." }),
  website: z.string().max(0),
});

type DemoRequestForm = z.infer<typeof demoRequestSchema>;

const defaults: DemoRequestForm = {
  full_name: "",
  work_email: "",
  organisation_name: "",
  job_title: "",
  organisation_size: "not_sure",
  primary_need: "strategic_foresight",
  message: "",
  consent_to_contact: false,
  website: "",
};

export function RequestDemoPage() {
  const form = useForm<DemoRequestForm>({
    resolver: zodResolver(demoRequestSchema),
    defaultValues: defaults,
  });
  const request = useMutation({ mutationFn: submitDemoRequest });

  return (
    <main id="main-content" className="demo-request-page" tabIndex={-1}>
      <header className="demo-request-header">
        <Link className="public-brand" to="/" aria-label="CrowdSmarter home">
          <LogoMark size={38} />
          <span><strong>CrowdSmarter</strong><small>Foresight. Collective intelligence. Decisions.</small></span>
        </Link>
        <Link className="demo-request-header__signin" to="/login">Already have access? Sign in</Link>
      </header>

      <section className="demo-request-shell" aria-labelledby="demo-title">
        <div className="demo-request-intro">
          <div className="public-proof-pill"><Icon name="users" size={16} />A focused product conversation</div>
          <p className="public-eyebrow">Request a demonstration</p>
          <h1 id="demo-title">See how CrowdSmarter would support a real decision in your organisation.</h1>
          <p className="demo-request-intro__lead">
            We will centre the conversation on your decision environment—not on a generic feature tour.
            Share enough context for us to prepare a relevant walkthrough.
          </p>
          <div className="demo-expectations" aria-label="What to expect">
            <article><span>01</span><div><strong>A 30-minute discovery</strong><p>Your decision challenges, participants, evidence, uncertainty, and governance needs.</p></div></article>
            <article><span>02</span><div><strong>A tailored product walkthrough</strong><p>Signals, systems, scenarios, collective evaluation, analysis, and accountable follow-through.</p></div></article>
            <article><span>03</span><div><strong>An honest fit assessment</strong><p>Where CrowdSmarter helps now, what should remain in specialist tools, and what a pilot would require.</p></div></article>
          </div>
          <div className="demo-trust-note"><Icon name="shield" size={18} /><span>Your details are used only to respond to this request. No advertising list and no automatic account creation.</span></div>
          <div className="demo-direct-contact">
            <span>Prefer email?</span>
            <a href={buildMailto(contactChannels.demo, "CrowdSmarter demonstration enquiry", "Organisation:\nDecision challenge:\nPreferred next step:")}>{contactChannels.demo}</a>
          </div>
        </div>

        <section className="demo-request-card" aria-label="Demo request form">
          {request.isSuccess ? (
            <div className="demo-success" role="status">
              <span className="demo-success__icon"><Icon name="check" size={30} /></span>
              <p className="public-eyebrow">Request received</p>
              <h2>Thank you. We have the context needed to follow up.</h2>
              <p>{request.data.detail}</p>
              <p className="demo-success__contact">Follow-up will come from an official CrowdSmarter address. You can also reach us at <a href={buildMailto(contactChannels.demo, `Demo request ${request.data.reference}`)}>{contactChannels.demo}</a>.</p>
              <div className="demo-reference"><span>Reference</span><code>{request.data.reference}</code></div>
              <Link className="public-button public-button--primary" to="/">Return to the homepage</Link>
            </div>
          ) : (
            <>
              <div className="demo-form-heading">
                <p className="public-eyebrow">Tell us about your context</p>
                <h2>Request your tailored demonstration</h2>
                <p>Fields marked required help us prepare a useful conversation.</p>
              </div>
              {request.error ? (
                <StatusMessage kind="error">
                  {request.error instanceof ApiError ? request.error.message : "The request could not be submitted."}
                </StatusMessage>
              ) : null}
              <form
                className="demo-form"
                onSubmit={form.handleSubmit((values) => request.mutate({
                  ...values,
                  work_email: values.work_email.trim().toLowerCase(),
                }))}
                noValidate
              >
                <div className="demo-form-grid">
                  <div>
                    <label htmlFor="full_name">Full name *</label>
                    <input id="full_name" autoComplete="name" {...form.register("full_name")} />
                    <FieldError message={form.formState.errors.full_name?.message} />
                  </div>
                  <div>
                    <label htmlFor="work_email">Work email *</label>
                    <input id="work_email" type="email" autoComplete="email" placeholder="you@organisation.com" {...form.register("work_email")} />
                    <FieldError message={form.formState.errors.work_email?.message} />
                  </div>
                  <div>
                    <label htmlFor="organisation_name">Organisation *</label>
                    <input id="organisation_name" autoComplete="organization" {...form.register("organisation_name")} />
                    <FieldError message={form.formState.errors.organisation_name?.message} />
                  </div>
                  <div>
                    <label htmlFor="job_title">Role or job title</label>
                    <input id="job_title" autoComplete="organization-title" {...form.register("job_title")} />
                    <FieldError message={form.formState.errors.job_title?.message} />
                  </div>
                  <div>
                    <label htmlFor="organisation_size">Organisation size *</label>
                    <select id="organisation_size" {...form.register("organisation_size")}>
                      <option value="not_sure">Not sure</option>
                      <option value="1-10">1–10 people</option>
                      <option value="11-50">11–50 people</option>
                      <option value="51-200">51–200 people</option>
                      <option value="201-1000">201–1,000 people</option>
                      <option value="1000+">More than 1,000 people</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="primary_need">Primary area of interest *</label>
                    <select id="primary_need" {...form.register("primary_need")}>
                      <option value="strategic_foresight">Strategic foresight</option>
                      <option value="decision_governance">Decision governance</option>
                      <option value="collective_intelligence">Collective intelligence</option>
                      <option value="portfolio_prioritisation">Portfolio prioritisation</option>
                      <option value="organisational_learning">Organisational learning</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label htmlFor="message">What decision challenge should the demonstration address?</label>
                  <textarea id="message" rows={5} placeholder="For example: We need to compare strategic options under uncertainty while preserving evidence, dissent, and implementation conditions." {...form.register("message")} />
                  <div className="field-support"><span>Optional, but useful for tailoring the session.</span><span>{form.watch("message").length}/2000</span></div>
                  <FieldError message={form.formState.errors.message?.message} />
                </div>
                <div className="demo-honeypot" aria-hidden="true">
                  <label htmlFor="website">Website</label>
                  <input id="website" tabIndex={-1} autoComplete="off" {...form.register("website")} />
                </div>
                <label className="demo-consent" htmlFor="consent_to_contact">
                  <input id="consent_to_contact" type="checkbox" {...form.register("consent_to_contact")} />
                  <span>I consent to being contacted about this demonstration request. *</span>
                </label>
                <FieldError message={form.formState.errors.consent_to_contact?.message} />
                <button className="button button--primary button--large button--full" type="submit" disabled={request.isPending}>
                  {request.isPending ? "Sending request…" : <>Request demonstration <Icon name="arrow-right" size={18} /></>}
                </button>
                <p className="demo-form-footnote">Submitting this form does not create an account or subscribe you to marketing communications.</p>
              </form>
            </>
          )}
        </section>
      </section>
    </main>
  );
}
