# Phase 15.1 quality gate

Phase 15.1 is complete only when the exact release images satisfy these checks.

## Public experience

- The homepage exposes a visible request-demo action and a sign-in path at desktop and narrow widths.
- The page explains the foresight-to-decision-to-learning proposition without unverified customer claims.
- Workflow tabs are keyboard reachable and preserve visible selected state.
- The product preview is decorative and does not misrepresent live customer data.

## Demo requests

- Valid submissions are stored and return `202` with a reference.
- Missing CSRF, missing consent, honeypot content, unexpected fields, malformed email, and overlong content are rejected.
- The endpoint is anonymous but rate limited.
- Optional email failure cannot roll back the stored request.
- Request records are visible only through authenticated Django administration.

## Sign-in and recovery

- Email matching is case insensitive and tolerates surrounding whitespace.
- Wrong password, missing account, and inactive account retain one generic API response.
- The browser converts that response into useful password-recovery guidance without account enumeration.
- A debug installation with no active account receives one generated local owner.
- An installation with an active account is never reset by the bootstrap command.
- Local password repair reads the secret from standard input and is blocked outside debug mode.

## Engineering

- `demo_requests.0001_initial` matches its model.
- Django checks and migration-drift checks pass.
- Focused backend and frontend tests pass.
- Full TypeScript checking and the production Vite build pass.
- The upgrade preserves source and PostgreSQL, and restores both after failed validation.
