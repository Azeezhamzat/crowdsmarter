# Phase 18A — Accessibility Remediation Foundation

Phase 18A is a frontend-only accessibility release built on the visually approved Phase 17.3 baseline. It changes no backend domain, migration, customer record, or Docker volume.

## Customer-visible changes

- Adds a consistent skip-to-main-content link across public, authentication, invitation, demo, not-found, and authenticated routes.
- Gives each route a meaningful document title and announces route changes politely to assistive technologies.
- Moves keyboard focus to the new page heading after client-side navigation.
- Ensures public routes expose exactly one `main` landmark and removes nested `main` landmarks from evaluation and contribution workspaces.
- Adds a branded, recoverable not-found page instead of an unstructured router failure.
- Completes the workflow tabs pattern with roving focus, Arrow Left/Right, Home, End, `aria-orientation`, and a focusable tab panel.
- Reworks quick navigation as a labelled modal combobox/listbox pattern with focus containment, Escape support, close control, result announcements, and focus restoration.
- Adds explicit expanded/control relationships for mobile navigation and quick navigation.
- Announces field-level validation errors.
- Strengthens focus rings, minimum interactive target sizes, high-contrast behaviour, forced-colours support, and reduced-motion behaviour.

## Assurance boundary

This release is a substantial WCAG 2.2 AA remediation baseline, not an independent accessibility certification. Manual testing with representative keyboard, screen-reader, magnification, speech-input, and high-contrast users remains required before making a formal conformance claim.

## Release safety

- Builds and validates an isolated candidate image before touching the live frontend.
- Runs TypeScript checking, focused component tests, and the production Vite build before installation.
- Replaces only the complete frontend source and frontend container.
- Never dumps, migrates, drops, restores, or otherwise modifies PostgreSQL.
