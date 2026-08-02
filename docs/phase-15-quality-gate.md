# Phase 15 quality gate

Phase 15 is complete only when the following behaviour passes in the built release images.

## Domain and governance

- Analysis is option-centred and traceable to existing source records.
- The read model cannot mutate a decision or select an option.
- Cross-tenant and cross-decision links are rejected.
- Only active organisation members may own an issue.
- Contributors can create issues; only the assigned owner or accountable authority can update them.
- Only accountable authorities can transfer issue ownership.
- Resolved issues require a resolution, actor, and timestamp.
- Open issue ownership blocks unsafe member removal.
- Only accountable authorities can create, publish, or approve synthesis records.
- Draft reviews and summaries are not disclosed to non-authorities.
- Published reviews and approved summaries are immutable and versioned.
- Ready-with-conditions reviews require recorded conditions.
- Approved summaries require an explicit proposed judgement and human approval attribution.
- No aggregate is presented as an objective or automatic decision-quality score.

## API and security

- Every Phase 15 endpoint requires authentication.
- Tenant outsiders receive `404` rather than object-existence disclosure.
- Strict serializers reject unknown command fields.
- Server-derived capabilities govern all write paths.
- Archived and post-decision records are read-only through Phase 15 commands.
- Audit events are written for issue, review, and summary material changes.
- Search and exports remain tenant-scoped.

## Customer experience

- A user can compare all active options without navigating across separate record-type pages.
- Evidence balance, source credibility, assumptions, risk exposure, stakeholder support, scenario robustness, collective evaluation, and open issues are visible.
- Cross-cutting records and preserved minority reports remain visible.
- Gaps can be assigned, progressed, and resolved.
- Quality reviews and executive summaries preserve version history.
- The UI states clearly that synthesis does not replace human authority.
- Keyboard focus, semantic headings, labels, narrow-screen layouts, and reduced-motion behaviour remain usable.

## Regression and release checks

- Django system checks pass.
- Migration drift is absent.
- Phase 15 model and API tests pass.
- Export, search, organisation-offboarding, evaluation, scenario, and decision regressions pass.
- Full frontend type checking passes.
- Focused Phase 15 Vitest tests pass.
- The production Vite build passes.
- Backend liveness and frontend HTTP checks pass after migration.
- The upgrade script verifies the archive, backs up PostgreSQL, preserves Phase 14 source, and restores source plus database after any failed post-swap validation.
- Docker volumes are never deleted by the upgrader.
