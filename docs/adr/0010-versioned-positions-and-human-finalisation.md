# ADR 0010: Versioned positions and explicit human finalisation

- Status: Accepted
- Date: 2026-07-26

## Context

A governed decision needs to preserve what stakeholders believed, which option they supported, and how the authorised human reached the final choice. Mutable comments or a direct status patch would erase changes in judgement and allow a decision to appear final without a selected option, rationale, or treatment of dissent.

## Decision

1. Each stakeholder submission is an immutable `Position` version linked to one active decision participant and snapshots the participant role held at submission.
2. A revision appends the next version rather than updating the existing row.
3. Current positions are derived by selecting the latest version for each active participant.
4. Every active decision owner and designated decision maker must have a current position before finalisation.
5. Finalisation is a dedicated transactional command, not an ordinary lifecycle transition.
6. The command requires an active selected option, explicit rationale, confirmation that positions were reviewed, and a dissent summary when current positions do not support the selected option.
7. The immutable finalisation stores a snapshot of current positions and atomically transitions the decision to `Decision Finalised`.
8. AI adapters have no special pathway to submit positions, select an option, or invoke finalisation.

## Consequences

- Organisational reasoning remains attributable and reviewable over time.
- Disagreement is preserved rather than silently averaged or overwritten.
- Final decisions require more explicit user input, which is intentional governance friction.
- Position history increases row count, but PostgreSQL can support the expected pre-revenue and early-customer scale without another datastore.
- Corrections after finalisation require a future explicit amendment or reversal workflow; records are not edited in place.
