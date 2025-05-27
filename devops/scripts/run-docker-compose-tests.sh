#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Docker Compose Integration Tests${NC}"
echo "========================================"

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up Docker environment...${NC}"
    docker compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if docker compose is available
if ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${YELLOW}🏗️  Building and starting test environment...${NC}"

# Build and start services with proper waiting
if docker compose -f docker-compose.test.yml up -d --build --wait; then
    echo -e "${GREEN}✅ Test environment is ready!${NC}"
else
    echo -e "${RED}❌ Failed to start test environment${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Verifying service health...${NC}"

# Check application health
if docker compose -f docker-compose.test.yml exec -T app curl -f http://localhost:8080/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Application is healthy${NC}"
else
    echo -e "${RED}❌ Application health check failed${NC}"
    docker compose -f docker-compose.test.yml logs app
    exit 1
fi

# Check Firestore emulator
if docker compose -f docker-compose.test.yml exec -T firestore-emulator nc -z localhost 8080 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Firestore emulator is healthy${NC}"
else
    echo -e "${RED}❌ Firestore emulator health check failed${NC}"
    docker compose -f docker-compose.test.yml logs firestore-emulator
    exit 1
fi

echo -e "${YELLOW}🧪 Running Docker integration tests...${NC}"

# Create local test results directory
mkdir -p test-results

# Run tests using the test runner service
if docker compose -f docker-compose.test.yml run --rm test-runner; then
    echo -e "${GREEN}✅ Docker tests completed successfully!${NC}"

    # Copy test results
    docker compose -f docker-compose.test.yml cp test-runner:/app/test-results ./test-results/ 2>/dev/null || true

    # Show results summary
    if [ -f test-results/docker-tests.xml ]; then
        echo -e "${GREEN}📊 Test results saved to test-results/${NC}"
        ls -la test-results/
    fi

    echo -e "${GREEN}🎉 All Docker integration tests passed!${NC}"
else
    echo -e "${RED}❌ Docker tests failed${NC}"

    # Show logs for debugging
    echo -e "${YELLOW}🔍 Application logs:${NC}"
    docker compose -f docker-compose.test.yml logs app

    echo -e "${YELLOW}🔍 Test runner logs:${NC}"
    docker compose -f docker-compose.test.yml logs test-runner

    exit 1
fi
