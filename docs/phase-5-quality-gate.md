# Phase 5 quality gate

## Customer value

- A final decision can be followed through commitment, implementation, outcome assessment, learning, and archival.
- Implementation accountability cannot silently disappear during offboarding.
- Future teams can retrieve prior reasoning, outcomes, and lessons without an external search service.
- The public CrowdSmarter story and the product ship together as one coherent experience.

## Architecture

- `reviews`, `lessons`, and `search` are explicit Django domains.
- Views are thin, command serializers are strict, and workflows live in transactional services.
- Generic lifecycle transitions cannot bypass required post-decision records.
- PostgreSQL remains the only required data service.
- The landing page introduces no CMS, tracking service, or separate deployment.

## Security and governance

- All new reads are tenant-scoped.
- All material commands repeat server-side authority checks.
- Expected lifecycle state protects against stale submissions.
- Ownership transfer accepts only active organisation members and is audited.
- Search terms and records remain inside customer-controlled PostgreSQL.

## Testing

- Every Phase 5 API endpoint has automated coverage.
- Business rules, permissions, tenant isolation, stale commands, offboarding, and archival gates have focused tests.
- Frontend unit tests cover the landing page, outcomes workflow, and search.
- Playwright smoke coverage includes the public site.
