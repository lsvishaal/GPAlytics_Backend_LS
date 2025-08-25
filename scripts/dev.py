#!/usr/bin/env python3
"""
Cross-platform development script for GPAlytics Backend
Replaces separate PowerShell and Bash scripts
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path

# Colors for cross-platform output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_info(msg): print(f"{Colors.BLUE}🚀 {msg}{Colors.END}")
def print_success(msg): print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")
def print_error(msg): print(f"{Colors.RED}❌ {msg}{Colors.END}")

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check, 
                              capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        print_error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_requirements():
    """Check if required tools are installed"""
    tools = {
        'uv': 'uv --version',
        'docker': 'docker --version',
        'docker-compose': 'docker compose version'
    }
    
    for tool, cmd in tools.items():
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            print_error(f"{tool} is not installed or not in PATH")
            return False
    
    print_success("All required tools are available")
    return True

def install_deps():
    """Install dependencies with UV"""
    print_info("Installing dependencies with UV...")
    run_command("uv sync")
    print_success("Dependencies installed!")

def dev_server():
    """Start development server"""
    print_info("Starting development server...")
    run_command("uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

def run_tests():
    """Run tests"""
    print_info("Running tests...")
    run_command("uv run pytest tests/ -v")

def docker_dev():
    """Start Docker development environment"""
    print_info("Starting Docker development environment...")
    run_command("docker compose -f docker/docker-compose.yml --profile dev up --build -d")
    print_success("Development environment started!")
    print_info("🌐 API: http://localhost:8000")
    print_info("🗄️  SQL Server: localhost:1433")

def docker_prod():
    """Start Docker production environment"""
    print_info("Starting Docker production environment...")
    run_command("docker compose -f docker/docker-compose.yml --profile prod up --build -d")
    print_success("Production environment started!")

def docker_stop():
    """Stop Docker services"""
    print_info("Stopping Docker services...")
    run_command("docker compose -f docker/docker-compose.yml down")
    print_success("Docker services stopped!")

def docker_logs():
    """Show Docker logs"""
    print_info("Showing Docker logs...")
    run_command("docker compose -f docker/docker-compose.yml logs -f")

def health_check():
    """Check service health"""
    import requests
    
    endpoints = {
        'Development': 'http://localhost:8000/health',
        'Production': 'http://localhost:8000/health'
    }
    
    for name, url in endpoints.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"{name} service is healthy!")
            else:
                print_warning(f"{name} service returned status {response.status_code}")
        except requests.exceptions.RequestException:
            print_warning(f"{name} service is not responding")

def cleanup():
    """Clean up Docker resources"""
    print_info("Cleaning up Docker resources...")
    run_command("docker compose -f docker/docker-compose.yml down -v")
    run_command("docker system prune -f")
    print_success("Cleanup complete!")

def main():
    parser = argparse.ArgumentParser(description='GPAlytics Backend Development Tool')
    parser.add_argument('command', choices=[
        'check', 'install', 'dev', 'test', 'docker-dev', 'docker-prod', 
        'docker-stop', 'logs', 'health', 'clean'
    ], help='Command to run')
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    
    print_info(f"GPAlytics Backend - {args.command.upper()}")
    
    if args.command == 'check':
        check_requirements()
    elif args.command == 'install':
        if check_requirements():
            install_deps()
    elif args.command == 'dev':
        dev_server()
    elif args.command == 'test':
        run_tests()
    elif args.command == 'docker-dev':
        docker_dev()
    elif args.command == 'docker-prod':
        docker_prod()
    elif args.command == 'docker-stop':
        docker_stop()
    elif args.command == 'logs':
        docker_logs()
    elif args.command == 'health':
        health_check()
    elif args.command == 'clean':
        cleanup()

if __name__ == '__main__':
    main()
