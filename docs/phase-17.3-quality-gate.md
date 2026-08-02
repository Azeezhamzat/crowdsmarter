# Phase 17.3 quality gate

Phase 17.3 is complete only when:

- public navigation anchors leave section headings fully below the sticky header;
- workflow supporting copy renders at 17px or larger on desktop;
- capability supporting copy renders at 16px or larger on desktop;
- the foresight trace caption renders at 13px or larger on desktop;
- all five workflow illustrations remain visible without horizontal overflow;
- the workflow tabs support Arrow Left, Arrow Right, Home, and End;
- the semantic foresight-to-decision trace remains readable at desktop, tablet, and mobile widths;
- TypeScript checking succeeds;
- focused landing, demo-request, login, and AppShell tests succeed;
- the Vite production build succeeds;
- `/`, `/request-demo`, and `/login` respond after frontend recreation;
- installation failure restores a complete prior frontend when one is available;
- no database command or Docker-volume deletion is performed.
