#!/usr/bin/env bash
# Development scripts using UV (no pip!)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if UV is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        echo_error "UV is not installed. Install it first:"
        echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    echo_success "UV is installed: $(uv --version)"
}

# Function to install dependencies
install_deps() {
    echo_info "Installing dependencies with UV..."
    uv sync
    echo_success "Dependencies installed!"
}

# Function to run development server
dev_server() {
    echo_info "Starting development server..."
    export PYTHONPATH="src"
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
}

# Function to run tests
run_tests() {
    echo_info "Running tests with pytest..."
    export PYTHONPATH="src"
    uv run pytest src/ -v
}

# Function to run linting
run_lint() {
    echo_info "Adding linting tools..."
    uv add --dev ruff black isort
    
    echo_info "Running code formatting..."
    uv run black src/
    uv run isort src/
    
    echo_info "Running linting..."
    uv run ruff check src/
}

# Function to build Docker image
build_docker() {
    echo_info "Building Docker image..."
    docker build -t gpalytics-backend .
    echo_success "Docker image built!"
}

# Function to run Docker Compose
run_docker() {
    echo_info "Starting Docker Compose..."
    docker-compose up --build -d
    echo_success "Docker services started!"
    echo_info "API: http://localhost:8000"
    echo_info "Health: http://localhost:8000/health"
}

# Function to stop Docker Compose
stop_docker() {
    echo_info "Stopping Docker Compose..."
    docker-compose down
    echo_success "Docker services stopped!"
}

# Function to run Docker Compose for development
run_docker_dev() {
    echo_info "Starting Docker Compose in development mode..."
    docker-compose --profile dev up --build -d
    echo_success "Docker services started in dev mode!"
    echo_info "API: http://localhost:8001 (with hot-reload)"
}

# Function to show logs
show_logs() {
    echo_info "Showing Docker logs..."
    docker-compose logs -f app
}

# Function to clean up
cleanup() {
    echo_info "Cleaning up..."
    docker-compose down -v
    docker system prune -f
    echo_success "Cleanup complete!"
}

# Main script logic
case "$1" in
    "check")
        check_uv
        ;;
    "install")
        check_uv
        install_deps
        ;;
    "dev")
        check_uv
        dev_server
        ;;
    "test")
        check_uv
        run_tests
        ;;
    "lint")
        check_uv
        run_lint
        ;;
    "build")
        build_docker
        ;;
    "up")
        run_docker
        ;;
    "dev-docker")
        run_docker_dev
        ;;
    "down")
        stop_docker
        ;;
    "logs")
        show_logs
        ;;
    "clean")
        cleanup
        ;;
    *)
        echo_info "GPAlytics Backend Development Commands"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  check       - Check if UV is installed"
        echo "  install     - Install dependencies with UV"
        echo "  dev         - Run development server"
        echo "  test        - Run tests"
        echo "  lint        - Run code formatting and linting"
        echo "  build       - Build Docker image"
        echo "  up          - Start Docker Compose"
        echo "  dev-docker  - Start Docker Compose in dev mode"
        echo "  down        - Stop Docker Compose"
        echo "  logs        - Show Docker logs"
        echo "  clean       - Clean up Docker resources"
        echo ""
        echo_warning "Always use UV instead of pip for this project!"
        ;;
esac
