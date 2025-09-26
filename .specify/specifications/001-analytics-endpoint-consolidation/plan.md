# Plan: Consolidate analytics semester endpoints

Status: Draft

## Summary

This plan details the minimal, low-risk changes required to consolidate `GET /analytics/semesters` and `GET /analytics/semesters/{semester_number}` into a single canonical endpoint: `GET /analytics/semesters` with an optional `semester_number` query parameter.

Guiding principles: follow the project constitution (SDD, TDD, minimal changes, backward compatibility), keep changes small (Simplicity Gate), and ensure tests cover behavior.

## Technical Approach

1. Route changes
   - Remove route registration for `GET /analytics/semesters/{semester_number}` from `analytics/controller.py`.
   - Update `GET /analytics/semesters` handler to accept an optional `semester_number: int | None = None` query parameter and branch behavior accordingly.
   - Add a compatibility shim controlled by env var `ANALYTICS_ALLOW_OLD_ROUTE`:
     - If `true` (default during migration), register the old route but emit deprecation headers.
     - If `false`, do not register the old route.

2. Configuration
   - Add `ANALYTICS_ALLOW_OLD_ROUTE` to config (default `true`). Document in `.env.example`.

3. Tests
   - Contract tests (unit-style) for `analytics/controller` verifying response shape for both all semesters and specific semester.
   - Integration tests that use the existing ephemeral DB fixture to insert sample grade records and verify both endpoints.
   - Backward compatibility test toggling `ANALYTICS_ALLOW_OLD_ROUTE=false` to ensure old route is absent.

4. Docs
   - Update OpenAPI examples (FastAPI `responses` and `examples`) in controller docstrings.
   - Add changelog entry and `specs/001-analytics-endpoint-consolidation/quickstart.md` summarizing usage.

5. Release & Migration
   - Merge to `master` behind a feature branch and release with notes: `Deprecated /analytics/semesters/{semester_number}. Use /analytics/semesters?semester_number=`.
   - Monitor logs for usage of old route (add metric `analytics.old_route.hits`).
   - After one release cycle, flip `ANALYTICS_ALLOW_OLD_ROUTE=false` and remove shim.

## File Changes (Planned)

- `app/analytics/controller.py` — update handler, optional shim registration
- `app/core/config.py` — add `ANALYTICS_ALLOW_OLD_ROUTE` config
- `tests/integration/` — add integration tests for consolidation
- `.specify/specifications/001-analytics-endpoint-consolidation/*` — spec, plan, tasks, quickstart

## Risk Analysis

- Low: Behavior remains identical if shim enabled. Risk occurs during removal of shim when clients may still use old route.
- Mitigation: Deprecation headers, CHANGELOG, and monitoring metric.

## Gate Checks

- Simplicity Gate: Changes touch `app/analytics/controller.py` and `app/core/config.py` (≤3 modules) — PASS.
- Security Gate: No auth changes — PASS.
- Performance Gate: No algorithmic change — PASS.

## Estimated Effort

- Implementation & tests: 3-5 hours
- Review & QA: 1-2 hours
- Release & monitoring: 30 minutes

---

Next: generate `tasks.md` with TDD-first tasks.