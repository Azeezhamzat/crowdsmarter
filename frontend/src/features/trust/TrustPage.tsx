import { Link } from "react-router";

import { Icon, type IconName } from "../../components/Icon";
import { LogoMark } from "../../components/Logo";
import { buildMailto, contactChannels } from "../../config/contact";

const inPlace: Array<{ icon: IconName; title: string; description: string }> = [
  {
    icon: "shield",
    title: "CSRF-protected, session-authenticated everywhere",
    description: "Every state-changing request - including public applicant flows like session join, idea submission, voting, and the applicant portal's magic-link sign-in - requires a valid CSRF token, not just a session.",
  },
  {
    icon: "layers",
    title: "Tenant isolation at the query layer",
    description: "Every organisation-scoped lookup starts from an active-membership check before an object is returned. A client-supplied organisation ID is never trusted on its own.",
  },
  {
    icon: "check",
    title: "Reviewer conflicts stay visible",
    description: "A declared conflict of interest automatically excludes that reviewer's scores from results - and the exclusion itself is shown, not hidden.",
  },
  {
    icon: "building",
    title: "Encrypted provider credentials",
    description: "Any API key you connect (AI provider, Stripe, Candid) is encrypted at rest and decrypted only at the moment of use. Only the last 4 characters of a key ever appear in an audit entry.",
  },
  {
    icon: "decision",
    title: "An append-only audit trail",
    description: "Every configuration change, disbursement, eligibility decision, and funding outcome is recorded permanently - never edited or deleted after the fact.",
  },
  {
    icon: "external",
    title: "Two-factor authentication",
    description: "Every account can enrol a TOTP authenticator app with single-use backup codes, independent of any organisation's plan.",
  },
  {
    icon: "spark",
    title: "Immutable finalisation",
    description: "A funding decision, once finalised, is locked - including a snapshot of every stakeholder position at the moment of decision. This applies to grant rounds exactly as it does to every other decision type on the platform.",
  },
  {
    icon: "users",
    title: "Rate limiting on public endpoints",
    description: "Every public-facing action - joining a round, submitting an idea, voting, requesting a sign-in link - is throttled per action, independent of authentication.",
  },
];

const notYetTrue: Array<{ title: string; description: string }> = [
  {
    title: "No formal third-party certification",
    description: "No SOC 2, ISO 27001, or Cyber Essentials certification has been pursued or obtained. That requires an accredited external auditor examining our live production deployment and operational processes - it is not something code alone can produce, and we are not implying otherwise.",
  },
  {
    title: "No independent security audit yet",
    description: "This codebase has not yet been through an independent penetration test or third-party security review. That is a planned pre-launch step, not a completed one.",
  },
  {
    title: "Payment and lookup integrations are unverified against live credentials",
    description: "Stripe and Candid integrations are code-complete and unit-tested against documented API behaviour, but neither has been exercised against a real, live account. Every organisation defaults to a dependency-free manual mode - you are never required to trust an unverified integration to use the platform.",
  },
];

export function TrustPage() {
  return (
    <div className="public-site public-site--executive trust-page">
      <header className="demo-request-header">
        <Link className="public-brand" to="/" aria-label="CrowdSmarter home">
          <LogoMark size={38} />
          <span><strong>CrowdSmarter</strong><small>Facilitation. Systems. Collective intelligence.</small></span>
        </Link>
      </header>

      <main id="main-content" className="open-session-page trust-page__main" tabIndex={-1}>
        <section className="open-session-intro">
          <p className="public-eyebrow">Trust and security posture</p>
          <h1>What's actually true today - nothing more.</h1>
          <p className="open-session-prompt">
            This page exists to answer "how do you handle our data" directly. Every claim below maps to a
            specific, checkable control. Where something isn't true yet, we say so plainly instead of implying
            otherwise.
          </p>
        </section>

        <section className="trust-panel trust-panel--executive" aria-labelledby="trust-in-place-title">
          <div className="trust-panel__copy">
            <p className="public-eyebrow">In place today</p>
            <h2 id="trust-in-place-title">Controls you can verify.</h2>
            <p>Each of these maps to a specific module in the codebase - nothing here is aspirational.</p>
          </div>
          <div className="trust-list trust-list--executive">
            {inPlace.map((point) => (
              <article key={point.title}>
                <Icon name={point.icon} />
                <div><strong>{point.title}</strong><span>{point.description}</span></div>
              </article>
            ))}
          </div>
        </section>

        <section className="trust-honesty-section" aria-labelledby="trust-not-yet-title">
          <p className="public-eyebrow">Stated plainly, not hidden</p>
          <h2 id="trust-not-yet-title">Not yet true.</h2>
          <div className="trust-honesty-list">
            {notYetTrue.map((point) => (
              <article key={point.title}>
                <strong>{point.title}</strong>
                <p>{point.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="open-session-join" aria-label="Governance and security contact">
          <h2>Questions about your organisation's specific requirements?</h2>
          <p className="muted">We'll answer directly rather than route you through a sales process.</p>
          <div className="trust-contact-links">
            <a href={buildMailto(contactChannels.privacy, "CrowdSmarter privacy enquiry")}>Privacy enquiries</a>
            <a href={buildMailto(contactChannels.security, "CrowdSmarter security report")}>Security reports</a>
          </div>
          <Link className="button button--primary" to="/request-demo">Book a fit assessment</Link>
        </section>
      </main>
    </div>
  );
}
