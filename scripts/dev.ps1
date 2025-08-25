# PowerShell version for Windows
# GPAlytics Backend Development Commands

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("check", "install", "dev", "test", "lint", "build", "up", "dev-docker", "down", "logs", "clean")]
    [string]$Command
)

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Test-UV {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "UV is not installed. Install it first:"
        Write-Host "irm https://astral.sh/uv/install.ps1 | iex"
        exit 1
    }
    $uvVersion = uv --version
    Write-Success "UV is installed: $uvVersion"
}

function Install-Dependencies {
    Write-Info "Installing dependencies with UV..."
    uv sync
    Write-Success "Dependencies installed!"
}

function Start-DevServer {
    Write-Info "Starting development server..."
    $env:PYTHONPATH = "src"
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
}

function Invoke-Tests {
    Write-Info "Running tests with pytest..."
    $env:PYTHONPATH = "src"
    uv run pytest src/ -v
}

function Invoke-Linting {
    Write-Info "Adding linting tools..."
    uv add --dev ruff black isort
    
    Write-Info "Running code formatting..."
    uv run black src/
    uv run isort src/
    
    Write-Info "Running linting..."
    uv run ruff check src/
}

function Build-DockerImage {
    Write-Info "Building Docker image..."
    docker build -t gpalytics-backend .
    Write-Success "Docker image built!"
}

function Start-Docker {
    Write-Info "Starting Docker Compose..."
    docker-compose up --build -d
    Write-Success "Docker services started!"
    Write-Info "API: http://localhost:8000"
    Write-Info "Health: http://localhost:8000/health"
}

function Stop-Docker {
    Write-Info "Stopping Docker Compose..."
    docker-compose down
    Write-Success "Docker services stopped!"
}

function Start-DockerDev {
    Write-Info "Starting Docker Compose in development mode..."
    docker-compose --profile dev up --build -d
    Write-Success "Docker services started in dev mode!"
    Write-Info "API: http://localhost:8001 (with hot-reload)"
}

function Show-Logs {
    Write-Info "Showing Docker logs..."
    docker-compose logs -f app
}

function Invoke-Cleanup {
    Write-Info "Cleaning up..."
    docker-compose down -v
    docker system prune -f
    Write-Success "Cleanup complete!"
}

# Main script logic
switch ($Command) {
    "check" { Test-UV }
    "install" { Test-UV; Install-Dependencies }
    "dev" { Test-UV; Start-DevServer }
    "test" { Test-UV; Invoke-Tests }
    "lint" { Test-UV; Invoke-Linting }
    "build" { Build-DockerImage }
    "up" { Start-Docker }
    "dev-docker" { Start-DockerDev }
    "down" { Stop-Docker }
    "logs" { Show-Logs }
    "clean" { Invoke-Cleanup }
}

# Show help if needed
if ($Command -eq "help" -or -not $Command) {
    Write-Info "GPAlytics Backend Development Commands"
    Write-Host ""
    Write-Host "Usage: .\dev.ps1 -Command {command}"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  check       - Check if UV is installed"
    Write-Host "  install     - Install dependencies with UV"
    Write-Host "  dev         - Run development server"
    Write-Host "  test        - Run tests"
    Write-Host "  lint        - Run code formatting and linting"
    Write-Host "  build       - Build Docker image"
    Write-Host "  up          - Start Docker Compose"
    Write-Host "  dev-docker  - Start Docker Compose in dev mode"
    Write-Host "  down        - Stop Docker Compose"
    Write-Host "  logs        - Show Docker logs"
    Write-Host "  clean       - Clean up Docker resources"
    Write-Host ""
    Write-Warning "Always use UV instead of pip for this project!"
}
