# GPAlytics Backend Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-20

## Active Technologies
- **FastAPI** (async/await patterns, dependency injection)
- **SQLModel** (database models and schemas)
- **Azure SQL Serverless** (connection retry patterns)
- **Gemini Vision AI** (OCR processing)
- **JWT Authentication** (access/refresh tokens)
- **pytest** (async testing, database fixtures)

## Project Structure
```
app/
├── auth/           # Authentication (JWT, user management)
├── grades/         # Grade processing (OCR, storage)
├── analytics/      # GPA calculations, semester data
├── users/          # User profile management
├── core/           # Database, config, security utilities
└── entities/       # Data models (User, Grade, etc.)
```

## Architecture Patterns
- **Controller → Service → Entity** separation
- **Dependency injection** for database sessions and user context
- **Async/await** throughout the stack
- **Error handling** with specific HTTP status codes
- **Constitutional compliance** required for all changes

## Code Style
- Use `async def` for all database operations
- Import entities from `..entities` relative imports
- Follow existing FastAPI router patterns
- Use Pydantic schemas for request/response validation
- Include comprehensive error handling with user-friendly messages

## Constitutional Requirements
All changes MUST comply with:
1. **Clean Architecture** - Controller/Service/Entity separation
2. **Test-First Development** - TDD with pytest-asyncio
3. **Azure SQL Compatibility** - Connection retry logic
4. **Performance Standards** - <2s grade processing, <500ms API responses
5. **Security First** - JWT auth, input validation, no PII in logs

## Recent Changes
- Enhanced OCR pipeline with image sharpening
- Serverless database connection retry logic
- Comprehensive error handling with user guidance

<!-- MANUAL ADDITIONS START -->
## Development Workflow
Use Specification-Driven Development:
1. `/specify` - Define user stories and requirements
2. `/plan` - Technical approach and architecture
3. `/tasks` - Implementation breakdown with TDD
4. `/implement` - Execute test-first development

Reference the constitution at `.specify/memory/constitution.md` for all architectural decisions.
<!-- MANUAL ADDITIONS END -->