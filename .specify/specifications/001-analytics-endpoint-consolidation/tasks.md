# Tasks: Analytics endpoint consolidation (TDD-first)

Feature: Consolidate `/analytics/semesters` and `/analytics/semesters/{semester_number}`

Guidelines: Follow SDD constitution: write tests first, create failing tests, implement to pass, then refactor. Keep shim enabled by default.

## Tasks

1. [P] Create contract tests for consolidated endpoint (Red)
   - File: `tests/contracts/test_analytics_semesters_contract.py`
   - Tests should assert the response envelope and schema for:
     - All semesters (no query param)
     - Specific semester (`?semester_number=1`)
   - Expected: failing (no route change yet)

2. [P] Create integration test to exercise controller → service → DB (Red)
   - File: `tests/integration/test_analytics_semesters_integration.py`
   - Use ephemeral DB fixture; insert sample grades for user; assert both endpoints return correct SGPA and subject lists.
   - Expected: failing

3. Update config to add `ANALYTICS_ALLOW_OLD_ROUTE` (code change)
   - File: `app/core/config.py` and `.env.example`
   - Default: `true`

4. Implement consolidated handler (Green)
   - File: `app/analytics/controller.py`
   - Update `GET /analytics/semesters` to accept optional `semester_number` query param; remove duplicate route registration (but register shim when env var true)

5. Implement compatibility shim (Green)
   - Register `GET /analytics/semesters/{semester_number}` only when `ANALYTICS_ALLOW_OLD_ROUTE=true`. When hit, add headers:
     - `Deprecation: true`
     - `Link: </analytics/semesters?semester_number={semester_number}>; rel="alternate"`

6. Implement unit tests for controller logic (Green)
   - Mock service responses and confirm controller behavior for both branches.

7. Update OpenAPI docs (code/docstring changes) and `specs` examples (docs)
   - Verify docs by running `uvicorn` locally and checking `/docs`.

8. Update CHANGELOG and add `specs/001-analytics-endpoint-consolidation/quickstart.md` with usage examples.

9. CI: Add test run step and ensure new tests run in pipeline.

10. Post-merge: Monitor `analytics.old_route.hits` metric for two release cycles; schedule removal of shim after client migration.

## Notes
- Mark tasks 1 and 2 as `[P]` (parallel) since they are test creation tasks and can be done by separate contributors.
- Keep each task small and focused; avoid introducing additional features during these changes.

*** End tasks ***