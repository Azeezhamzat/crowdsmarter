# Accessibility

CrowdSmarter aims to support WCAG 2.2 Level AA across the public experience and authenticated decision workflows.

## Implemented foundation

- Semantic page landmarks with one top-level `main` per route.
- A global skip link targeting `#main-content`.
- Route-specific document titles and polite route announcements.
- Programmatic focus movement after client-side route changes.
- Visible keyboard focus with increased-contrast and forced-colours adaptations.
- Minimum 44-pixel targets for primary interactive controls.
- Reduced-motion handling for transitions, animation, and smooth scrolling.
- Keyboard-complete public workflow tabs.
- Modal quick navigation with a named dialog, combobox/listbox semantics, focus containment, Escape handling, result status, and focus restoration.
- Status and validation messages exposed through live-region roles.
- A named not-found page with clear recovery paths.

## Testing

Automated coverage includes:

- one-main-landmark checks for public routes;
- skip-link focus behaviour;
- route title and live-announcement behaviour;
- workflow-tab keyboard behaviour;
- quick-navigation focus restoration;
- public form label checks;
- not-found recovery semantics;
- responsive homepage and illustration containment.

Automated checks cannot establish complete conformance. Before a public conformance statement, test at minimum with keyboard only, browser zoom and reflow, Windows High Contrast, VoiceOver/Safari, NVDA/Firefox or Chrome, and representative users carrying out real decision workflows.

## Reporting an accessibility problem

When reporting a problem, include the route, browser, assistive technology, expected behaviour, actual behaviour, and the smallest sequence of actions that reproduces it. Accessibility defects should receive a regression test at the lowest reliable layer.
