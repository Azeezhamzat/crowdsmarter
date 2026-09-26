# Production email-delivery runbook

## What is implemented

CrowdSmarter supports authenticated SMTP with TLS or SSL, a bounded network timeout, a configured sender and reply-to mailbox, and startup checks that reject incomplete production settings. Local development keeps using Django's console backend and does not send messages externally.

## Configure

Set the provider-issued values in `.env.production`; do not commit that file:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-provider-smtp-host
EMAIL_PORT=587
EMAIL_HOST_USER=hello@crowdsmarter.com
EMAIL_HOST_PASSWORD=provider-secret
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_TIMEOUT=15
DEFAULT_FROM_EMAIL=CrowdSmarter <hello@crowdsmarter.com>
EMAIL_REPLY_TO=hello@crowdsmarter.com
```

Use TLS for the provider's submission port unless the provider specifically requires implicit SSL. Never enable both settings.

## Validate without sending

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production \
  run --rm backend python manage.py check_email_configuration
docker compose -f docker-compose.prod.yml --env-file .env.production \
  run --rm backend python manage.py check --deploy
```

## Provider acceptance test

This step sends real external email and must be run only by an authorised operator after credentials and DNS are configured:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production \
  run --rm backend python manage.py sendtestemail hello@crowdsmarter.com
```

Then test invitation, password-reset, and email-change messages end to end. Verify inbox placement, links, reply handling, expiry, duplicate suppression, and delivery failure logging.

## External prerequisites

The mailbox/provider owner must configure and verify SPF, DKIM, DMARC, bounce handling, abuse handling, and domain alignment. Provider dashboard evidence and receipt by at least two independent mail systems are required before production readiness can be claimed. These checks cannot be completed from the repository alone.

