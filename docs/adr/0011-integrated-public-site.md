# ADR 0011: Serve the public site and product from one frontend

## Status

Accepted in Phase 5.

## Context

The CrowdSmarter needs a credible public presence as well as an authenticated decision workflow. A separate marketing repository, CMS, host, and domain would add recurring operational cost, duplicate deployment and security configuration, create visual drift, and complicate same-origin authentication without creating customer value at the current stage.

## Decision

The React application serves the public landing page at `/` and the authenticated application from `/app` and protected domain routes. The same Vite build and Nginx deployment serve both. Public content remains source-controlled and static until content frequency or non-technical publishing needs provide evidence for a CMS.

## Consequences

- One repository, build, domain, deployment, accessibility baseline, and design system.
- No additional hosting or CMS cost.
- Same-origin session and CSRF behaviour remains simple.
- Marketing changes currently require a normal product deployment.
- A future CDN, static host, or CMS can be introduced at the routing/configuration layer without changing Django domains.
