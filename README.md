# GPAlytics Backend

A clean FastAPI backend for academic performance tracking and GPA analytics. Built with modern Python practices for reliability and maintainability.

## What It Does

- **Student Management**: User registration, authentication with JWT tokens
- **Grade Processing**: OCR-powered grade sheet analysis using Google Gemini Vision
- **Analytics**: Calculate CGPA, semester-wise performance, grade trends
- **API-First**: RESTful endpoints for integration with frontend applications

## Architecture

```
src/
├── app/main.py           # FastAPI application entry point
├── routers/              # HTTP API endpoints (active routes)
│   ├── auth/            # Authentication & user management
│   ├── users/           # User profile operations
│   ├── grades/          # Grade upload & OCR processing
│   └── analytics/       # GPA calculations & reporting
├── shared/              # Core utilities & models
│   ├── entities.py      # Database models (SQLModel)
│   ├── database.py      # Azure SQL connection & sessions
│   ├── security.py      # JWT & password hashing
│   └── config.py        # Environment configuration
└── features/            # Legacy feature modules (being phased out)
```

## Tech Stack

- **FastAPI** - Web framework with automatic OpenAPI docs
- **SQLModel** - Type-safe database models & queries
- **Azure SQL** - Cloud database with auto-scaling
- **Argon2** - Password hashing
- **JWT** - Stateless authentication
- **Google Gemini Vision** - OCR for grade sheet processing
- **Docker** - Containerized deployment

## Getting Started

### Prerequisites
- Python 3.12+
- UV package manager
- Azure SQL Database (or modify for local SQLite)

### Installation

```bash
# Clone the repository
git clone https://github.com/lsvishaal/GPAlytics_Backend_LS.git
cd GPAlytics_Backend_LS

# Install dependencies
uv install

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials and secrets
```

### Environment Configuration

Create `.env` file with:

```env
# Database
DATABASE_URL="mssql+aioodbc://user:pass@server.database.windows.net:1433/db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"

# Authentication
JWT_SECRET_KEY="your-secret-key-here"
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# OCR Processing
GEMINI_KEY="your-google-gemini-api-key"

# Application
DEBUG=true
ENVIRONMENT=development
```

### Running the Application

```bash
# Development server (auto-reload)
uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000

# With Docker
docker-compose up --build
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Authenticate user & get JWT tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/forgot-password` - Password reset

### User Management
- `GET /users/me` - Get current user profile

### Grade Management
- `POST /grades/upload` - Upload grade sheet (OCR processing)
- `GET /grades/` - List user's grades
- `DELETE /grades/semester/{id}` - Delete semester grades

### Analytics
- `GET /analytics/cgpa` - Calculate overall CGPA
- `GET /analytics/semesters` - Semester-wise breakdown

## Development Workflow

### Running Tests
```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src

# Specific test file
uv run pytest tests/integration/auth/test_login.py -v
```

### Code Quality
```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Database Operations
```bash
# Reset database (development only)
uv run python scripts/reset_db.py

# Check database health
curl http://localhost:8000/health
```

## Deployment

### Docker Production
```bash
# Build production image
docker build -f docker/Dockerfile -t gpalytics-backend .

# Run with environment
docker run -p 8000:8000 --env-file .env gpalytics-backend
```

### Azure Container Instances
Configured in `docker/docker-compose.yml` for Azure deployment with:
- Azure SQL Database integration
- Redis caching layer
- Health checks & monitoring

## Project Structure Explained

- **`src/routers/`** - Active API routes following feature-based organization
- **`src/shared/`** - Core utilities shared across all features
- **`src/features/`** - Legacy modules being gradually removed
- **`tests/`** - Test suite mirroring src structure
- **`docker/`** - Containerization configs
- **`docs/`** - Architecture documentation

## Contributing

1. Create feature branch from `development`
2. Make changes following existing patterns
3. Add tests for new functionality
4. Update documentation as needed
5. Submit PR with clear description

## License

Private project - All rights reserved.