# GPAlytics Backend

FastAPI backend for GPA analytics platform. Clean, simple, and production-ready.

## Features

- **JWT Authentication** - Secure user registration and login
- **Azure SQL Database** - Production cloud database
- **FastAPI** - Modern, fast web framework
- **SQLModel** - Type-safe database models
- **Async/Await** - High-performance async operations

## Quick Start

```bash
# Install dependencies
uv install

# Run development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest
```

## API Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication  
- `GET /health` - Health check

## Environment Setup

Create `.env` file:
```env
DATABASE_URL=your_azure_sql_connection_string
JWT_SECRET_KEY=your_secret_key
DEBUG=true
ENVIRONMENT=development
```

## Testing

Simple integration tests using the same Azure SQL database as development. Tests create unique test data and clean up after themselves.

```bash
uv run pytest tests/test_auth.py -v
```

## Tech Stack

- **FastAPI** - Web framework
- **SQLModel** - Database ORM
- **Azure SQL** - Cloud database
- **Argon2** - Password hashing
- **JWT** - Authentication tokens
- **Pytest** - Testing framework