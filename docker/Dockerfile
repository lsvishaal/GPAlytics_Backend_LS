# ==========================================
# Multi-stage Dockerfile for GPAlytics Backend
# Uses UV for 10x faster builds than pip
# ==========================================

# ==========================================
# BUILDER STAGE - Dependencies only
# ==========================================
FROM python:3.12-slim as builder

# Install system dependencies for SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc-dev \
    g++ \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install UV - the fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.lock* ./

# Install dependencies with UV (10x faster than pip!)
RUN uv sync --frozen --no-dev --no-cache

# ==========================================
# RUNTIME STAGE - Minimal production image
# ==========================================
FROM python:3.12-slim as runtime

# Install only runtime dependencies for SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy UV binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY app/ ./app/
COPY pyproject.toml ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create logs directory and set permissions
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Create UV cache directory for the non-root user
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser/.cache

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Use UV to run the application with proper signal handling
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
