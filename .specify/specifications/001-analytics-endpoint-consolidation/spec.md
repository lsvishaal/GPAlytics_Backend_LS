# 001 - Analytics endpoint consolidation

Title: Consolidate analytics semester endpoints into `/analytics/semesters`

Author: Automated Spec Draft (you should review and approve)

Date: 2025-09-20

## Context & Motivation

The codebase currently exposes two related endpoints:

- `GET /analytics/semesters` (returns all semesters summary)
- `GET /analytics/semesters/{semester_number}` (returns a specific semester)

Functionally these endpoints overlap: `GET /analytics/semesters` already supports an optional `semester_number` path parameter in the application code. This redundancy causes maintenance burden, duplicated documentation, and confusion for API consumers.

Goal: Consolidate behavior into a single, well-documented endpoint `GET /analytics/semesters` that accepts an optional `semester_number` query parameter (or pathless optional parameter) and deprecate the `/{semester_number}` route.

## Scope

- Update FastAPI routes to remove `GET /analytics/semesters/{semester_number}` and implement consistent behavior under `GET /analytics/semesters`.
- Provide a migration plan and deprecation strategy (headers + changelog + one-release compatibility shim optional).
- Update OpenAPI docs and tests.
- Ensure backward compatibility for one release window by keeping a lightweight shim that returns a `301` or deprecation warning header if the old route is hit (configurable via feature flag).

## Non-Goals

- Major refactors to analytics internals (calculations remain unchanged).
- UI/frontend changes (separate PR expected if necessary).

## Requirements

1. Consolidated endpoint behavior:
   - `GET /analytics/semesters` → if `semester_number` param provided (query), return specific semester data; else return all semesters.
2. Backwards compatibility:
   - `GET /analytics/semesters/{semester_number}` must continue to work for at least one release but should emit a deprecation header: `Deprecation: true` and `Link: </analytics/semesters?semester_number={semester_number}>; rel="alternate"`.
   - Provide a runtime config toggle (`ANALYTICS_ALLOW_OLD_ROUTE=true/false`) to disable the shim.
3. Tests:
   - Contract tests for both responses (all semesters and specific semester).
   - Integration tests exercising controller → service → DB using ephemeral DB fixtures.
4. Documentation:
   - OpenAPI examples updated and `specs/001-analytics-endpoint-consolidation` should include example request/response payloads.

## Acceptance Criteria

- [ ] `GET /analytics/semesters` returns same payloads as before for both all and specific semester queries.
- [ ] Old route `GET /analytics/semesters/{semester_number}` returns 200 and includes deprecation headers while `ANALYTICS_ALLOW_OLD_ROUTE=true`. When `false` it returns 404.
- [ ] OpenAPI docs reflect the consolidation and examples updated.
- [ ] Tests covering both scenarios pass in CI.

## Notes / Open Questions

- [NEEDS CLARIFICATION] Preferred parameter style: query param `?semester_number=3` vs optional pathless param — proposal: use query param to keep the resource path stable.
- [NEEDS CLARIFICATION] How long to keep the compatibility shim? Proposal: one release cycle (document in CHANGELOG).

---

Please review and resolve `[NEEDS CLARIFICATION]` items before proceeding to the plan stage.