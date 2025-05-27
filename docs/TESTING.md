# Testing Guide

This document explains the comprehensive testing strategy for **TelegramGroupie**, including the dependency injection test structure and how to run different types of tests.

## 🏗️ **Test Structure Overview**

```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── test_main.py        # Flask app core functionality
│   ├── test_encryption.py  # Encryption/decryption logic
│   └── test_message_retrieval.py  # Message API endpoints
├── docker/                  # Containerized integration tests
│   └── test_integration_docker.py  # Docker environment tests
└── __init__.py             # Test package initialization
```

## 🧪 **Test Types & Categories**

### **1. Unit Tests** (`tests/unit/`)
- **Purpose**: Test individual components in isolation with dependency injection
- **Speed**: ⚡ Fast (< 2 seconds)
- **Dependencies**: None (uses injected test implementations)
- **Coverage**: Core business logic, utilities, individual functions

**What's tested**:
- Flask application endpoints with test service container (`test_main.py`)
- Encryption/decryption functionality with mock KMS (`test_encryption.py`)
- Message retrieval API with mock database (`test_message_retrieval.py`)

### **2. Docker Tests** (`tests/docker/`)
- **Purpose**: Test containerized deployment scenarios with realistic networking
- **Speed**: 🐌 Slow (30+ seconds)
- **Dependencies**: Docker, Container runtime, test service implementations
- **Coverage**: Production-like environments, networking, service discovery

**What's tested**:
- Container builds and startup with dependency injection
- Service-to-service communication using test implementations
- Environment variable configuration with APP_ENV=test
- Production deployment scenarios with mock services

## 🔧 **Dependency Injection Testing Strategy**

### **Environment Detection**
The application automatically detects test environments and injects appropriate implementations:

```python
# Automatic test environment detection
def create_service_container(environment: str = None) -> ServiceContainer:
    if environment is None:
        if os.environ.get("APP_ENV") == "test":
            environment = "test"
        elif os.environ.get("FLASK_ENV") == "testing":
            environment = "test"
        elif "pytest" in os.environ.get("_", ""):
            environment = "test"
        else:
            environment = "production"
    
    return (TestServiceContainer() if environment == "test" 
            else ProductionServiceContainer())
```

### **Test Service Implementations**
Tests use mock implementations injected via the test service container:

- **TestDatabaseClient**: In-memory dictionary storage, no network calls
- **TestEncryptionService**: Base64 encoding for deterministic testing
- **TestTelegramBot**: Logs messages instead of sending to Telegram
- **TestMessageHandler**: Processes messages with test implementations

### **Key Benefits**
✅ **Identical Logic**: Tests validate the same code that runs in production
✅ **No Conditional Code**: Zero environment-specific branches in application logic
✅ **Fast Execution**: Mock implementations eliminate network latency
✅ **Deterministic**: Consistent results across all test runs

## 🚀 **Running Tests**

### **Quick Commands**

```bash
# Run unit tests (fastest)
make test-unit

# Run Docker tests (requires Docker)
make test-docker

# Run all tests
make test-all

# Run tests with coverage
make test-coverage
```

### **Detailed Test Commands**

```bash
# Unit tests with verbose output
python -m pytest tests/unit/ -v --tb=short

# Unit tests with dependency injection validation
APP_ENV=test python -m pytest tests/unit/ -v --tb=short

# Docker tests with test environment
python -m pytest tests/docker/ -v

# Run tests with coverage report
python -m pytest tests/unit/ --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_main.py -v

# Run specific test function
python -m pytest tests/unit/test_main.py::test_healthz_endpoint -v
```

### **Using Test Markers**

```bash
# Run only fast tests (excludes docker)
pytest tests/ -m "not docker"

# Run Docker tests only
pytest tests/ -m "docker"

# Run specific test categories
pytest tests/ -k "encryption"
```

## 📊 **Test Results & Coverage**

### **Current Test Statistics**
- **Total Tests**: 23 tests
- **Unit Tests**: 15 tests ⚡
- **Docker Tests**: 8 tests 🐳
- **Passing**: 23/23 ✅
- **Coverage**: >90% of application code

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

### **Environment Variables**

```bash
# For dependency injection testing
export APP_ENV=test
export GCP_PROJECT_ID=test-project
export WEBHOOK_SECRET=test-secret

# For Docker tests
export APP_URL=http://app:8080

# Alternative environment variable (legacy support)
export FLASK_ENV=testing
```

### **Test Service Container Configuration**

The test environment automatically configures mock services:

```python
# Test implementations are injected automatically
app = create_app(environment="test")

# No need to manually configure mocks:
# - TestDatabaseClient replaces ProductionDatabaseClient
# - TestEncryptionService replaces ProductionEncryptionService
# - TestTelegramBot replaces ProductionTelegramBot
```

## 🔄 **CI/CD Integration**

### **GitHub Actions Workflows**

1. **`python-app.yml`** - Main CI pipeline
   - Unit tests with dependency injection
   - Coverage reporting
   - Fast feedback loop

2. **`static-analysis.yml`** - Code quality
   - Linting, security, complexity
   - Quality gates

### **Workflow Execution Strategy**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Unit Tests  │───▶│   Docker    │───▶│   Deploy    │
│  (2 mins)   │    │Tests (5min) │    │  (Manual)   │
│   Fast ⚡   │    │Production🐳 │    │     🚀      │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🐛 **Debugging Tests**

### **Common Issues & Solutions**

**1. Environment Detection Issues**
```bash
# Verify environment detection
export APP_ENV=test
python -c "from main import create_app; app = create_app(); print('Environment detected correctly')"
```

**2. Service Container Issues**
```bash
# Debug service container creation
python -c "
from service_container import create_service_container
container = create_service_container('test')
print(f'Container type: {type(container).__name__}')
"
```

**3. Docker Test Failures**
```bash
# Check Docker is running
docker info

# Run with verbose logging
docker-compose -f docker-compose.test.yml up --build

# Check application logs
docker-compose -f docker-compose.test.yml logs app
```

### **Debugging Commands**

```bash
# Run with maximum verbosity
pytest tests/ -v -s --tb=long

# Drop into debugger on failure
pytest tests/ --pdb

# Run single test with debug output
pytest tests/unit/test_main.py::test_healthz_endpoint -v -s

# Test environment detection
APP_ENV=test python -m pytest tests/unit/ -v -s
```

## 📈 **Performance Testing**

### **Performance Targets**

- **Unit Tests**: < 2 seconds total
- **Docker Tests**: < 60 seconds total
- **Health Endpoint**: < 100ms response time
- **API Endpoints**: < 1 second response time

### **Benchmarks**

```bash
# Quick unit test run
time make test-unit

# Docker test with timing
time make test-docker

# Performance test specific endpoints
pytest tests/unit/test_main.py::test_healthz_endpoint -v --durations=10
```

## 🔐 **Security Testing**

### **Security Test Coverage**

1. **Input Validation** - Unit tests with mock services
2. **Encryption** - Unit tests with TestEncryptionService
3. **Authentication** - Integration tests with test implementations
4. **Container Security** - Docker tests with APP_ENV=test

### **Security Test Commands**

```bash
# Run security-focused tests
pytest tests/ -k "security or auth or encrypt" -v

# Test encryption with mock KMS
pytest tests/unit/test_encryption.py -v
```

## 📝 **Writing New Tests**

### **Unit Test Template**

```python
"""
Unit Tests for [Component Name]

Tests the [component] functionality using dependency injection with test implementations.
"""

import pytest
from main import create_app

class TestComponent:
    """Unit tests for component using dependency injection."""
    
    def setup_method(self):
        """Set up test environment with injected test services."""
        self.app = create_app(environment="test")
        self.client = self.app.test_client()
        
    def test_component_function(self):
        """Test component function with injected test implementations."""
        # Act - test services are automatically injected
        response = self.client.get("/endpoint")
        
        # Assert
        assert response.status_code == 200
        # Test services provide predictable responses
```

### **Docker Test Template**

```python
"""
Docker Tests for [Container Feature]

Tests the [feature] in containerized environments with dependency injection.
"""

import pytest
import requests

pytestmark = pytest.mark.docker

class TestDockerFeature:
    """Docker-based tests with dependency injection."""

    def test_container_feature(self):
        """Test feature in Docker environment with test services."""
        # Container automatically uses APP_ENV=test
        response = requests.get("http://app:8080/endpoint")
        assert response.status_code == 200
```

## 🎯 **Best Practices**

### **Dependency Injection Testing**
1. **Use application factory** - `create_app(environment="test")`
2. **Let DI handle mocks** - Don't manually configure test services
3. **Test real workflows** - Same code paths as production
4. **Validate service injection** - Ensure correct implementations are used

### **Test Organization**
1. **One test class per component** - Clear organization
2. **Descriptive test names** - `test_component_action_expected_result`
3. **Arrange-Act-Assert** - Clear test structure
4. **Independent tests** - No test dependencies

### **Environment Configuration**
1. **Use APP_ENV=test** - Primary environment variable
2. **Let auto-detection work** - pytest automatically detected
3. **Verify injection** - Check that test services are used

---

This testing guide provides comprehensive coverage of the **TelegramGroupie** dependency injection testing strategy. The clean architecture ensures fast development cycles while maintaining confidence that tests validate the exact same code that runs in production.

## 🐳 **Enhanced Docker Testing with Dependency Injection**

### **Docker Test Environment**

Docker tests use the same dependency injection system as unit tests:

```yaml
# docker-compose.test.yml
services:
  app:
    environment:
      - APP_ENV=test  # Triggers test service injection
    # Application automatically uses TestServiceContainer
```

### **Service Injection in Containers**

The containerized application automatically detects the test environment and injects appropriate services:

1. **TestDatabaseClient**: Provides in-memory storage
2. **TestEncryptionService**: Uses deterministic mock encryption
3. **TestTelegramBot**: Logs instead of sending messages

### **Enhanced Docker Commands**

```bash
# Run Docker tests with dependency injection
make test-docker

# Start test environment for debugging
docker-compose -f docker-compose.test.yml up

# View logs to verify service injection
docker-compose -f docker-compose.test.yml logs app
```

## 🔄 **Dependency Injection Validation**

### **Verifying Service Injection**

```bash
# Test that correct services are injected
python -c "
from main import create_app
app = create_app(environment='test')
with app.app_context():
    from flask import current_app
    container = current_app.config['service_container']
    print(f'Database: {type(container.get_database_client()).__name__}')
    print(f'Encryption: {type(container.get_encryption_service()).__name__}')
"
```

### **Environment Detection Testing**

```bash
# Test automatic environment detection
APP_ENV=test python -c "
from service_container import create_service_container
container = create_service_container()
print(f'Auto-detected: {type(container).__name__}')
"

# Test pytest detection
python -m pytest --collect-only tests/unit/test_main.py
```
