# Testing Guide

This document explains the comprehensive testing strategy for **TelegramGroupie**, including the new organized test structure and how to run different types of tests.

## 🏗️ **Test Structure Overview**

```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── test_main.py        # Flask app core functionality
│   ├── test_encryption.py  # Encryption/decryption logic
│   └── test_message_retrieval.py  # Message API endpoints
├── integration/             # End-to-end tests with mocks
│   └── test_integration.py # Complete workflow testing
├── docker/                  # Containerized integration tests
│   └── test_integration_docker.py  # Docker environment tests
└── __init__.py             # Test package initialization
```

## 🧪 **Test Types & Categories**

### **1. Unit Tests** (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Speed**: ⚡ Fast (< 2 seconds)
- **Dependencies**: None (fully mocked)
- **Coverage**: Core business logic, utilities, individual functions

**What's tested**:
- Flask application endpoints (`test_main.py`)
- Encryption/decryption functionality (`test_encryption.py`)
- Message retrieval API (`test_message_retrieval.py`)

### **2. Integration Tests** (`tests/integration/`)
- **Purpose**: Test complete workflows with mock services
- **Speed**: 🏃 Medium (< 5 seconds)
- **Dependencies**: Mock Firestore, Mock KMS, Test server
- **Coverage**: API workflows, service integration, error handling

**What's tested**:
- HTTP API endpoints with realistic data flow
- Message processing from webhook to storage
- Error handling and edge cases
- Performance characteristics

### **3. Docker Tests** (`tests/docker/`)
- **Purpose**: Test containerized deployment scenarios
- **Speed**: 🐌 Slow (30+ seconds)
- **Dependencies**: Docker, Container runtime
- **Coverage**: Production-like environments, networking, service discovery

**What's tested**:
- Container builds and startup
- Service-to-service communication
- Environment variable configuration
- Production deployment scenarios

## 🚀 **Running Tests**

### **Quick Commands**

```bash
# Run unit tests (fastest)
make test-unit

# Run integration tests
make test-integration

# Run Docker tests (requires Docker)
make test-docker

# Run CI test suite (unit + integration)
make test-ci

# Run ALL tests including Docker
make test-all
```

### **Detailed Test Commands**

```bash
# Unit tests with verbose output
python -m pytest tests/unit/ -v --tb=short -m "unit"

# Integration tests with environment
TESTING=true python -m pytest tests/integration/ -v --tb=short -m "integration"

# Docker tests with specific markers
python -m pytest tests/docker/ -v -m "docker"

# Run tests with coverage
python -m pytest tests/unit/ tests/integration/ --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_main.py -v

# Run specific test function
python -m pytest tests/unit/test_main.py::test_healthz_endpoint -v
```

### **Using Test Markers**

```bash
# Run only fast tests (excludes slow and docker)
pytest tests/ -m "not slow and not docker"

# Run only slow tests
pytest tests/ -m "slow"

# Run tests that don't require authentication
pytest tests/ -m "not requires_auth"

# Combine markers
pytest tests/ -m "unit or integration"
```

## 📊 **Test Results & Coverage**

### **Current Test Statistics**
- **Total Tests**: 23 tests
- **Unit Tests**: 12 tests ⚡
- **Integration Tests**: 10 tests 🔗
- **Docker Tests**: 8 tests 🐳
- **Passing**: 22/23 ✅
- **Skipped**: 1 (requires auth) ⏭️

### **Coverage Reports**

```bash
# Generate HTML coverage report
make test-coverage
open htmlcov/index.html

# Generate XML coverage for CI
python -m pytest --cov=. --cov-report=xml

# View coverage in terminal
python -m pytest --cov=. --cov-report=term-missing
```

## 🔧 **Test Configuration**

### **Pytest Configuration** (`pytest.ini`)

```ini
[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
markers =
    unit: fast, isolated unit tests
    integration: tests with mock services
    docker: containerized integration tests
    slow: tests that take > 5 seconds
    requires_auth: tests requiring real credentials
```

### **Environment Variables**

```bash
# For integration tests
export TESTING=true
export GCP_PROJECT_ID=test-project
export WEBHOOK_SECRET=test-secret

# For Docker tests
export APP_URL=http://localhost:8081
export FIRESTORE_EMULATOR_HOST=localhost:8081
```

## 🔄 **CI/CD Integration**

### **GitHub Actions Workflows**

1. **`python-app.yml`** - Main CI pipeline
   - Unit tests (fast)
   - Integration tests (with mocks)
   - Coverage reporting

2. **`docker-tests.yml`** - Docker testing
   - Container builds
   - Docker integration tests
   - Production-like testing

3. **`static-analysis.yml`** - Code quality
   - Linting, security, complexity
   - Quality gates

### **Workflow Execution Strategy**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Unit Tests  │───▶│Integration  │───▶│   Docker    │
│  (2 mins)   │    │Tests (3min) │    │Tests (5min) │
│   Fast ⚡   │    │ Realistic🔗 │    │Production🐳 │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🐛 **Debugging Tests**

### **Common Issues & Solutions**

**1. Import Errors**
```bash
# Ensure proper PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH
python -m pytest tests/unit/test_main.py
```

**2. Mock Failures**
```bash
# Check mock setup in test files
# Ensure mocks are patched before imports
```

**3. Docker Test Failures**
```bash
# Check Docker is running
docker info

# Check container logs
docker logs telegramgroupie-test

# Run with debug
docker run -it telegramgroupie:test bash
```

**4. Environment Issues**
```bash
# Verify environment variables
env | grep TESTING

# Reset test environment
unset TESTING GCP_PROJECT_ID
export TESTING=true
```

### **Debugging Commands**

```bash
# Run with maximum verbosity
pytest tests/ -v -s --tb=long

# Drop into debugger on failure
pytest tests/ --pdb

# Run single test with prints
pytest tests/unit/test_main.py::test_healthz_endpoint -v -s

# Collect test info without running
pytest tests/ --collect-only
```

## 📈 **Performance Testing**

### **Benchmarks**

```bash
# Quick smoke test (< 1 second)
make test-smoke

# Performance test subset
pytest tests/ -m "not slow" -v

# Benchmark specific functions
python -m pytest tests/integration/test_integration.py::TestPerformance -v
```

### **Performance Targets**

- **Unit Tests**: < 2 seconds total
- **Integration Tests**: < 5 seconds total
- **Docker Tests**: < 60 seconds total
- **Health Endpoint**: < 100ms response time
- **API Endpoints**: < 1 second response time

## 🔐 **Security Testing**

### **Security Test Categories**

1. **Input Validation** - Unit tests
2. **Authentication** - Integration tests
3. **Authorization** - Integration tests
4. **Encryption** - Unit & integration tests
5. **Container Security** - Docker tests

### **Security Test Commands**

```bash
# Run security-focused tests
pytest tests/ -k "security or auth or encrypt" -v

# Skip authentication tests (for CI)
pytest tests/ -m "not requires_auth" -v
```

## 📝 **Writing New Tests**

### **Unit Test Template**

```python
"""
Unit Tests for [Component Name]

Tests the [component] functionality using mocks for external dependencies.
"""

import pytest
from unittest.mock import Mock, patch

# Mark all tests as unit tests
pytestmark = pytest.mark.unit

def test_component_function():
    """Test component function with mocked dependencies."""
    # Arrange
    mock_dependency = Mock()

    # Act
    with patch('module.dependency', mock_dependency):
        result = component_function()

    # Assert
    assert result == expected_value
    mock_dependency.assert_called_once()
```

### **Integration Test Template**

```python
"""
Integration Tests for [Feature Name]

Tests the [feature] workflow using mock services for realistic testing.
"""

import pytest
import requests

# Mark all tests as integration tests
pytestmark = pytest.mark.integration

class TestFeatureIntegration:
    """Integration tests for feature workflow."""

    def test_feature_workflow(self, api_client):
        """Test complete feature workflow."""
        # Test realistic workflow
        response = requests.get(f"{api_client}/endpoint")
        assert response.status_code == 200
```

### **Docker Test Template**

```python
"""
Docker Tests for [Container Feature]

Tests the [feature] in containerized environments.
"""

import pytest
import requests

# Mark all tests as docker tests
pytestmark = pytest.mark.docker

class TestDockerFeature:
    """Docker-based tests for container feature."""

    def test_container_feature(self, api_client):
        """Test feature in Docker environment."""
        response = requests.get(f"{api_client}/endpoint")
        assert response.status_code == 200
```

## 🎯 **Best Practices**

### **Test Organization**
1. **One test class per component** - Clear organization
2. **Descriptive test names** - `test_component_action_expected_result`
3. **Arrange-Act-Assert** - Clear test structure
4. **Independent tests** - No test dependencies

### **Mock Strategy**
1. **Unit tests** - Mock all external dependencies
2. **Integration tests** - Mock only slow/unreliable services
3. **Docker tests** - Minimal mocking, real containers

### **Test Data**
1. **Realistic data** - Use production-like test data
2. **Edge cases** - Test boundary conditions
3. **Error scenarios** - Test failure modes

---

This testing guide provides comprehensive coverage of the **TelegramGroupie** testing strategy, from quick unit tests to full Docker integration testing. The organized structure ensures fast development cycles while maintaining confidence in production deployments.

## 🐳 **Enhanced Docker Testing with Compose**

### **Docker Compose Architecture**

Following best practices from modern Docker integration testing guides, we now use Docker Compose for comprehensive service orchestration:

```yaml
# docker-compose.test.yml
services:
  app:                    # Main TelegramGroupie application
  firestore-emulator:     # Google Cloud Firestore emulator
  test-runner:           # Dedicated test execution service
networks:
  test-network:          # Isolated network for service communication
```

### **Key Improvements Over Single Container**

1. **Service Discovery**: Services communicate using service names (`app`, `firestore-emulator`) instead of `localhost`
2. **Health Checks**: Proper health checks with `--wait` flag ensure services are ready
3. **Network Isolation**: All services run in dedicated `test-network`
4. **Dependency Management**: Services start in correct order with `depends_on` conditions
5. **Real Service Integration**: Tests run against actual service dependencies

### **Enhanced Docker Commands**

```bash
# Recommended: Full Docker Compose tests
make docker-test-compose

# Start test environment for development
make docker-up

# Check service health
make docker-health

# View service logs
make docker-logs

# Stop test environment
make docker-down

# Legacy single-container tests
make docker-test-legacy
```

### **Local Docker Development Workflow**

```bash
# Start test environment and keep it running
make docker-up

# In another terminal, run manual tests
curl http://localhost:8080/healthz

# Run tests against running environment
APP_URL=http://localhost:8080 python -m pytest tests/docker/ -v

# Check logs if needed
make docker-logs

# Stop when done
make docker-down
```

## 🔄 **Enhanced Pre-commit Integration**

### **Comprehensive Pre-commit Commands**

```bash
# Full pre-commit suite (includes Docker if available)
make pre-commit

# Fast pre-commit (skips Docker tests)
make pre-commit-fast

# Simulate complete CI pipeline locally
make ci-simulate

# Run EVERYTHING (matches GitHub Actions exactly)
make test-full
```

### **Conditional Docker Testing**

Docker tests are smart about when to run:

- **Local Development**: Always available via `make docker-test-compose`
- **Pull Requests**: Unit + Integration tests only (fast feedback)
- **Main Branch Pushes**: Full test suite including Docker
- **Manual Override**: Use `SKIP_DOCKER=true make pre-commit` to skip

### **Enhanced CI Pipeline Flow**

```
Pull Request (Fast):
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Unit Tests  │───▶│Integration  │───▶│  Coverage   │
│  (1-2 min)  │    │Tests (2min) │    │ (1-2 min)   │
└─────────────┘    └─────────────┘    └─────────────┘

Main Branch Push (Complete):
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Unit Tests  │───▶│Integration  │───▶│Docker Tests │───▶│  Coverage   │
│  (1-2 min)  │    │Tests (2min) │    │ (3-4 min)   │    │ (1-2 min)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### **Updated GitHub Actions Workflows**

#### **1. Main CI Pipeline** (`python-app.yml`)
- ✅ **Unit Tests** → **Integration Tests** → **Docker Tests** (conditional) → **Coverage**
- ✅ **Docker tests only run on main branch pushes** (saves CI resources)
- ✅ **Comprehensive status checking** with final CI success job

#### **2. Enhanced Docker Tests** (`docker-tests.yml`)
- ✅ **Full Docker Compose orchestration** with `--wait` flag
- ✅ **Service health verification** before running tests
- ✅ **Comprehensive test execution** with proper cleanup
- ✅ **Artifact collection** and **detailed log debugging**

#### **3. Static Analysis** (`static-analysis.yml`)
- ✅ **Robust pre-commit hooks**
- ✅ **Ultra-fast Ruff linting**
- ✅ **Comprehensive security scanning**
- ✅ **Type checking with MyPy**

### **Development Workflow Examples**

```bash
# Before committing (fast check)
make pre-commit-fast

# Before pushing to main (full check)
make pre-commit

# Simulate exact CI behavior
make ci-simulate

# Development with Docker services
make docker-up
# ... develop and test ...
make docker-down

# Quick health check
make docker-health
```

---

**🎯 Summary**: The enhanced testing setup provides a comprehensive, fast, and reliable testing pipeline that scales from quick local development to full CI/CD deployment confidence. The Docker Compose integration follows modern best practices while maintaining backward compatibility with existing workflows.
