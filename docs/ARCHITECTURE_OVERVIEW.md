# GPAlytics Backend — Architecture Overview

This document provides a comprehensive overview of the codebase structure and component interactions. Use it alongside the utility scripts to explore the system architecture.

## Entry Points

- `src/app/main.py`: FastAPI application definition and router registration
  - Includes routers from `src/routers/{auth,users,grades,analytics}`
  - Sets up CORS, health checks, and database lifecycle management

## Clean Architecture Implementation

**Current Active Structure** (routers are the primary implementation):

- **HTTP Layer**: `src/routers/*/api.py` - FastAPI endpoints with dependency injection
- **Business Logic**: `src/routers/*/service.py` - Domain logic and database operations
- **Data Models**: `src/shared/entities.py` - SQLModel tables and Pydantic schemas
- **Core Infrastructure**: `src/shared/*` - Cross-cutting concerns and utilities

**Legacy Structure** (being phased out):
- `src/features/*` - Original feature modules, functionality moved to routers

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
