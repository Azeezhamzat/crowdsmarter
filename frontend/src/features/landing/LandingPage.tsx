import { useState } from "react";
import { Link } from "react-router";

import { Icon, type IconName } from "../../components/Icon";
import { LogoMark } from "../../components/Logo";
import { buildMailto, contactChannels } from "../../config/contact";
import { HeroVideo } from "./HeroVideo";
import { ForesightDecisionTrace, WorkflowIllustration } from "./WorkflowIllustrations";

const workflow = [
  {
    key: "sense",
    label: "Anticipate",
    icon: "search" as IconName,
    title: "Identify and examine consequential change before it is forced onto the agenda.",
    description:
      "Capture attributable sources, weak signals, emerging issues, strategic horizons, and watchlists in one governed organisational record.",
    detail: "Foresight begins with disciplined attention—not confident prediction.",
  },
  {
    key: "interpret",
    label: "Deliberate",
    icon: "layers" as IconName,
    title: "Connect signals, systems, stakeholders, and uncertainty.",
    description:
      "Map drivers and relationships, develop scenarios, test implications, and preserve competing interpretations rather than flattening them into artificial consensus.",
    detail: "The same signal can mean different things to different stakeholders.",
  },
  {
    key: "decide",
    label: "Decide",
    icon: "decision" as IconName,
    title: "Compare strategic options through an inspectable evidence chain.",
    description:
      "Bring evidence, assumptions, risks, stakeholder positions, collective evaluation, scenario robustness, and unresolved issues into one accountable decision picture.",
    detail: "AI may surface blind spots; people retain authority for every organisational choice.",
  },
  {
    key: "act",
    label: "Act",
    icon: "activity" as IconName,
    title: "Convert judgement into owned commitments and explicit conditions.",
    description:
      "Preserve the final rationale, implementation ownership, review conditions, risks, and signposts so decisions remain responsive as circumstances change.",
    detail: "Approval is not the end of a decision; it is the beginning of accountable execution.",
  },
  {
    key: "learn",
    label: "Learn",
    icon: "analytics" as IconName,
    title: "Turn outcomes into reusable organisational judgement.",
    description:
      "Compare expectations with results, record unintended consequences, preserve lessons, and make prior signals, assumptions, and decisions useful to future teams.",
    detail: "Institutional memory becomes strategic capability when anticipation, action, and outcome remain connected.",
  },
];

const useCases = [
  {
    key: "investment",
    icon: "analytics" as IconName,
    title: "Investment and transformation",
    description: "Prioritise initiatives, technologies, markets, or assets using transparent, weighted criteria.",
    examples: ["Capital allocation", "Digital transformation", "Market entry"],
  },
  {
    key: "policy",
    icon: "building" as IconName,
    title: "Policy and programmes",
    description: "Compare interventions and integrate perspectives across institutions or departments.",
    examples: ["Programme prioritisation", "Stakeholder consultation", "Option appraisal"],
  },
  {
    key: "resilience",
    icon: "shield" as IconName,
    title: "Resilience and scenarios",
    description: "Stress-test strategy against regulatory, climate, and economic disruption.",
    examples: ["Strategic stress-testing", "Continuity planning", "Signpost monitoring"],
  },
];

const sprintSteps = [
  {
    label: "Week 1",
    stage: "Anticipate",
    title: "Frame the decision",
    description: "Clarify the question, decision authority, objectives, constraints, stakeholders, and deadline.",
  },
  {
    label: "Weeks 1–2",
    stage: "Anticipate",
    title: "Gather knowledge",
    description: "Collect evidence, assumptions, risks, signals, and independent contributions.",
  },
  {
    label: "Weeks 2–4",
    stage: "Deliberate",
    title: "Explore uncertainty",
    description: "Build scenarios, test options, and identify the conditions for success.",
  },
  {
    label: "Weeks 4–6",
    stage: "Decide",
    title: "Evaluate without hiding disagreement",
    description: "Compare options, analyse robustness, and make useful dissent visible.",
  },
  {
    label: "Weeks 6–8",
    stage: "Decide → Act",
    title: "Decide and organise review",
    description: "Finalise the choice, responsibilities, signposts to monitor, and the review date.",
  },
];

const commercialJourney = [
  {
    title: "Fit assessment and demonstration",
    description: "A short conversation and live walkthrough to confirm CrowdSmarter fits your decision.",
  },
  {
    title: "Facilitated Decision Sprint",
    description: "Run one real, consequential decision through the platform with guided facilitation.",
  },
  {
    title: "Platform adoption and organisational scaling",
    description: "Continue using the platform independently for future decisions and organisational learning.",
  },
];

const pilotStats: Array<[string, string]> = [
  ["Duration", "4 to 8 weeks"],
  ["Team", "5 to 25 participants"],
  ["Format", "Hybrid or remote"],
  ["Outcome", "Decision + reusable platform"],
];

const outcomes = [
  {
    icon: "layers" as IconName,
    title: "A complete decision record",
    description: "Choice, rejected options, evidence, assumptions, dissent, and accountability in one auditable history.",
  },
  {
    icon: "analytics" as IconName,
    title: "A robustness analysis",
    description: "Tornado sensitivity, scenario-by-scenario comparison, and rank stability across assumptions.",
  },
  {
    icon: "search" as IconName,
    title: "A monitoring system",
    description: "Adaptive signposts, watchlists, and review dates linked to the decisions they inform.",
  },
  {
    icon: "external" as IconName,
    title: "A reusable method",
    description: "Approved decision templates and criteria your organisation can apply next time without starting from zero.",
  },
];

export function LandingPage() {
  const [activeWorkflow, setActiveWorkflow] = useState(workflow[0]!);
  const activeWorkflowIndex = workflow.findIndex((step) => step.key === activeWorkflow.key);

  const focusWorkflowTab = (index: number) => {
    const nextStep = workflow[index];
    if (!nextStep) return;
    setActiveWorkflow(nextStep);
    document.getElementById(`workflow-tab-${nextStep.key}`)?.focus();
  };

  return (
    <div className="public-site public-site--executive">
      <header className="public-header public-header--executive">
        <Link className="public-brand" to="/" aria-label="CrowdSmarter home">
          <LogoMark size={38} />
          <span><strong>CrowdSmarter</strong><small>Foresight. Collective intelligence. Decisions.</small></span>
        </Link>
        <nav className="public-nav public-nav--executive" aria-label="Primary navigation">
          <a href="#platform">Platform</a>
          <a href="#workflow">How it works</a>
          <a href="#sprint">Decision Sprint</a>
          <a href="#difference">Why CrowdSmarter</a>
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
          secondaryCta={{ label: "See how it works", href: "#workflow" }}
          trustItems={["Funder-owned records", "Reviewer disagreement stays visible", "Community voice, not just staff"]}
        />

        <section className="proof-strip" aria-label="Product foundation">
          <p className="public-eyebrow">Where this comes from</p>
          <p>
            Built from research in participatory grantmaking, collective intelligence, and accountable
            decision-making. CrowdSmarter is currently working with a first cohort of charter customer
            organisations on consequential strategy, policy, and transformation decisions.
          </p>
        </section>

        <section className="public-section use-case-section" id="use-cases" aria-labelledby="use-cases-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">Built for consequential choices</p><h2 id="use-cases-title">Designed for decisions where uncertainty and stakeholders both matter.</h2></div>
          </div>
          <div className="use-case-grid">
            {useCases.map((useCase) => (
              <article className="use-case" key={useCase.key}>
                <span className="capability-icon"><Icon name={useCase.icon} /></span>
                <h3>{useCase.title}</h3>
                <p>{useCase.description}</p>
                <ul>{useCase.examples.map((example) => <li key={example}>{example}</li>)}</ul>
              </article>
            ))}
          </div>
        </section>

        <section className="public-section public-section--platform" id="platform" aria-labelledby="platform-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">One continuous intelligence chain</p><h2 id="platform-title">The missing connection between foresight and accountable decisions.</h2></div>
            <p>
              Most organisations separate horizon scanning, workshops, evaluation, approvals, implementation,
              and learning across disconnected tools. CrowdSmarter preserves the relationships between them so
              the reasoning behind an important choice does not disappear after the meeting.
            </p>
          </div>
          <div className="continuity-grid continuity-grid--five">
            <article><span className="continuity-grid__number">01</span><Icon name="search" /><h3>Anticipate</h3><p>Sources, signals, drivers, systems maps, critical uncertainties, scenarios, and signposts.</p></article>
            <article><span className="continuity-grid__number">02</span><Icon name="users" /><h3>Deliberate</h3><p>Independent contributions, evidence, assumptions, risks, stakeholder positions, Delphi rounds, and dissent.</p></article>
            <article><span className="continuity-grid__number">03</span><Icon name="decision" /><h3>Decide</h3><p>Option comparison, decision-quality review, executive synthesis, explicit authority, and audit history.</p></article>
            <article><span className="continuity-grid__number">04</span><Icon name="activity" /><h3>Act</h3><p>Implementation ownership, review conditions, risks, and signposts as explicit commitments.</p></article>
            <article><span className="continuity-grid__number">05</span><Icon name="analytics" /><h3>Learn</h3><p>Outcomes, lessons, and reusable organisational memory for the next decision.</p></article>
          </div>
        </section>

        <section className="public-section public-section--dark workflow-showcase workflow-showcase--executive" id="workflow" aria-labelledby="workflow-title">
          <div className="section-intro section-intro--workflow">
            <p className="public-eyebrow">The platform connects the complete decision workflow</p>
            <h2 id="workflow-title">Move from emerging change to better judgement—without losing the evidence trail.</h2>
          </div>
          <div className="workflow-tabs workflow-tabs--executive" role="tablist" aria-label="CrowdSmarter workflow stages" aria-orientation="horizontal">
            {workflow.map((step, index) => (
              <button
                key={step.key}
                id={`workflow-tab-${step.key}`}
                type="button"
                role="tab"
                aria-controls="workflow-panel"
                aria-selected={activeWorkflow.key === step.key}
                tabIndex={activeWorkflow.key === step.key ? 0 : -1}
                className={activeWorkflow.key === step.key ? "is-active" : ""}
                onClick={() => setActiveWorkflow(step)}
                onKeyDown={(event) => {
                  if (event.key === "ArrowRight") {
                    event.preventDefault();
                    focusWorkflowTab((activeWorkflowIndex + 1) % workflow.length);
                  } else if (event.key === "ArrowLeft") {
                    event.preventDefault();
                    focusWorkflowTab((activeWorkflowIndex - 1 + workflow.length) % workflow.length);
                  } else if (event.key === "Home") {
                    event.preventDefault();
                    focusWorkflowTab(0);
                  } else if (event.key === "End") {
                    event.preventDefault();
                    focusWorkflowTab(workflow.length - 1);
                  }
                }}
              >
                <span>{String(index + 1).padStart(2, "0")}</span><Icon name={step.icon} size={18} />{step.label}
              </button>
            ))}
          </div>
          <div
            id="workflow-panel"
            className="workflow-feature workflow-feature--executive"
            role="tabpanel"
            aria-labelledby={`workflow-tab-${activeWorkflow.key}`}
            tabIndex={0}
          >
            <div>
              <p className="public-eyebrow">{activeWorkflow.label}</p>
              <h3>{activeWorkflow.title}</h3>
              <p>{activeWorkflow.description}</p>
              <blockquote>{activeWorkflow.detail}</blockquote>
            </div>
            <div className="workflow-diagram" data-stage={activeWorkflow.key}>
              <WorkflowIllustration stage={activeWorkflow.key} />
            </div>
          </div>
        </section>

        <section className="public-section sprint-section" id="sprint" aria-labelledby="sprint-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">Platform and service, as one journey</p><h2 id="sprint-title">Bring one real decision through a structured first engagement.</h2></div>
            <p>
              CrowdSmarter combines a governed decision-intelligence platform with a facilitated Decision Sprint.
              Start with one consequential decision, establish the workflow, and continue using the platform for
              future decisions and organisational learning.
            </p>
          </div>
          <div className="commercial-journey">
            {commercialJourney.map((stage, index) => (
              <article className="commercial-journey__step" key={stage.title}>
                <span>{index + 1}</span>
                <div><h3>{stage.title}</h3><p>{stage.description}</p></div>
              </article>
            ))}
          </div>
          <p className="sprint-timeline-intro">Inside the Decision Sprint, the same Anticipate → Deliberate → Decide → Act lifecycle plays out over four to eight weeks:</p>
          <div className="sprint-timeline">
            {sprintSteps.map((step, index) => (
              <article className="sprint-step" key={step.title}>
                <span className="sprint-step__number">{index + 1}</span>
                <div>
                  <p className="sprint-step__label">{step.label}<span className="sprint-step__stage">{step.stage}</span></p>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>
              </article>
            ))}
          </div>
          <div className="pilot-panel">
            <div className="pilot-panel__copy">
              <p className="public-eyebrow">Charter customer programme</p>
              <h3>Start with one real, important decision.</h3>
              <p>Charter customers run a first Decision Sprint and help shape the platform's development before wider release.</p>
            </div>
            <div className="pilot-stats">
              {pilotStats.map(([label, value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}
            </div>
            <Link className="public-button public-button--primary" to="/request-demo">Apply as a charter customer <Icon name="arrow-right" size={18} /></Link>
          </div>
        </section>

        <section className="public-section public-difference-section" id="difference" aria-labelledby="difference-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">A deliberately different product category</p><h2 id="difference-title">Keep important reasoning visible across the tools you already use.</h2></div>
            <p>CrowdSmarter connects the decision work around specialist tools such as financial models, GIS, statistical software, documents, and team collaboration platforms.</p>
          </div>
          <div className="difference-layout">
            <div className="difference-statement">
              <span>A commonly fragmented workflow</span>
              <p>Signals in one database. Workshop notes in slides. Evidence in folders. Voting in another app. Approval in email. Outcomes rarely revisited.</p>
            </div>
            <div className="difference-connector" aria-hidden="true"><Icon name="arrow-right" size={25} /></div>
            <div className="difference-statement difference-statement--positive">
              <span>CrowdSmarter workflow</span>
              <p>One attributable chain from external change, through collective interpretation and human judgement, to implementation, outcomes, and organisational learning.</p>
            </div>
          </div>
          <div className="product-capability-grid product-capability-grid--executive">
            <article className="product-capability product-capability--feature"><span className="capability-icon capability-icon--dark"><Icon name="layers" /></span><h3>Foresight that reaches the decision</h3><p>Signals, systems maps, scenarios, strategic implications, and signposts remain linked to the choices they inform.</p><div className="capability-trace"><ForesightDecisionTrace /></div></article>
            <article className="product-capability"><span className="capability-icon"><Icon name="decision" /></span><h3>Integrated analysis</h3><p>Compare options through evidence, assumptions, risk, stakeholder views, scenario robustness, and collective evaluation.</p></article>
            <article className="product-capability"><span className="capability-icon"><Icon name="users" /></span><h3>Governed collective intelligence</h3><p>Support blind rounds, consent, quorum, confidence, minority reports, and transparent prioritisation without forced consensus.</p></article>
            <article className="product-capability"><span className="capability-icon"><Icon name="spark" /></span><h3>Advisory, replaceable AI</h3><p>AI can identify gaps and patterns, but cannot silently edit records, select options, or exercise decision authority.</p></article>
            <article className="product-capability"><span className="capability-icon"><Icon name="analytics" /></span><h3>Learning after the decision</h3><p>Review outcomes against expectations and preserve lessons that improve future sensing, reasoning, and action.</p></article>
          </div>
        </section>

        <section className="public-section public-section--dark outcome-section" aria-labelledby="outcomes-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">What you walk away with</p><h2 id="outcomes-title">A concrete result, not just a workshop.</h2></div>
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

        <section className="public-section trust-section trust-section--executive" id="trust" aria-labelledby="trust-title">
          <div className="trust-panel trust-panel--executive">
            <div className="trust-panel__copy">
              <p className="public-eyebrow">Designed for organisational trust</p>
              <h2 id="trust-title">Your decision records should remain inspectable, portable, and under human authority.</h2>
              <p>Your organisation keeps authority over every decision, exports its own records at any time, and can inspect the full history behind each choice.</p>
              <Link className="public-text-link" to="/request-demo">Discuss your governance requirements <Icon name="arrow-right" size={16} /></Link>
              <div className="trust-contact-links" aria-label="Governance contact channels">
                <a href={buildMailto(contactChannels.privacy, "CrowdSmarter privacy enquiry")}>Privacy enquiries</a>
                <a href={buildMailto(contactChannels.security, "CrowdSmarter security report")}>Security reports</a>
              </div>
            </div>
            <div className="trust-list trust-list--executive">
              <article><Icon name="shield" /><div><strong>Human authority</strong><span>No automated final decisions or silent AI changes.</span></div></article>
              <article><Icon name="building" /><div><strong>Tenant isolation</strong><span>Organisation-scoped permissions and object-level controls.</span></div></article>
              <article><Icon name="layers" /><div><strong>Traceable reasoning</strong><span>Evidence, dissent, transitions, and summaries retain history.</span></div></article>
              <article><Icon name="external" /><div><strong>Customer ownership</strong><span>Exportable records and provider-independent architecture.</span></div></article>
              <article><Icon name="check" /><div><strong>Secure defaults</strong><span>Session authentication, CSRF protection, rate limits, and validated inputs.</span></div></article>
              <article><Icon name="activity" /><div><strong>Long-term maintainability</strong><span>Explicit services, tests, documentation, and safe upgrades.</span></div></article>
            </div>
          </div>
        </section>

        <section className="public-cta public-cta--executive" aria-labelledby="cta-title">
          <div>
            <p className="public-eyebrow">Bring a real decision</p>
            <h2 id="cta-title">See whether CrowdSmarter fits the way your organisation needs to anticipate, decide, and learn.</h2>
            <p>We will tailor the demonstration to your context and give you an honest assessment of product fit.</p>
          </div>
          <div className="public-cta__actions">
            <Link className="public-button public-button--light public-button--large" to="/request-demo">Book a fit assessment <Icon name="arrow-right" size={18} /></Link>
            <Link className="public-cta__signin" to="/login">Existing user? Sign in</Link>
          </div>
        </section>
      </main>

      <footer className="public-footer public-footer--executive">
        <div className="public-brand"><LogoMark size={38} /><span><strong>CrowdSmarter</strong><small>Foresight. Collective intelligence. Decisions.</small></span></div>
        <div className="public-footer__contact">
          <span>General enquiries and partnerships</span>
          <a href={buildMailto(contactChannels.general, "CrowdSmarter enquiry")}>{contactChannels.general}</a>
        </div>
        <div className="public-footer__links"><Link to="/request-demo">Book a fit assessment</Link><Link to="/login">Sign in</Link><span>Human authority retained</span><span>Working with organisations across Africa, Europe, and the Middle East</span></div>
      </footer>
    </div>
  );
}
