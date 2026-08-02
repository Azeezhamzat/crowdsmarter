# ADR 0014: Versioned built-in decision templates

## Status

Accepted for Phase 8.

## Context

New users need help framing a decision, but a template system can easily become hidden automation, prescriptive methodology, or a complex marketplace before customer demand exists.

## Decision

CrowdSmarter ships a small catalogue of versioned templates defined in application code. A template contains only:

- a stable key and version;
- a name and use-case description;
- prompts for the question, purpose, context, scope, and contribution boundaries;
- a suggested urgency;
- a short checklist.

The user must write and review every persisted field. Template selection creates no evidence, assumptions, risks, options, positions, or lifecycle changes. The selected key is retained as provenance on the draft and in audit metadata.

## Rationale

- Works at zero recurring cost.
- Avoids a premature template-management subsystem.
- Keeps behaviour reviewable in source control.
- Makes prompt changes explicit through versioning.
- Preserves human ownership and avoids template-driven decisions.

## Consequences

- Organisations cannot yet create custom templates.
- Updating a built-in template requires a normal product release.
- Existing decisions retain the template key, not a frozen copy of all prompt text. Templates do not populate organisational facts, so this does not rewrite the decision record.

A future custom-template capability should be introduced only after real organisations demonstrate repeated, stable framing patterns.
