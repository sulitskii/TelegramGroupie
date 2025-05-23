#!/bin/bash

set -e

# Default behavior
DOCKER_TESTS=false
INTERACTIVE=false
NO_CLEANUP=false

# Set proper Docker Compose project name (instead of directory name)
export COMPOSE_PROJECT_NAME="telegramgroupie"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --docker)
      DOCKER_TESTS=true
      shift
      ;;
    --interactive)
      INTERACTIVE=true
      shift
      ;;
    --no-cleanup)
      NO_CLEANUP=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --docker       Run Docker integration tests"
      echo "  --interactive  Ask before running Docker tests"
      echo "  --no-cleanup   Skip Docker cleanup (useful for debugging)"
      echo "  --help, -h     Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                    # Run unit tests only"
      echo "  $0 --docker           # Run unit + Docker tests with cleanup"
      echo "  $0 --docker --no-cleanup  # Run tests, keep containers for debugging"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

echo "🧪 Running TelegramGroupie Tests"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Docker cleanup function
cleanup_docker() {
    local reason=$1
    if [[ "$NO_CLEANUP" == "true" ]]; then
        print_warning "Cleanup skipped due to --no-cleanup flag"
        if [[ "$reason" == "failed" ]]; then
            echo "💡 Containers preserved for debugging. You can inspect them with:"
            echo "   docker compose -f docker-compose.test.yml logs"
            echo "   docker compose -f docker-compose.test.yml exec app bash"
            echo "   docker compose -f docker-compose.test.yml down -v  # when done debugging"
        fi
        return 0
    fi

    if [[ "$reason" == "failed" ]]; then
        print_warning "Cleanup skipped - containers preserved for debugging"
        echo "💡 You can inspect the failed containers with:"
        echo "   docker compose -f docker-compose.test.yml logs"
        echo "   docker compose -f docker-compose.test.yml exec app bash"
        echo "   docker compose -f docker-compose.test.yml down -v  # when done debugging"
        return 0
    fi

    print_status "Cleaning up Docker containers..."
    if docker compose -f docker-compose.test.yml down -v --remove-orphans >/dev/null 2>&1; then
        echo "🧹 Docker cleanup completed"
    else
        print_warning "Docker cleanup had some issues (this is usually OK)"
    fi
}

# Run Docker tests function
run_docker_tests() {
    if [[ "$NO_CLEANUP" == "true" ]]; then
        # For debugging: keep services running
        print_status "Starting Docker services (debug mode)..."
        if ! docker compose -f docker-compose.test.yml up -d --build; then
            print_error "Failed to start Docker services"
            return 1
        fi
        
        # Wait for services to be ready
        print_status "Waiting for services to be ready..."
        sleep 10
        
        # Run tests against running services
        print_status "Running tests against persistent services..."
        if docker compose -f docker-compose.test.yml run --rm test-runner; then
            print_success "Docker tests passed"
            print_warning "Services left running for debugging"
            echo "💡 When done debugging, clean up with:"
            echo "   docker compose -f docker-compose.test.yml down -v"
            return 0
        else
            print_error "Docker tests failed"
            print_warning "Services left running for debugging"
            echo "💡 Debug with:"
            echo "   docker compose -f docker-compose.test.yml logs app"
            echo "   docker compose -f docker-compose.test.yml exec app bash"
            echo "   docker compose -f docker-compose.test.yml down -v  # when done"
            return 1
        fi
    else
        # Normal mode: clean up automatically
        if docker compose -f docker-compose.test.yml up --build --abort-on-container-exit; then
            return 0
        else
            return 1
        fi
    fi
}

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Not in a virtual environment. Consider running: source venv/bin/activate"
fi

# Unit Tests
print_status "Running unit tests..."
if python -m pytest tests/unit/ -v; then
    print_success "Unit tests passed"
else
    print_error "Unit tests failed"
    exit 1
fi

# Docker Tests
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    if [[ "$INTERACTIVE" == "true" ]]; then
        echo
        read -p "🐳 Run Docker integration tests? (y/N): " run_docker
        if [[ $run_docker =~ ^[Yy]$ ]]; then
            DOCKER_TESTS=true
        fi
    fi

    if [[ "$DOCKER_TESTS" == "true" ]]; then
        echo
        
        # Pre-test cleanup (unless in debug mode)
        if [[ "$NO_CLEANUP" != "true" ]]; then
            print_status "Preparing Docker environment..."
            cleanup_docker "prepare"
        else
            print_status "Preparing Docker environment (debug mode)..."
            print_warning "Skipping pre-test cleanup due to --no-cleanup flag"
        fi
        
        # Run Docker tests
        print_status "Running Docker integration tests..."
        DOCKER_TEST_SUCCESS=false
        
        if run_docker_tests; then
            print_success "Docker tests passed"
            DOCKER_TEST_SUCCESS=true
        else
            print_error "Docker tests failed"
        fi
        
        # Post-test cleanup (conditional)
        if [[ "$DOCKER_TEST_SUCCESS" == "true" ]]; then
            cleanup_docker "success"
        else
            cleanup_docker "failed"
            exit 1
        fi
    else
        echo
        echo "ℹ️  Docker tests skipped. Use --docker to run them or --interactive to be prompted."
    fi
else
    print_warning "Docker not available, skipping Docker tests"
fi

echo
print_success "All tests completed successfully!"
echo "🎉 Your code is ready!" 