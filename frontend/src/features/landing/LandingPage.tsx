import { Link } from "react-router";

import { Icon, type IconName } from "../../components/Icon";
import { LanguageSwitcher } from "../../components/LanguageSwitcher";
import { LogoMark } from "../../components/Logo";
import { buildMailto, contactChannels } from "../../config/contact";
import { useLocale, useTranslations } from "../../lib/i18n";
import { landingCatalog } from "../../lib/catalogs/landing";
import { HeroVideo } from "./HeroVideo";

const heroTitleByLocale = {
  en: <>Decide together,<br />in a commons<br /><span>everyone can see.</span></>,
  fr: <>Décidez ensemble,<br />dans un commun<br /><span>que chacun peut voir.</span></>,
  pt: <>Decidam juntos,<br />num comum<br /><span>que todos podem ver.</span></>,
};

const lifecycleStages = [
  {
    label: "Anticipate",
    description: "Define the purpose, who is included, decision criteria and participation model before contribution opens.",
  },
  {
    label: "Deliberate",
    description: "Bring evidence, member perspectives and reviewer judgement into a structured assessment process.",
  },
  {
    label: "Decide",
    description: "Compare assessments without concealing disagreement, then record the judgement and evidence behind the final decision.",
  },
  {
    label: "Act",
    description: "Communicate the outcome, follow through on commitments and establish the next points of accountability.",
  },
  {
    label: "Learn",
    description: "Carry evidence from this decision into the design of the next one.",
  },
];

const freeStartJourney = [
  {
    title: "Sign up free",
    description: "Create your account and your commons in a couple of minutes. No card required.",
  },
  {
    title: "Bring your group",
    description: "Share one link. Anyone can join, contribute a signal or a submission, and vote, with no account needed on their side.",
  },
  {
    title: "Decide, together",
    description: "Move from open contribution to a recorded, accountable decision, then carry what you learned into the next one.",
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
    description: "Assessments, evidence, disagreement, and final rationale remain available as a coherent history of the decision.",
  },
  {
    icon: "analytics" as IconName,
    title: "Defensible comparison",
    description: "Show how the chosen response compared with the alternatives, and what evidence informed the judgement.",
  },
  {
    icon: "check" as IconName,
    title: "Meaningful feedback to contributors",
    description: "Contributors receive a reasoned explanation grounded in the assessment process, not a generic form rejection.",
  },
  {
    icon: "external" as IconName,
    title: "A reusable decision template",
    description: "Eligibility, criteria, participation, and workflow carry into the next decision without rebuilding from zero.",
  },
];

const foundations = [
  {
    icon: "layers" as IconName,
    title: "Systems thinking",
    description: "Treat each decision as part of a learning system. Outcomes inform how eligibility, criteria, and participation are designed next time.",
  },
  {
    icon: "search" as IconName,
    title: "Futures thinking",
    description: "Design criteria around emerging needs and plausible change, rather than assuming past patterns are still the right guide.",
  },
  {
    icon: "users" as IconName,
    title: "Collective intelligence",
    description: "Structure member perspectives and reviewer judgement to inform a decision, without forcing disagreement into artificial consensus.",
  },
];

const trustPoints = [
  {
    icon: "shield" as IconName,
    title: "Human decision authority",
    description: "Final decisions remain with authorised people. CrowdSmarter structures evidence and deliberation; it does not replace accountable judgement.",
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
    title: "Your control",
    description: "Your commons or organisation retains control of its decision records and can export a documented history of the process at any time.",
  },
];

export function LandingPage() {
  const locale = useLocale();
  const t = useTranslations(landingCatalog);
  return (
    <div className="public-site public-site--executive">
      <header className="public-header public-header--executive">
        <Link className="public-brand" to="/" aria-label="CrowdSmarter home">
          <LogoMark size={38} />
          <span><strong>CrowdSmarter</strong><small>Systems. Futures. Collective intelligence.</small></span>
        </Link>
        <nav className="public-nav public-nav--executive" aria-label="Primary navigation">
          <a href="#platform">{t.navPlatform}</a>
          <a href="#how-it-works">{t.navHowItWorks}</a>
          <a href="#why-us">{t.navWhyUs}</a>
          <a href="#trust">{t.navTrust}</a>
        </nav>
        <div className="public-header__actions">
          <LanguageSwitcher />
          <Link className="public-nav__signin" to="/login">{t.signIn}</Link>
          <Link className="public-button public-button--secondary" to="/request-demo">{t.bookAssessment}</Link>
          <Link className="public-button public-button--primary public-header__demo" to="/signup">{t.startFreeCta}</Link>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <HeroVideo
          eyebrow={t.heroEyebrow}
          title={heroTitleByLocale[locale]}
          lead={t.heroLead}
          primaryCta={{ label: t.startFreeCta, href: "/signup" }}
          secondaryCta={{ label: t.heroSecondaryCta, href: "#how-it-works" }}
          trustItems={[t.trustItem1, t.trustItem2, t.trustItem3]}
        />

        <section className="proof-strip" aria-label="Product foundation">
          <p className="public-eyebrow">{t.proofEyebrow}</p>
          <p>{t.proofBody}</p>
        </section>

        <section className="public-section public-section--platform" id="platform" aria-labelledby="platform-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">The process</p><h2 id="platform-title">Any group's decision, as a connected system.</h2></div>
            <p>
              Each stage carries evidence forward. The aim is not simply to move a decision through a workflow,
              but to keep participation, assessment, judgement, and learning connected from one decision to the next.
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
            <div><p className="public-eyebrow">Getting started</p><h2 id="how-it-works-title">Free to start, no institution required.</h2></div>
            <p>
              Most groups start on their own, with no sales conversation. The three steps below are the
              whole process.
            </p>
          </div>
          <div className="commercial-journey">
            {freeStartJourney.map((step, index) => (
              <article className="commercial-journey__step" key={step.title}>
                <span>{index + 1}</span>
                <div><h3>{step.title}</h3><p>{step.description}</p></div>
              </article>
            ))}
          </div>
          <div className="pilot-panel">
            <div className="pilot-panel__copy">
              <p className="public-eyebrow">For funders and institutions</p>
              <h3>Prefer a guided rollout? Run a charter grant round.</h3>
              <p>Charter programmes provide a bounded setting to run the method, refine the platform, and leave your organisation with a completed round and a reusable process. This is the path for an institution running a funded grant round, not a requirement for starting a commons.</p>
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
              evidence, discussion, decision rationale, and feedback become separated across them.
            </p>
          </div>
          <div className="difference-layout">
            <div className="difference-statement">
              <span>When the process is fragmented</span>
              <p>Contributions, assessments, discussion, and final decisions sit in separate tools. The path to a decision becomes difficult to inspect, and difficult to explain consistently to members, communities, or boards.</p>
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
            <div><p className="public-eyebrow">What stays with you</p><h2 id="outcomes-title">A decision, and capability that remains.</h2></div>
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
            <div><p className="public-eyebrow">Methodological foundations</p><h2 id="why-us-title">Three disciplines shape how the decision is designed.</h2></div>
            <p>CrowdSmarter is not grant-management software. It is informed by systems thinking, futures thinking, and collective intelligence, each of which changes how evidence, participation, and judgement are handled in practice.</p>
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
              <p>Confidence, whether from a neighbourhood commons or an institution, depends on understanding who decided, what evidence was considered, and what remained under your own control.</p>
              <Link className="public-text-link" to="/trust">Read our full trust and security posture <Icon name="arrow-right" size={16} /></Link>
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
            <p className="public-eyebrow">Two ways in</p>
            <h2 id="cta-title">Start free, or bring us a real round.</h2>
            <p>Start your own commons for free, or talk to us about a guided, funded grant round for your institution.</p>
          </div>
          <div className="public-cta__actions">
            <Link className="public-button public-button--light public-button--large" to="/signup">{t.startFreeCta} <Icon name="arrow-right" size={18} /></Link>
            <Link className="public-cta__signin" to="/request-demo">{t.bookAssessment}</Link>
          </div>
        </section>
      </main>

      <footer className="public-footer public-footer--executive">
        <div className="public-brand"><LogoMark size={38} /><span><strong>CrowdSmarter</strong><small>Systems. Futures. Collective intelligence.</small></span></div>
        <div className="public-footer__contact">
          <span>General enquiries and partnerships</span>
          <a href={buildMailto(contactChannels.general, "CrowdSmarter enquiry")}>{contactChannels.general}</a>
        </div>
        <nav className="public-footer__nav" aria-label="Footer navigation">
          <a href="#platform">{t.navPlatform}</a>
          <a href="#how-it-works">{t.navHowItWorks}</a>
          <a href="#why-us">{t.navWhyUs}</a>
          <a href="#trust">{t.navTrust}</a>
        </nav>
        <div className="public-footer__bottom">
          <span>© {new Date().getFullYear()} CrowdSmarter</span>
          <div className="public-footer__links"><Link to="/signup">{t.startFreeCta}</Link><Link to="/request-demo">{t.bookAssessment}</Link><Link to="/login">{t.signIn}</Link><Link to="/my-applications">{t.footerApplicant}</Link><Link to="/trust">{t.footerTrust}</Link><span>{t.footerHumanAuthority}</span></div>
        </div>
      </footer>
    </div>
  );
}
