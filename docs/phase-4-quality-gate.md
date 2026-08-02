# Phase 4 quality gate

## Customer value

- [x] Eligible stakeholders can state and revise their position without erasing history or rewriting the role held at submission.
- [x] Decision authorities can see exactly whose position is missing.
- [x] A decision cannot be finalised until every active decision owner and decision maker has submitted a current position.
- [x] A human authority selects the final option and records the rationale.
- [x] Dissent and alternative positions must be explicitly addressed.
- [x] Organisation managers can inspect attributable audit history.

## Security and governance

- [x] Tenant selectors resolve decision or organisation visibility before returning records.
- [x] Position submission requires an active tenant membership and eligible active participation.
- [x] Users submit only their own positions.
- [x] Position and finalisation records are immutable.
- [x] Finalisation separates human authority from lifecycle availability, uses optimistic status checking, and runs in a database transaction.
- [x] The selected option must be active and belong to the same decision.
- [x] Generic status transitions cannot bypass option selection and finalisation.
- [x] The audit API is restricted to active organisation owners and administrators.

## Maintainability

- [x] Positions are a separate Django domain app.
- [x] Models, selectors, policies, services, serializers, views, URLs, admin, migrations, and tests are separated.
- [x] Finalisation remains inside the decision aggregate and uses the shared transition recorder.
- [x] Server-derived capabilities control the interface while service checks remain authoritative.
- [x] No provider-specific or paid infrastructure dependency was introduced.
- [x] Architecture, domain, API, permissions, workflow, security, testing, release, and upgrade documentation are updated.

## Verification

- [x] Python source compiles and parses.
- [x] TypeScript and TSX parse successfully.
- [x] JSON, TOML, YAML, shell, and CSS sources pass static structural validation.
- [x] Migration source matches the model design under static review.
- [ ] Django/DRF tests must pass in Docker on the installation machine.
- [ ] PostgreSQL migration drift must report no changes in Docker.
- [ ] Frontend typecheck, component tests, build, and Playwright must pass in Docker.
