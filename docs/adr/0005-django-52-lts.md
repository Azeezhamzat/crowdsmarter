# ADR 0005: Start on the Django 5.2 LTS line

- Status: Accepted
- Date: 2026-07-25

## Context

The product prioritises predictable maintenance and security support over immediate adoption of each framework major release.

## Decision

Pin Django to the 5.2 LTS minor line and accept current security/bug-fix patches within that line. Pin Django REST Framework to the compatible 3.16 line.

## Consequences

Patch upgrades remain routine while framework-major changes are deliberate. Dependency automation should propose tested patch updates. A move to a later LTS will receive its own upgrade plan and regression pass.
