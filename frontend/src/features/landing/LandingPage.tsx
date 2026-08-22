import { Link } from "react-router";

import { Icon, type IconName } from "../../components/Icon";
import { LogoMark } from "../../components/Logo";
import { buildMailto, contactChannels } from "../../config/contact";
import { HeroVideo } from "./HeroVideo";

const lifecycleStages = [
  {
    label: "Anticipate",
    description: "Define the purpose of the round, eligibility, decision criteria and participation model before applications open.",
  },
  {
    label: "Deliberate",
    description: "Bring applicant evidence, community perspectives and reviewer judgement into a structured assessment process.",
  },
  {
    label: "Decide",
    description: "Compare assessments without concealing disagreement, then record the judgement and evidence behind the final decision.",
  },
  {
    label: "Act",
    description: "Issue awards, communicate meaningful feedback and establish the next points of accountability.",
  },
  {
    label: "Learn",
    description: "Carry evidence from the completed round into the design of the next one.",
  },
];

const implementationJourney = [
  {
    title: "Fit assessment",
    description: "A short working session to understand the round, governance context, participation model, and whether CrowdSmarter is an appropriate fit.",
  },
  {
    title: "Grant Round Sprint",
    description: "One real round, from open call to award, with the process configured and guided end to end.",
  },
  {
    title: "Adoption",
    description: "Retain the round structure, decision record, and reusable template so your team can run future rounds with less external support.",
  },
];

const charterStats: Array<[string, string]> = [
  ["Duration", "6 to 10 weeks"],
  ["Review team", "5 to 25 reviewers"],
  ["Format", "Hybrid or remote"],
  ["Outcome", "Funded round + reusable template"],
];

const outcomes = [
  {
    icon: "layers" as IconName,
    title: "Documented decision history",
    description: "Assessments, evidence, disagreement, and final rationale remain available as a coherent history of the round.",
  },
  {
    icon: "analytics" as IconName,
    title: "Defensible comparison",
    description: "Show how funded applications compared with the wider field, and what evidence informed the judgement.",
  },
  {
    icon: "check" as IconName,
    title: "Meaningful applicant feedback",
    description: "Applicants receive a reasoned explanation grounded in the assessment process, not a generic form rejection.",
  },
  {
    icon: "external" as IconName,
    title: "A reusable round template",
    description: "Eligibility, criteria, participation, and workflow carry into the next round without rebuilding from zero.",
  },
];

const foundations = [
  {
    icon: "layers" as IconName,
    title: "Systems thinking",
    description: "Treat each grant round as part of a learning system. Outcomes inform how eligibility, criteria, and participation are designed next time.",
  },
  {
    icon: "search" as IconName,
    title: "Futures thinking",
    description: "Design criteria around emerging needs and plausible change, rather than assuming past funding patterns are still the right guide.",
  },
  {
    icon: "users" as IconName,
    title: "Collective intelligence",
    description: "Structure community perspectives and reviewer judgement to inform a decision, without forcing disagreement into artificial consensus.",
  },
];

const trustPoints = [
  {
    icon: "shield" as IconName,
    title: "Human decision authority",
    description: "Final funding decisions remain with authorised people. CrowdSmarter structures evidence and deliberation; it does not replace accountable judgement.",
  },
  {
    icon: "layers" as IconName,
    title: "Traceable decision-making",
    description: "Assessments, evidence, disagreement, and final rationale stay connected, so the path to a decision can be inspected later.",
  },
  {
    icon: "check" as IconName,
    title: "Reviewer conflicts stay visible",
    description: "Reviewers declare conflicts before scoring; conflicted responses are excluded from results, transparently.",
  },
  {
    icon: "external" as IconName,
    title: "Organisational control",
    description: "Your organisation retains control of its round records and can export a documented history of the process at any time.",
  },
];

export function LandingPage() {
  return (
    <div className="public-site public-site--executive">
      <header className="public-header public-header--executive">
        <Link className="public-brand" to="/" aria-label="CrowdSmarter home">
          <LogoMark size={38} />
          <span><strong>CrowdSmarter</strong><small>Systems. Futures. Collective intelligence.</small></span>
        </Link>
        <nav className="public-nav public-nav--executive" aria-label="Primary navigation">
          <a href="#platform">Platform</a>
          <a href="#how-it-works">How it works</a>
          <a href="#why-us">Why us</a>
          <a href="#trust">Trust</a>
        </nav>
        <div className="public-header__actions">
          <Link className="public-nav__signin" to="/login">Sign in</Link>
          <Link className="public-button public-button--primary public-header__demo" to="/request-demo">Book a fit assessment</Link>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <HeroVideo
          eyebrow="Participatory grantmaking"
          title={<>Grantmaking your<br />community can<br /><span>actually see.</span></>}
          lead="One traceable record from open call to award — community input, reviewer scoring, and evidence behind every decision."
          primaryCta={{ label: "Book a fit assessment", href: "/request-demo" }}
          secondaryCta={{ label: "See how it works", href: "#how-it-works" }}
          trustItems={["Funder-owned records", "Reviewer disagreement stays visible", "Community voice, not just staff"]}
        />

        <section className="proof-strip" aria-label="Product foundation">
          <p className="public-eyebrow">Where this comes from</p>
          <p>
            The approach draws on participatory grantmaking and collective-intelligence research, with charter
            programmes structured around real, funded rounds before wider adoption.
          </p>
        </section>

        <section className="public-section public-section--platform" id="platform" aria-labelledby="platform-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">The process</p><h2 id="platform-title">A grant round as a connected decision system.</h2></div>
            <p>
              Each stage carries evidence forward. The aim is not simply to move applications through a workflow,
              but to keep participation, assessment, judgement, and learning connected from one round to the next.
            </p>
          </div>
          <div className="continuity-grid continuity-grid--five">
            {lifecycleStages.map((stage, index) => (
              <article key={stage.label}>
                <span className="continuity-grid__number">{String(index + 1).padStart(2, "0")}</span>
                <h3>{stage.label}</h3>
                <p>{stage.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="public-section public-section--dark" id="how-it-works" aria-labelledby="how-it-works-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">Implementation</p><h2 id="how-it-works-title">Learn the approach by running one real round.</h2></div>
            <p>
              The process is learned through delivery, not introduced as an abstract methodology. The first
              engagement creates a controlled route from fit assessment to an independently reusable process.
            </p>
          </div>
          <div className="commercial-journey">
            {implementationJourney.map((step, index) => (
              <article className="commercial-journey__step" key={step.title}>
                <span>{index + 1}</span>
                <div><h3>{step.title}</h3><p>{step.description}</p></div>
              </article>
            ))}
          </div>
          <div className="pilot-panel">
            <div className="pilot-panel__copy">
              <p className="public-eyebrow">Charter grant programme</p>
              <h3>Start with one real, funded round.</h3>
              <p>Charter programmes provide a bounded setting to run the method, refine the platform, and leave your organisation with a completed round and a reusable process.</p>
            </div>
            <div className="pilot-stats">
              {charterStats.map(([label, value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}
            </div>
            <Link className="public-button public-button--primary" to="/request-demo">Apply as a charter programme <Icon name="arrow-right" size={18} /></Link>
          </div>
        </section>

        <section className="public-section public-difference-section" aria-labelledby="difference-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">Connected reasoning</p><h2 id="difference-title">The distinction is continuity, not more software.</h2></div>
            <p>
              Forms, spreadsheets, and separate review tools can all be practical. The difficulty appears when
              evidence, discussion, decision rationale, and applicant feedback become separated across them.
            </p>
          </div>
          <div className="difference-layout">
            <div className="difference-statement">
              <span>When the process is fragmented</span>
              <p>Applications, assessments, discussion, and final decisions sit in separate tools. The path to a decision becomes difficult to inspect—and difficult to explain consistently to applicants, communities, or boards.</p>
            </div>
            <div className="difference-connector" aria-hidden="true"><Icon name="arrow-right" size={25} /></div>
            <div className="difference-statement difference-statement--positive">
              <span>When the reasoning stays connected</span>
              <p>CrowdSmarter keeps evidence, assessments, disagreement, the final decision, and its rationale connected, creating traceability without removing human judgement.</p>
            </div>
          </div>
        </section>

        <section className="public-section public-section--dark outcome-section" aria-labelledby="outcomes-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">Engagement outputs</p><h2 id="outcomes-title">A funded round—and capability that remains.</h2></div>
          </div>
          <div className="public-outcome-grid">
            {outcomes.map((outcome, index) => (
              <article className="public-outcome" key={outcome.title}>
                <span className="continuity-grid__number">{String(index + 1).padStart(2, "0")}</span>
                <Icon name={outcome.icon} />
                <h3>{outcome.title}</h3>
                <p>{outcome.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="public-section use-case-section" id="why-us" aria-labelledby="why-us-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">Methodological foundations</p><h2 id="why-us-title">Three disciplines shape how the round is designed.</h2></div>
            <p>CrowdSmarter is not grant-management software. It is informed by systems thinking, futures thinking, and collective intelligence—each changes how evidence, participation, and judgement are handled in practice.</p>
          </div>
          <div className="use-case-grid">
            {foundations.map((item) => (
              <article className="use-case" key={item.title}>
                <span className="capability-icon"><Icon name={item.icon} /></span>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="public-section trust-section trust-section--executive" id="trust" aria-labelledby="trust-title">
          <div className="trust-panel trust-panel--executive">
            <div className="trust-panel__copy">
              <p className="public-eyebrow">Governance and trust</p>
              <h2 id="trust-title">Designed to support scrutiny, not obscure it.</h2>
              <p>Institutional confidence depends on understanding who decided, what evidence was considered, and what remained under organisational control.</p>
              <Link className="public-text-link" to="/request-demo">Discuss your governance requirements <Icon name="arrow-right" size={16} /></Link>
              <div className="trust-contact-links" aria-label="Governance contact channels">
                <a href={buildMailto(contactChannels.privacy, "CrowdSmarter privacy enquiry")}>Privacy enquiries</a>
                <a href={buildMailto(contactChannels.security, "CrowdSmarter security report")}>Security reports</a>
              </div>
            </div>
            <div className="trust-list trust-list--executive">
              {trustPoints.map((point) => (
                <article key={point.title}><Icon name={point.icon} /><div><strong>{point.title}</strong><span>{point.description}</span></div></article>
              ))}
            </div>
          </div>
        </section>

        <section className="public-cta public-cta--executive" aria-labelledby="cta-title">
          <div>
            <p className="public-eyebrow">Bring a real round</p>
            <h2 id="cta-title">See whether CrowdSmarter fits your next round.</h2>
            <p>We'll shape the demo around a real round and give you a direct answer.</p>
          </div>
          <div className="public-cta__actions">
            <Link className="public-button public-button--light public-button--large" to="/request-demo">Book a fit assessment <Icon name="arrow-right" size={18} /></Link>
            <Link className="public-cta__signin" to="/login">Existing user? Sign in</Link>
          </div>
        </section>
      </main>

      <footer className="public-footer public-footer--executive">
        <div className="public-brand"><LogoMark size={38} /><span><strong>CrowdSmarter</strong><small>Systems. Futures. Collective intelligence.</small></span></div>
        <div className="public-footer__contact">
          <span>General enquiries and partnerships</span>
          <a href={buildMailto(contactChannels.general, "CrowdSmarter enquiry")}>{contactChannels.general}</a>
        </div>
        <div className="public-footer__links"><Link to="/request-demo">Book a fit assessment</Link><Link to="/login">Sign in</Link><span>Human authority retained</span><span>Working with organisations across Africa, Europe, and the Middle East</span></div>
      </footer>
    </div>
  );
}
