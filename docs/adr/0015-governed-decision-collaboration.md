# ADR 0015: Governed append-only decision collaboration

## Status

Accepted.

## Context

The structured reasoning domains preserve formal decision inputs, but users also need to ask questions, record concerns, provide updates, and explain context during the workflow. A conventional chat stream would encourage transient conversation, silent edits, and decision authority outside the governed record.

## Decision

Add an organisation- and decision-scoped collaboration domain with four entry types: note, question, concern, and update. Entries are attributable and append-only. Replies reference another entry without creating unrestricted nested conversations. Mentions are limited to active organisation members.

Questions and concerns may receive an explicit resolution record from the decision owner or an organisation manager. The resolution does not modify the original entry. New collaboration is blocked once a decision is archived.

## Consequences

- Deliberation context is preserved without turning the product into a chat application.
- Unresolved questions and concerns become visible portfolio work.
- Mention and resolution notifications remain focused and attributable.
- Corrections are made by adding a new entry, preserving history.
- Realtime websockets and third-party messaging infrastructure are unnecessary.
