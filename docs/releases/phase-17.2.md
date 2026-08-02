# Phase 17.2 — Public UI and Release Stabilisation

Phase 17.2 is a frontend-only stabilisation release. It does not add a database migration or change backend domain behaviour.

## Customer-visible changes

- Replaces abstract homepage skeleton blocks with five meaningful inline SVG workflow diagrams.
- Replaces the empty foresight trace placeholder with an explicit signal → system → scenario → decision chain.
- Corrects inherited white-on-white text inside the workflow panel.
- Keeps diagrams within their cards at desktop, tablet, and mobile widths.
- Preserves reduced-motion behaviour and semantic image descriptions.
- Retains the working Request Demo route and homepage calls to action.

## Release-safety changes

- Uses a frontend-only atomic installer.
- Never migrates, drops, restores, or otherwise modifies PostgreSQL.
- Stops the frontend before replacement and starts it only after type, test, and build checks pass.
- Restores the complete prior frontend and exits immediately after a failed check.
- Verifies the running container contains the Phase 17.2 source and the live public routes respond.
