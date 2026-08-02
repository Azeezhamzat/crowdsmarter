# ADR 0016 — Maintain a local professional design system

## Status

Accepted for Phase 9.

## Context

The Phase 8 application had broad workflow coverage but inconsistent visual hierarchy and limited interaction quality. Introducing a commercial component library would add cost, dependency risk, upgrade work, and styling constraints before the product interaction model is stable.

## Decision

CrowdSmarter will maintain a small local design system using:

- semantic React components;
- CSS custom properties for colour, spacing, radii, and shadows;
- local inline SVG icons;
- native HTML controls and disclosures;
- accessible focus and reduced-motion behaviour;
- responsive layouts without a runtime styling framework.

The system is intentionally component-light. It standardises shell navigation, buttons, cards, metrics, status treatments, modals, loading states, filters, empty states, and public-site presentation.

## Consequences

### Positive

- zero recurring cost;
- no design-system vendor lock-in;
- smaller production dependency surface;
- visual behaviour remains inspectable and replaceable;
- accessibility can be improved directly rather than negotiated through a framework.

### Trade-offs

- the team owns consistency and regression testing;
- complex components must be implemented deliberately;
- formal visual regression testing remains a future requirement.

## Guardrails

- animation must never obscure state or delay work;
- colour must not be the only carrier of meaning;
- custom controls must retain keyboard access;
- every new pattern should solve a recurring product problem;
- application screens should prioritise one primary user purpose.
