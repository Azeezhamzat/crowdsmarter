# Global competition programme

**Established:** 2 September 2026  
**Product position:** facilitation-led practice with a supporting platform  
**Delivery rule:** deepen complete decision journeys before adding unrelated modules

## Outcome

CrowdSmarter should compete on the quality and accountability of facilitated
decisions, not on the number of generic collaboration widgets. The target is a
coherent operating system that helps a facilitator frame a consequential
question, include relevant perspectives through appropriate channels, preserve
evidence and disagreement, support a legitimate decision, close the feedback
loop, and learn from implementation.

“Global standard” does not mean copying every feature offered by a broad
participation portal. It means that each journey CrowdSmarter chooses to offer
is dependable, guided, accessible, interoperable, auditable, and suitable for
professional delivery.

## Reference bar

This programme uses current official sources as capability and quality
references:

- the [OECD Guidelines for Citizen Participation Processes](https://www.oecd.org/en/publications/2022/09/oecd-guidelines-for-citizen-participation-processes_63b34541.html)
  for purpose, method choice, inclusion, feedback, accountability, and
  evaluation;
- [Decidim's documented participation model](https://docs.decidim.org/en/develop/features/general-description.html)
  and [accountability component](https://docs.decidim.org/en/develop/admin/components/accountability.html)
  for configurable processes, import/export, public responses, implementation
  states, milestones, and traceability;
- [WCAG 2.2](https://www.w3.org/TR/wcag/) as the accessibility baseline;
- [OWASP ASVS 5.0](https://owasp.org/www-project-application-security-verification-standard/)
  as the application-security verification catalogue;
- the dated competitor and operating-context comparison in
  `docs/research/crowdsmarter-desk-research-baseline-2026-09.md`.

Vendor documentation establishes that a capability exists; it does not prove
that the capability is effective. CrowdSmarter's own outcome claims remain
unknown until supported by observed use.

## Maturity scale

Every important capability is assessed against the same bar:

| Level | Meaning | Required evidence |
| --- | --- | --- |
| 0 — absent | No dependable workflow | None |
| 1 — recorded | Basic structured create/read/update workflow | Model, permissions, audit, API tests |
| 2 — usable | A professional can complete the task without reconstructing the record elsewhere | Guided UI, validation, search/filter, useful output, responsive behaviour |
| 3 — operational | A team can run the workflow repeatedly and govern exceptions | Ownership, review dates, notifications, import/export, history, metrics, runbook |
| 4 — competitive | The complete journey withstands enterprise and cross-context use | Accessibility evidence, security verification, scale/load evidence, integration boundary, recovery test, independent review where required |

A module is not called complete merely because it has database tables and a
form. Level 3 is the normal release target for core workflows. Level 4 requires
evidence that cannot always be generated locally.

## Workstreams

### 1. Facilitation delivery cockpit — in delivery

Build a low-friction live workspace around the hybrid session record already
present:

- agenda, run-of-show, method steps, timeboxes, room roles, and facilitator
  prompts;
- rapid keyboard-first capture of observations, questions, tensions,
  commitments, minority positions, and parking-lot items;
- visible influence boundary, constraints, missing perspectives, channel mix,
  accessibility arrangements, and consent boundary;
- structured synthesis that never overwrites attributable source records;
- print/offline pack before the session and authority-response pack after it;
- facilitator review checklist and session-quality evaluation.

The first operational slices landed on 3 September 2026: structured timeboxed
agenda items, one-live-item enforcement, live elapsed time, facilitator and
capture prompts, agenda-linked outputs, closure safeguards, printable
run-of-show evidence, portable exports, explicit accessibility and
consent/attribution arrangements, and a scored post-session quality review
with qualitative learning. Deeper room roles, keyboard capture, parking-lot
reconciliation, participant evaluation, and cross-session quality analytics
remain in the next slices.

Success means a facilitator can prepare, run, reconcile, and close a hybrid
engagement without rebuilding the record in documents and spreadsheets.

### 2. Research-to-decision intelligence — in delivery

The first Level 2/3 slice was added on 2 September 2026:

- neutral research claims with demonstrated/supported/plausible/unknown/
  contradicted states;
- explicit build/integrate/defer/avoid/monitor recommendations;
- authority, directness, recency, and triangulation scoring out of ten;
- supporting, contrary, and contextual source relationships;
- material limitations, assumptions, expected outcomes, and reversal
  conditions;
- accountable owner, review date, lifecycle, decision link, tenant isolation,
  audit history, and inclusion in organisation/decision exports;
- source access date, jurisdiction, archived URL, and freshness review fields.

Next increments are URL verification history, duplicate/citation detection,
claim change history, review notifications, saved research questions, and a
client-ready research brief generated from approved claims.

### 3. Inclusion and channel reach

- optimise every participant-critical path for small screens and intermittent
  connections;
- provide resumable drafts, compact payloads, and clear connection/retry state;
- import facilitator-captured paper, phone, radio, meeting, or partner-channel
  contributions with provenance and deduplication;
- add accessibility and participation-support needs to preparation without
  scoring or profiling people;
- deliver a complete translated journey only when content operations and
  support can maintain it; partial translation is not a launch state.

### 4. Decision quality and explainability

- progressive disclosure so teams see the next decision task rather than a
  catalogue of modules;
- relationship views linking claim → source → signal → option/assumption/risk →
  decision → commitment → outcome;
- quality gates that explain missing reasoning and allow governed exceptions;
- comparison views for options, trade-offs, dependencies, distributional
  effects, minority reports, and unresolved uncertainty;
- durable rationale and decision-change history.

### 5. Accountability and impact

- turn authority responses into scheduled, trackable public commitments;
- milestones, evidence of progress, blockers, owners, confidence, and dated
  updates;
- participant-facing feedback showing what was heard, what changed, what did
  not, why, and what happens next;
- process evaluation from the start, including inclusion, neutrality,
  deliberative quality, participant experience, and pathways to impact;
- distinguish output metrics from outcomes and never imply causality without
  suitable evidence.

### 6. Interoperability and client ownership

- stable documented API and versioned schemas;
- accessible print, JSON, CSV, and XLSX outputs for every professional register;
- import/export validation reports and reversible bulk operations;
- integration boundaries for identity, email, calendars, documents,
  conferencing, survey/GIS tools, and established participation platforms;
- webhooks and idempotent event delivery only after a replay/dead-letter design
  is tested.

### 7. Enterprise trust and reliability

- map the existing control set to OWASP ASVS 5.0 requirements and turn gaps
  into executable tests where possible;
- add performance budgets and load tests for participant submission, live
  facilitation capture, portfolio reads, search, and exports;
- retain fail-closed upload scanning, tenant-isolation tests, MFA, immutable
  audit, retention review, restore drills, observability, and readiness checks;
- production deployment still requires real email, alert receivers,
  infrastructure monitoring, secrets management, recovery objectives, legal
  policy approval, and an independent security/privacy review;
- never display an assurance or compliance claim that has not been earned.

### 8. Product coherence

- unify terminology, state models, empty/error/loading behaviour, filters,
  ownership, dates, and audit presentation across modules;
- add command/search navigation for experienced facilitators while keeping a
  guided path for occasional users;
- set page-weight, interaction-latency, and accessibility regression budgets;
- replace phase-number narratives with user outcomes and current evidence;
- remove or hide low-depth features that cannot support a coherent journey.

## Release gates

An upgraded workflow cannot be marked competitive until it has:

1. server-enforced tenant and role permissions;
2. service-layer validation and an audit event for every mutation;
3. tests for success, rejection, and cross-tenant access;
4. accessible, responsive, keyboard-usable interaction states;
5. explicit ownership, dates, lifecycle, and review behaviour;
6. search/filter and a client-owned export or integration boundary;
7. useful error, empty, loading, and recovery states;
8. current documentation that distinguishes tested facts from aspirations;
9. performance and security checks proportional to the risk;
10. no unsupported claim of effectiveness, adoption, compliance, or production
    assurance.

## Execution order

Delivery proceeds vertically rather than by adding more skeleton modules:

1. complete the research-claim workflow and use it to govern subsequent
   feature commitments;
2. build the live facilitation cockpit on the existing hybrid session model;
3. connect authority response to implementation milestones and feedback;
4. strengthen low-bandwidth/offline capture and reconciliation;
5. add decision relationship views and client-ready briefs;
6. execute the ASVS, accessibility, performance, resilience, and independent
   review work needed for Level 4.

This order can change only through a dated claim-ledger decision with the
evidence and reversal condition recorded.
