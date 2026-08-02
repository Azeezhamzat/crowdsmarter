import { useState } from "react";
import { Link } from "react-router-dom";

import { Icon, type IconName } from "../../components/Icon";
import { buildMailto, contactChannels } from "../../config/contact";
import { ForesightDecisionTrace, WorkflowIllustration } from "./WorkflowIllustrations";

const workflow = [
  {
    key: "sense",
    label: "Sense",
    icon: "search" as IconName,
    title: "Detect consequential change before it becomes an urgent surprise.",
    description:
      "Capture attributable sources, weak signals, emerging issues, strategic horizons, and watchlists in one governed organisational record.",
    detail: "Foresight begins with disciplined attention—not confident prediction.",
  },
  {
    key: "interpret",
    label: "Interpret",
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

const audiences = ["Strategy", "Transformation", "Innovation", "Risk", "Policy", "Executive leadership"];

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
        <Link className="public-brand" to="/" aria-label="The CrowdSmarter home">
          <span className="public-brand__mark" aria-hidden="true"><span /><span /><span /></span>
          <span><strong>The CrowdSmarter</strong><small>Foresight-to-decision intelligence</small></span>
        </Link>
        <nav className="public-nav public-nav--executive" aria-label="Primary navigation">
          <a href="#platform">Platform</a>
          <a href="#workflow">How it works</a>
          <a href="#difference">Why CrowdSmarter</a>
          <a href="#trust">Trust</a>
        </nav>
        <div className="public-header__actions">
          <Link className="public-nav__signin" to="/login">Sign in</Link>
          <Link className="public-button public-button--primary public-header__demo" to="/request-demo">Request a demo</Link>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <section className="hero hero--executive" aria-labelledby="hero-title">
          <div className="hero__copy hero__copy--executive">
            <div className="public-proof-pill"><Icon name="shield" size={16} />Human judgement remains in control</div>
            <p className="public-eyebrow">Decision intelligence for consequential work</p>
            <h1 id="hero-title">Turn uncertainty into accountable action.</h1>
            <p className="hero__lead">
              CrowdSmarter connects strategic foresight, collective intelligence, governed decision-making,
              implementation, and organisational learning in one traceable operating system.
            </p>
            <div className="hero__actions hero__actions--executive">
              <Link className="public-button public-button--primary public-button--large" to="/request-demo">
                Request a tailored demo <Icon name="arrow-right" size={18} />
              </Link>
              <a className="public-button public-button--secondary public-button--large" href="#workflow">See the workflow</a>
            </div>
            <p className="hero__microcopy">Built for serious organisational decisions—not generic task management, chat, or automated judgement.</p>
            <div className="hero__trust-row hero__trust-row--executive">
              <span><Icon name="check" size={16} />Customer-owned records</span>
              <span><Icon name="check" size={16} />Visible uncertainty and dissent</span>
              <span><Icon name="check" size={16} />Provider-independent AI</span>
            </div>
          </div>

          <div className="executive-product-preview" aria-label="CrowdSmarter integrated decision analysis preview">
            <div className="executive-product-preview__glow" aria-hidden="true" />
            <div className="product-window product-window--executive">
              <div className="product-window__chrome">
                <span /><span /><span />
                <strong>Integrated decision analysis</strong>
                <small>Northstar Strategy</small>
              </div>
              <div className="product-window__body product-window__body--executive">
                <aside className="product-window__sidebar" aria-hidden="true"><i /><i /><i /><i /><i /><i /></aside>
                <div className="product-window__content product-window__content--executive">
                  <div className="preview-heading-row">
                    <div>
                      <span className="preview-label">Executive decision workspace</span>
                      <h2>How should we respond to accelerating AI adoption across our sector?</h2>
                    </div>
                    <span className="preview-status">Under review</span>
                  </div>
                  <div className="preview-readiness">
                    <div><span>Decision readiness</span><strong>Ready with conditions</strong></div>
                    <b>3 blockers</b>
                  </div>
                  <div className="preview-option-grid">
                    <article className="preview-option preview-option--lead">
                      <div><span>Option A</span><strong>Controlled pilot</strong></div>
                      <div className="preview-score"><span>Robustness</span><b>8.2</b></div>
                      <div className="preview-bars"><i /><i /><i /></div>
                    </article>
                    <article className="preview-option">
                      <div><span>Option B</span><strong>Enterprise rollout</strong></div>
                      <div className="preview-score"><span>Robustness</span><b>6.4</b></div>
                      <div className="preview-bars"><i /><i /><i /></div>
                    </article>
                  </div>
                  <div className="preview-insight-grid">
                    <article><span><Icon name="search" size={15} />Evidence</span><strong>16 linked</strong><small>3 material gaps</small></article>
                    <article><span><Icon name="layers" size={15} />Scenarios</span><strong>4 worlds</strong><small>2 vulnerabilities</small></article>
                    <article><span><Icon name="users" size={15} />Collective view</span><strong>72% support</strong><small>1 minority report</small></article>
                  </div>
                  <div className="preview-next preview-next--executive">
                    <span><Icon name="warning" size={16} /></span>
                    <div><small>Next accountable action</small><strong>Resolve procurement evidence gap before finalisation</strong></div>
                    <Icon name="arrow-right" size={17} />
                  </div>
                </div>
              </div>
            </div>
            <div className="preview-float-card preview-float-card--signal"><span>Emerging signal</span><strong>Regulatory expectations are tightening</strong><small>High relevance · Medium confidence</small></div>
            <div className="preview-float-card preview-float-card--audit"><Icon name="shield" size={16} /><span>Every judgement remains attributable</span></div>
          </div>
        </section>

        <section className="audience-strip" aria-label="Teams CrowdSmarter is designed for">
          <span>Designed for</span>
          <div>{audiences.map((audience) => <strong key={audience}>{audience}</strong>)}</div>
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
          <div className="continuity-grid">
            <article><span className="continuity-grid__number">01</span><Icon name="search" /><h3>Anticipate</h3><p>Sources, signals, drivers, systems maps, critical uncertainties, scenarios, and signposts.</p></article>
            <article><span className="continuity-grid__number">02</span><Icon name="users" /><h3>Deliberate</h3><p>Independent contributions, evidence, assumptions, risks, stakeholder positions, Delphi rounds, and dissent.</p></article>
            <article><span className="continuity-grid__number">03</span><Icon name="decision" /><h3>Decide</h3><p>Option comparison, decision-quality review, executive synthesis, explicit authority, and audit history.</p></article>
            <article><span className="continuity-grid__number">04</span><Icon name="activity" /><h3>Adapt and learn</h3><p>Implementation ownership, review conditions, outcomes, lessons, and reusable organisational memory.</p></article>
          </div>
        </section>

        <section className="public-section public-section--dark workflow-showcase workflow-showcase--executive" id="workflow" aria-labelledby="workflow-title">
          <div className="section-intro section-intro--workflow">
            <p className="public-eyebrow">The product is the workflow</p>
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

        <section className="public-section public-difference-section" id="difference" aria-labelledby="difference-title">
          <div className="section-intro section-intro--split section-intro--executive">
            <div><p className="public-eyebrow">A deliberately different product category</p><h2 id="difference-title">Not another place where important reasoning becomes invisible.</h2></div>
            <p>CrowdSmarter is the workflow and intelligence spine around specialist tools. It does not attempt to replace financial modelling, GIS, statistical software, document editing, or team chat.</p>
          </div>
          <div className="difference-layout">
            <div className="difference-statement">
              <span>Conventional workflow</span>
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

        <section className="public-section trust-section trust-section--executive" id="trust" aria-labelledby="trust-title">
          <div className="trust-panel trust-panel--executive">
            <div className="trust-panel__copy">
              <p className="public-eyebrow">Designed for organisational trust</p>
              <h2 id="trust-title">Your decision records should remain inspectable, portable, and under human authority.</h2>
              <p>CrowdSmarter is built as a maintainable modular monolith using open technologies, explicit permissions, tenant isolation, audit history, and customer-controlled exports.</p>
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
            <Link className="public-button public-button--light public-button--large" to="/request-demo">Request a tailored demo <Icon name="arrow-right" size={18} /></Link>
            <Link className="public-cta__signin" to="/login">Existing user? Sign in</Link>
          </div>
        </section>
      </main>

      <footer className="public-footer public-footer--executive">
        <div className="public-brand"><span className="public-brand__mark" aria-hidden="true"><span /><span /><span /></span><span><strong>The CrowdSmarter</strong><small>Foresight-driven organisational decision intelligence</small></span></div>
        <div className="public-footer__contact">
          <span>General enquiries and partnerships</span>
          <a href={buildMailto(contactChannels.general, "CrowdSmarter enquiry")}>{contactChannels.general}</a>
        </div>
        <div className="public-footer__links"><Link to="/request-demo">Request a demo</Link><Link to="/login">Sign in</Link><span>Human authority retained</span></div>
      </footer>
    </div>
  );
}
