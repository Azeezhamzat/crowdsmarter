# Phase 8 release notes

## Purpose

Phase 8 improves the product experience around the most important workflow boundary: creating and understanding a decision. It does not add autonomous decision making or a larger AI surface.

## Delivered

### Guided decision creation

- Five-step creation flow: template, framing, boundaries, authority/timing, and review.
- Seven built-in, versioned templates:
  - Blank decision
  - Technology adoption
  - Pilot or experiment
  - Strategic investment
  - Vendor selection
  - Research project approval
  - Policy or governance change
- Templates provide prompts and checklists only. They never create evidence, select options, assign stakeholder positions, or transition lifecycle state.
- All template-provided guidance remains editable before a draft is created.
- The source template key is retained on the decision and in the creation audit event.

### Coherent decision workspace

- A clear next-required-action panel.
- Lifecycle progress without treating progress as decision quality.
- At-a-glance framing, ownership, deadline, participant, discussion, option, evidence, assumption, and risk signals.
- Active-option comparison summary.
- Material-risk summary with transparent likelihood × impact scores.
- Contextual navigation to reasoning, discussion, positions, advisory review, and outcomes.
- Detailed framing, participant, transition, and history controls remain available through progressive disclosure.

### API and governance

- Authenticated decision-template catalogue endpoint.
- Tenant-isolated decision-overview endpoint.
- Strict validation rejects unknown template keys.
- Existing direct draft creation remains compatible and defaults to the blank template.
- Decision status still cannot be patched or inferred from template selection.

## Intentionally not included

Phase 8 does not yet include custom organisation templates, password recovery, evidence file attachments, customer-controlled exports, or production legal pages. Those remain subsequent product-trust slices and should not be implemented superficially in this release.
