# CrowdSmarter master manual

*Facilitation. Systems. Collective intelligence.*

This is the single place to start if you want to understand how to actually use CrowdSmarter — as an organisation member running a decision, or as a platform administrator operating the service. It is written for a human reading start to end, not as an API reference. For implementation detail behind any section, see the linked doc in `docs/`.

---

## 1. What CrowdSmarter is

CrowdSmarter is a facilitation-led practice for groups making consequential
decisions. It helps people frame the question, involve the right participants,
work with evidence and disagreement, exercise accountable judgement, and learn
from what follows. The platform described in this manual supports that work by
keeping an attributable record from framing to outcome. It is one part of
CrowdSmarter, not the whole service.

AI is an optional advisory layer that can be dismissed. It never chooses an
option, finalises a decision, or acts as a silent participant.

Inside the supporting platform, records are organised within an
**organisation** (a tenant). Organisations contain **workspaces**, workspaces
contain **decisions**, and every decision carries its own participants,
evidence, and history. Discovery and facilitation may begin outside the
platform when that better serves the group.

---

## 2. Roles

### Organisation roles (`docs/permissions.md` has the full matrix)

| Role | Scope |
|---|---|
| Owner | Ultimate accountability for the organisation; can appoint/remove other owners and transfer ownership |
| Administrator | Day-to-day tenant and membership administration, short of owner-level control |
| Contributor | Creates and contributes to decisions but cannot administer the tenant |
| Viewer | Read-only visibility across the tenant and its decisions |

A suspended membership grants no access regardless of role.

### Decision-level participant roles

Separate from your organisation role, each decision has its own participant list:

| Role | Scope |
|---|---|
| Decision Owner | Accountable for the decision; exactly one active owner per decision |
| Decision Maker | Authorised to finalise the decision |
| Contributor | Adds evidence, assumptions, risks, options, positions |
| Reviewer | Reviews content without decision authority |
| Observer | Read-only visibility into that specific decision |

---

## 3. Getting started

1. You're added to an organisation by invitation (owners/admins send these from the organisation's Invitations screen). Accept it to create or link your account.
2. Once in, you land on **My work** — a role-differentiated home showing decisions where you're a participant, overdue actions, and pending contributions across every organisation you belong to.
3. Turn on MFA from **Account settings** if you handle sensitive decisions: `POST /mfa/enroll/begin/` returns a QR/provisioning URI for an authenticator app, you confirm with a one-time code, and the server gives you backup codes to store safely. Login then requires the code until you disable it (which itself re-confirms your password).

---

## 4. Running a decision: the lifecycle

Every decision moves through the same eleven stages, in order. A stage can't be skipped, and each transition is recorded with who did it and why.

```
Draft → Framing → Open for Contribution → Under Review → Ready for Decision
      → Decision Finalised → Commitment → Implementation → Outcome Review → Lessons Learned → Archived
```

**Draft** — the decision exists but isn't yet visible to participants; you're still writing the question, purpose and context.

**Framing** — participants are added, the decision question, scope, and criteria are set. This is where you populate:
- **Evidence** — attributable sources supporting or complicating the decision
- **Assumptions** — stated beliefs the reasoning depends on, so they can be challenged
- **Risks** — scored and tracked
- **Options** — the candidate choices being weighed
- **Criteria** — weighted dimensions options will be judged against

**Open for Contribution** — participants submit **positions**: a recommendation, an option preference, and reasoning. Disagreement is preserved, not smoothed over — the platform explicitly does not rewrite minority views as consensus.

**Under Review** — an AI-assisted review can be requested here (see §6). It surfaces missing evidence, unsupported assumptions, contradictory or duplicate evidence, missing stakeholders, risk highlights, and similar past decisions. It's advisory only.

**Ready for Decision** — everything required is in place; the decision awaits formal finalisation by a Decision Maker.

**Decision Finalised** — a human records the actual decision and rationale. This is the one non-reversible authority step in the lifecycle, and it's always attributed to a named person.

**Commitment → Implementation** — the organisation tracks what was committed to and how implementation is progressing.

**Outcome Review** — after enough time has passed, the outcome is assessed against expectations (exceeded / met / partially met / did not meet / inconclusive). This feeds the organisation's analytics.

**Lessons Learned → Archived** — durable lessons are captured and the decision is closed out.

Collective evaluation of options, when you use it, runs one of four methods: **scorecard** (multi-criteria weighted scoring, the default), **approval voting**, **consent** (surfacing objections rather than a score), or **Delphi** (anonymous rounds converging toward a shared view). Evaluation results include dispersion/dissent metrics and — for scorecard — a tornado chart of which criteria are driving the outcome, so you can see how contested a result actually was, not just the final number.

### Facilitation around the lifecycle

The lifecycle is a record of the decision, not a substitute for facilitation.
Start by discovering whether there is a real decision, a named authority, and
a genuine reason to involve other people. Frame the purpose, scope,
participation boundary, and use of contributions before scheduling a session.

In **Contribution orchestration**, a decision authority can create a session
brief with an objective, agenda, participation guidance, facilitator,
schedule, and invited participants. Session roles distinguish people who are
participating from people who are observing; they do not change decision
authority. The readiness prompt highlights missing foundations but never
approves a process automatically.

Record accessibility arrangements and the consent/attribution boundary before
convening. These fields should state the practical language, format, timing,
venue, assistive-technology, confidentiality, quotation, and withdrawal
conditions that actually apply; they are not a generic compliance assertion.

Build the live **run of show** from ordered activities. Each activity can name
its purpose, method, timebox, facilitator prompt, and the output that should be
captured. Open the session, start one queued activity, and use the elapsed-time
display while facilitating. Only one activity can be live. Complete or skip it
before moving on; a skipped item can be returned to the queue while the session
is still open. A session cannot close with a live activity.

Capture agreements, disagreements, actions, evidence gaps, questions, and
participant statements during the session. When an activity is live, a new
record links to it by default; the facilitator can select another activity or
leave the record unlinked. This keeps synthesis traceable to the part of the
process that produced it without altering attributable participant input.

After closure, complete the **Session quality review**. Score inclusion,
boundary clarity, facilitator neutrality, meaningful participation, and
follow-through from one to five, then record what worked, what to improve, and
any unresolved risks. The score is a visible facilitator reflection, not a
judgement of participants or an automated approval.

After a session, record each bounded agreement, unresolved disagreement,
action, evidence gap, or next question as a linked contribution request with a
named assignee and review boundary. Closed sessions remain available for this
follow-through. This keeps the platform useful between meetings without
turning every facilitation activity into software administration.

The working service definition and validation approach are in
`docs/facilitation-offer.md` and `docs/facilitation-validation-plan.md`.

---

## 5. AI assistance

Two AI-assisted features exist, both advisory and both dismissible by a human:

- **Decision review** — requested from a decision under review; a structured pass over the same evidence a human would read, looking for gaps.
- **Analytics insight** — a short narrative over your organisation's decision-flow metrics (see §7), generated on demand and kept as a permanent, attributable record you can look back on later.

Both run on whichever provider a platform administrator has configured — the built-in rule-based reviewer (no external service, no cost) or a real model (Anthropic Claude, OpenAI ChatGPT, or Google Gemini) once a provider is selected and an API key is set. See §10 for how to configure this.

---

## 6. Foresight

Foresight is a separate, upstream layer for thinking about the operating environment *before* it becomes a decision. Its building blocks:

- **Research claims** — neutral propositions from internet or internal
  research, with explicit evidence state, source relationships, limitations,
  reversal conditions, accountable owner, review date, and a transparent
  ten-point evidence score. The build/integrate/defer/avoid/monitor field is a
  human recommendation, not an automated product decision.
- **Canvas** — a workspace for one foresight exercise, with a horizon year
- **Signals** — observed developments, tagged by STEEP category (Social, Technological, Economic, Environmental, Political, Legal, Ethical) and polarity (opportunity / threat / both / unclear)
- **Drivers** — forces shaping the future: a trend, a general driver of change, a critical uncertainty, a predetermined element, or a wild card — each with a direction (increasing/decreasing/stable/volatile/unclear)
- **Causal relationships** and **feedback loops** between drivers — rendered as the causal network diagram
- **Three Horizons** items — mapping what's current (H1), transitional (H2), and emerging (H3)
- **Scenario sets** — built by crossing two critical-uncertainty drivers into a 2×2 matrix of scenarios, each of which can be wind-tunnel tested (robust / adaptable / vulnerable / infeasible / uncertain)
- **Signposts** — early-warning indicators you watch for a scenario materialising, each with a cadence (monthly through event-driven) and a direction to watch for; signposts can be linked to assumptions or risks in an actual decision, so a live signal can flag a decision that depends on it

Foresight work can be linked into a real decision, closing the loop from "what might happen" to "what we decided to do about it."

---

## 7. Analytics

Every organisation has an analytics page showing a small set of explainable, non-judgemental measures — not a leaderboard:

- **Flow**: decisions by status, a six-month created-vs-finalised trend chart, median days to finalise, overdue target dates, contribution coverage (share of open decisions with at least two active participants)
- **Learning**: outcome reviews completed, success rate, reviews due or overdue, active lessons

Any owner or administrator can generate an AI insight narrative over these metrics on demand (§5); every one generated is kept, attributed to who requested it and when, so you can see how the read on your organisation's health has changed over time.

---

## 8. Notifications and exports

**Notifications** surface attributable workflow events — reviews due, contributions requested, signposts triggering, and similar — across every organisation you belong to.

**Exports** produce a ZIP for an organisation or a single decision: per-dataset JSON and CSV files, one multi-sheet XLSX workbook, a README, and a manifest containing a SHA-256 content hash — so two exports can be compared to confirm they cover identical underlying records. Credentials and invitation tokens are never included.

---

## 9. Billing and plans

Plans are entitlement records, not a payment integration — CrowdSmarter doesn't currently process payments itself. Each plan defines: a trial length, a cap on active decisions, a cap on active members, whether advanced foresight is included, whether AI assistance is included, and a support level (community / standard / priority). An organisation's subscription is trialing, active, or expired, and entitlements are enforced at the point of use (e.g. creating a decision or inviting a member beyond the cap is blocked, not silently allowed).

---

## 10. Platform administration

Open `/platform-admin` — this requires an active platform-administrator capability, which is separate from any organisation membership (see `docs/admin-access.md`). Platform authority lets you operate the service without silently joining a customer organisation's decisions.

What you can do from here:

- **Grant / suspend platform administrators** — at least one must always remain active
- **Activate / deactivate any user account**
- **Support access** — open a reasoned, time-bounded grant to inspect a specific tenant's detail (visible, scoped, expiring, and audited — never silent); revoke it early if needed
- **Transfer organisation ownership** or **deactivate/reactivate an organisation**
- **Manage pending invitations** — revoke or resend
- **Platform settings** — the contact channels shown publicly (support, privacy, security, decision-enquiry emails) and the maximum allowed support-access duration
- **AI provider** — choose the active provider (rules / Anthropic / OpenAI / Gemini), set its model identifier, store its API key (encrypted at rest, never re-displayed), and use **Test connection** to make a small live call and confirm the key actually works before relying on it
- **Decision enquiries** — triage facilitation enquiries from the public site
- **Audit** — every one of the above actions is logged here, attributed and searchable, along with the rationale you gave for it

Every change here that could affect a customer requires a short, meaningful rationale (see the answer to "what does Change rationale mean" — it's what makes the audit log actually useful later, not just a record that *something* changed).

---

## 11. Where to go deeper

This manual is the map, not the territory. For implementation-level detail:

- `docs/decision-workflow.md` — the lifecycle contract in full
- `docs/permissions.md` — the complete permission matrix
- `docs/admin-access.md` — platform vs. product administration, granting the first admin
- `docs/domain-model.md` — the underlying data model
- `docs/ai-architecture.md` — how the provider abstraction and advisory-only constraint are implemented
- `docs/api.md` — the REST API surface
- `docs/security.md`, `docs/accessibility.md` — security and WCAG posture
- `docs/architecture.md` — system architecture
