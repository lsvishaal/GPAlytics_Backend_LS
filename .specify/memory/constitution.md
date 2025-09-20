# GPAlytics Backend Constitution (SDD-aligned)

## Purpose
This constitution defines practical, enforceable rules for Specification‑Driven Development (SDD) in the GPAlytics Backend. It keeps SDD discipline (specs → plans → tests → implementation) while allowing pragmatic exceptions for real-world operations and developer ergonomics in VS Code with GitHub Copilot.

## At-a-glance Principles
- Specification-First: `/specify` → `/plan` → `/tasks` is required for non-trivial work.
- Test-First: Tests (Red) before implementation (Green). Prefer integration-first tests that exercise the full Controller→Service→Entity flow where feasible.
- Library-First (pragmatic): Prefer small, reusable libraries; expose CLIs or programmatic APIs when it aids testability and observability. JSON I/O is recommended for CLIs handling structured inputs/outputs.
- Simplicity: Start small; avoid speculative features and over-abstraction. Justify complexity in the plan.

## Core Rules (Enforceable)

1. Specification-First
	- All non-trivial features must begin with `/specify` and include acceptance criteria and `[NEEDS CLARIFICATION]` markers for ambiguities.
	- Specs are the single source of truth for expected behavior and tests.

2. Test-First Validation
	- Tests must be authored before implementation. The lifecycle: write tests → validate tests fail → implement → pass tests → refactor.
	- Use `pytest` + `pytest-asyncio` for async flows. Integration tests should run against ephemeral or dockerized databases when practical.

3. Library-First Architecture (Pragmatic)
	- Prefer encapsulating feature logic in libraries/modules that can be imported and tested independently from the FastAPI app.
	- Libraries that provide public behavior should expose a small CLI with JSON in/out for reproducible test runs and observability.

4. Framework & DB Practices
	- Use framework features (FastAPI, SQLModel) where they reduce complexity; avoid wrapping framework behavior unnecessarily.
	- Use dependency injection (`Depends(get_db_session)`, `Depends(get_current_user)`) and avoid global mutable state.
	- Design database access with clear repository or service layers; optimize queries in the planning phase and include performance checks in tests.

5. Security & Privacy
	- Authentication and authorization are mandatory for protected operations. Use JWT + refresh tokens per existing patterns.
	- Do not log PII or secrets. Mask or redact sensitive fields in logs.

6. API Design
	- Prefer consistent response envelopes. Low-level endpoints (health) may be exceptions.
	- Favor consolidated endpoints with optional parameters when it reduces duplication; include an explicit migration plan for endpoint removals.

7. Quality Gates (Gates enforced at planning/review)
	- Simplicity Gate: Initial implementation must touch ≤3 modules/projects; more requires documented impact analysis.
	- Security Gate: Any plan touching auth/PII must include threat model and mitigations.
	- Performance Gate: Critical flows must include measurable acceptance criteria and at least one automated benchmark in CI.

## Development Workflow (Enforced Steps)

1. `/specify` — Create `spec.md` with user stories, acceptance criteria, and `[NEEDS CLARIFICATION]` markers.
2. Human review — A maintainer resolves clarifications.
3. `/plan` — Produce `plan.md` with architecture, data model, complexity analysis, and gate checks.
4. `/tasks` — Emit `tasks.md` with TDD-first tasks; mark parallelizable work with `[P]`.
5. `/implement` — Execute tasks: tests (Red) are created, implementations follow to pass tests (Green), then refactor.
6. Code review & merge — Reviewers must validate constitutional compliance.

## AI-Assisted Development (VS Code / Copilot Notes)

- Copilot/VS Code is a supported AI assistant. Use it to draft specs, plans, and tests, but require human approval before merging any AI-proposed change.
- Store the constitution at `.specify/memory/constitution.md` for easy reference by agents.
- Recommended Copilot usage patterns in VS Code:
  - Use Copilot Chat for iterative `/specify` drafting and clarifications.
  - When Copilot suggests code, require generating failing tests first and attach them to the related spec's `tasks.md`.
  - Use the `/implement` command only after the spec, plan, and tasks are reviewed by a human maintainer.

## Governance & Amendments

- Amendments require a PR that includes: rationale, impact analysis, and migration/rollback plan. At least one maintainer review is required.
- Version and ratification date must be documented at the top of this file.

## Pragmatic Exceptions

- In emergency hotfixes where immediate action prevents production harm, document the exception in the PR and include a rollback plan; retrospective compliance (convert into spec + plan) is required within 7 days.

**Version**: 2.1.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20