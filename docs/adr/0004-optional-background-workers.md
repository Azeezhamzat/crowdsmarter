# ADR 0004: Keep background workers optional for core workflows

- Status: Accepted
- Date: 2026-07-25

## Context

Redis and Celery are useful for notifications, exports, and AI analysis, but worker availability must not decide whether a human can record an organisational decision.

## Decision

Persist authoritative state synchronously in PostgreSQL. Queue optional work only after commit. Log queue failures and design jobs to be recoverable from durable state.

## Consequences

The product remains usable when workers are stopped and can operate at lower pre-revenue cost. Features requiring delayed work must expose status and retry semantics rather than hiding failure.
