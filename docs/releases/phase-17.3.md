# Phase 17.3 — Public-Site Readability and Visual Hierarchy

Phase 17.3 is a frontend-only refinement release. It does not add migrations, alter backend behaviour, or modify customer data.

## Customer-visible changes

- Prevents the sticky public header from covering section headings reached through navigation links.
- Increases supporting-copy size and contrast across the workflow, difference, capability, trust, and call-to-action sections.
- Enlarges and clarifies all five workflow diagrams.
- Replaces the small SVG foresight trace with a responsive semantic signal → system → scenario → decision flow.
- Improves card spacing, line lengths, heading balance, borders, and shadows.
- Improves public-header brand, navigation, and action readability.
- Adds complete keyboard navigation for workflow tabs using Arrow Left, Arrow Right, Home, and End.

## Release safety

- Builds and validates an isolated candidate image before touching the live frontend.
- Runs TypeScript checking, focused regression tests, and the Vite production build before installation.
- Replaces only the frontend source and frontend container.
- Never dumps, migrates, drops, restores, or otherwise modifies PostgreSQL.
