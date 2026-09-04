# Development Guide

## Environment Setup
Use Python 3.12+ and Node.js 20+. Use Docker for isolated testing.

## Coding Standards
- **Python**: Use `ruff` for linting and formatting, `mypy` for static typing.
- **TypeScript**: Use `eslint` and strict mode.

## Testing Strategy
- Unit tests for all utility functions.
- Integration tests for the full pipeline.
- Fixture-based testing.

## Phase-based Development Workflow
Follow the project's phased delivery approach, achieving Definition of Done at each phase.

## DATASET / FIXTURE SOURCING
Test fixtures will come from:
1. Synthetic diagrams generated programmatically for testing.
2. Self-scanned pages from out-of-copyright textbooks (pre-1927 or explicit PD).
3. OER diagram sets from OpenStax or similar CC-licensed sources.

All fixtures must have documented provenance and licensing.
Fixture metadata is stored in `data/fixtures/manifest.json`.

## Git Workflow
Feature branches, PRs, and standard commit messages.

## Definition of Done
Code is linted, typed, tested, documented, and successfully passes the Docker build.

## Debug Artifacts
Convention: store temporary debugging images and logs in `debug/` directory, completely `.gitignore`d.
