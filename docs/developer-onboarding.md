# Developer onboarding

## Prerequisites

- Docker with Compose;
- Git;
- optional local Python 3.12+ and Node 20.19+ for non-container workflows.

## First run

```bash
git clone <repository>
cd crowdsmarter
cp .env.example .env
docker compose up --build
```

In another terminal:

```bash
docker compose run --rm backend python manage.py createsuperuser
```

Create an organisation, then use **Invite a person** in the React client. In local development, copy the displayed acceptance link into a private browser window so the invited person can choose their own password. Creating an organisation also creates its default `Decisions` workspace. From there, create a draft, complete its framing, assign stakeholders, and advance it through the enabled lifecycle states.

## Working agreement

1. Select one customer workflow and its measurable outcome.
2. Write or update the domain rationale and permissions.
3. Implement models and services before HTTP/UI orchestration.
4. Add denied permission cases as well as successful cases.
5. Keep tenant ownership explicit and reject unexpected command fields.
6. Record important design choices in an ADR.
7. Run tests, migration checks, lint, type checks, and production builds.
8. Refactor before opening the next vertical slice.

## Adding a Django domain

A domain app should contain only the modules it needs. Typical modules are `models`, `services`, `selectors`, `permissions`, `serializers`, `views`, `urls`, `admin`, `tests`, and migrations. Do not create empty layers to satisfy a pattern.

## Secrets

Never commit `.env`, credentials, customer exports, or production database copies. Development defaults are deliberately unsafe for production, and production settings fail fast.

## Phase 6 development paths

Run a local advisory review from the authenticated decision workspace. The default provider is deterministic, so no AI account or API key is needed. Provider implementations live under `apps.ai_assistance.providers` and must satisfy the protocol in `providers/base.py`.

Create due-review notifications manually with:

```bash
python manage.py send_due_review_notifications
```

Do not add provider SDK calls to views, serializers, React components, or decision services. Keep provider translation inside an adapter and persist output only through `apps.ai_assistance.services`.

## Local first-run and sign-in recovery

After migrations, create a starter owner only when the database has no active account:

```bash
docker compose run --rm backend python manage.py ensure_local_owner
```

The command prints a generated password when it creates the account. It does nothing when an active account already exists. To reset a local password without writing it to shell history:

```bash
bash scripts/reset-local-password.sh
```

Both workflows require `DJANGO_DEBUG=true` and must not be used as production identity administration.
