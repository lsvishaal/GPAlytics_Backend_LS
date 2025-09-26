# GPAlytics Backend — Architecture Overview

This document gives you a fast, opinionated tour of the codebase and how the parts connect. Use it with the scripts in `scripts/` to explore modules and API endpoints interactively.

## Entry Points

- `app/main.py`: FastAPI application definition and router registration.
  - Includes routers from `app/auth`, `app/grades`, `app/analytics`, `app/users`.
  - Sets up CORS and lifespan (startup/shutdown) that manages DB connections.

## Clean Architecture Layers (as implemented)

- Controller (HTTP): `*/controller.py` files define `APIRouter` endpoints and dependency injection.
- Service (Business Logic): `*/service.py` files encapsulate use-cases and DB access orchestration.
- Entities (Data Models): `app/entities/*.py` define SQLModel tables and Pydantic schemas.
- Core (Cross-cutting): `app/core/*` provides config, database, security, exceptions/utilities.

## Domain Packages

- `app/auth/`
  - `controller.py`: HTTP auth endpoints (register, login, get_current_user, forgot-password).
  - `service.py`: Auth business logic, hashing, token issuing.
  - `refresh_service.py`: Refresh token management.

- `app/grades/`
  - `controller.py`: Upload/delete/list endpoints for grades; validates files; orchestrates OCR + storage.
  - `service.py`: Stores parsed grades, de-duplicates, computes SGPA; delete flows.
  - `ocr/`
    - `service.py`: Gemini Vision integration; image enhancement; response cleaning/validation.

- `app/analytics/`
  - `controller.py`: CGPA and semester analytics endpoints.
  - `service.py`: Aggregations and GPA calculations over stored grades.

- `app/users/`
  - `controller.py`: Profile endpoints (current profile retrieval).
  - `service.py`: User-profile business logic.

## Core Utilities

- `app/core/config.py`: Loads environment (dotenv + Pydantic `Settings`).
- `app/core/database.py`: Async SQLModel/SQLAlchemy engine and `get_db_session()` dependency.
- `app/core/security.py`: JWT creation/validation, password hashing utilities.
- `app/core/exceptions.py`: Domain-specific exceptions and HTTP error factories.

## Entities (Data Layer)

- `app/entities/user.py`: `User` table + request/response schemas.
- `app/entities/grade.py`: `Grade`, `GradeUpload` tables + schemas for uploads, summaries, analytics.
- `app/entities/refresh_token.py`: Refresh token table.

## Supporting Files

- `app/constants.py`: Upload limits and allowed MIME types.
- `docker/`: Dockerfiles and `docker-compose.yml` (includes Redis container for future caching/rate-limiting).
- `tests/`: Integration and unit tests (auth, uploads, etc.).
- `*_backup.py` and `OCR/` folder: legacy/older versions retained for reference.

## Typical Request Lifecycles

1) Authentication — `POST /auth/login`
   - Controller validates request → calls `auth_service.login_user()` → issues JWT/refresh tokens → returns user profile + token.

2) Grade Upload — `POST /grades/process-result-card`
   - Controller validates `UploadFile` → `ocr_service.sharpen_image()` → `ocr_service.process_result_card()` (Gemini Vision) → `grades_service.store_extracted_grades()` → returns `UploadStatusResponseSchema` (duplicates handled gracefully).

3) Analytics — `GET /analytics/cgpa`
   - Controller injects `current_user` + `db` → `analytics_service.calculate_user_cgpa()` → returns computed metrics.

## How to Explore Quickly

- Scripts:
  - `uv run python scripts/module_map.py` — prints packages/modules, routers, top-level classes/functions.
  - `uv run python scripts/endpoint_map.py` — introspects FastAPI app and lists all endpoints by tag.

- In VS Code:
  - Search for `router = APIRouter` to see all controllers.
  - Search for `def get_db_session` and `Depends(` to follow DI flows.
  - Search for `auth_service|grades_service|analytics_service|users_service` to see business logic entry points.

## Diagram Notes (what’s missing in the current image)

- Present in code but not in diagram: Users service, Redis (docker-compose), clean layering (Controller→Service→Entity), exceptions/security, CORS & health checks, Docker runtime.
- See `docs/MERMAID_ARCHITECTURE.md` for an updated, code-accurate diagram.
