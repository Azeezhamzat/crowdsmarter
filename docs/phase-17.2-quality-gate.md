# Phase 17.2 quality gate

Phase 17.2 is complete only when:

- the workflow title and body copy are visible on the white workflow panel;
- each of the five workflow tabs renders a distinct meaningful SVG diagram;
- the foresight capability card renders a labelled signal-to-decision trace;
- the page has no horizontal overflow at common desktop, tablet, and mobile widths;
- TypeScript checking succeeds;
- the landing, demo-request, login, and AppShell tests succeed;
- the Vite production build succeeds;
- `/`, `/request-demo`, and `/login` respond after frontend recreation;
- installation failure restores the previous frontend without touching PostgreSQL.
