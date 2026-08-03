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

## Phase 20.1 audit (2026-08-03)

Ran `axe-core` (WCAG 2.2 A/AA rule sets) against every distinct route
template — public routes, and ~33 authenticated routes covering
organisations, workspaces, decisions (all sub-routes), foresight canvases,
platform administration, notifications, contributions, and account
settings — using real session state and real data rather than mocks.
Manually cross-checked heading order on a further sample of pages.

Found and fixed 9 real violations:

- **Colour contrast** (5 instances, one systemic pattern): several "muted
  small-print" text colours across the public site, the sidebar/footer
  brand mark, and the foresight horizon panel fell just short of the 4.5:1
  minimum for normal text (as low as 3.5:1). One was a genuine dark-on-dark
  bug: an executive-theme override redefined `.difference-statement`'s base
  text colour but didn't carry the override through for the `--positive`
  (dark green background) variant, leaving near-invisible text. Fixed each
  by darkening to a verified ≥4.5:1 ratio (computed against each element's
  actual rendered background via `getComputedStyle`, not assumed), and
  replaced one ad-hoc colour with the existing `--accent` design-system
  variable for consistency.
- **`scrollable-region-focusable`**: the horizontally-scrolling decision
  lifecycle stepper (`DecisionLifecycle.tsx`) had no way for a keyboard-only
  user to scroll it. Added `tabIndex={0}` and a descriptive `aria-label`.
- **`aria-required-children`** (critical): the contribution-workspace tab
  toggle used `role="tablist"` on the container but plain `<button>`
  children with no `role="tab"`. Implemented the full ARIA tabs pattern
  (`role="tab"`, `aria-selected`, `aria-controls`, roving `tabIndex`,
  arrow-key navigation, matching `role="tabpanel"` on each content panel) —
  the same pattern already used correctly on the public landing page.
- **`aria-prohibited-attr`**: a brand-colour swatch used `aria-label` on a
  plain `<span>`, which has no ARIA role capable of carrying an accessible
  name. Added `role="img"` so the label is valid.
- **`select-name`** (critical): the "clone a built-in method" dropdown had
  no accessible name at all — no wrapping `<label>`, no `aria-label`. Added
  one.

All fixes verified individually (re-scanned the affected route, zero
violations) and collectively (full frontend test suite 34/34, typecheck,
production build all clean). None of these were caught by the existing
Vitest/Playwright suites, which is expected — automated route-level axe
scanning with real authenticated data is a different, complementary check
from component-level rendering tests.

## Reporting an accessibility problem

When reporting a problem, include the route, browser, assistive technology, expected behaviour, actual behaviour, and the smallest sequence of actions that reproduces it. Accessibility defects should receive a regression test at the lowest reliable layer.
