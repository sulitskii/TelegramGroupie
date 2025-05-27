# Docker Testing Guide

This guide explains how to set up and run integration tests using Docker containers for the TelegramGroupie project with dependency injection architecture.

## 🎯 **Overview**

Docker-based integration testing with dependency injection provides:
- **Isolated Environment**: Tests run in clean, reproducible containers
- **Service Injection**: Automatic injection of test implementations via APP_ENV=test
- **Network Testing**: Tests realistic container-to-container communication
- **CI/CD Ready**: Easy integration with automated pipelines
- **Consistent Results**: Same environment across different machines with injected mocks

## 🛠️ **Prerequisites**

### Install Docker Desktop

#### macOS:
```bash
# Install via Homebrew
brew install --cask docker

# Or download from: https://docs.docker.com/desktop/mac/install/
```

#### Linux (Ubuntu/Debian):
```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Windows:
- Download Docker Desktop from: https://docs.docker.com/desktop/windows/install/
- Follow the installation wizard

### Verify Installation:
```bash
docker --version
docker-compose --version
docker info
```

## 🚀 **Quick Start**

### 1. Run All Integration Tests with Dependency Injection
```bash
# Using Make (recommended)
make test-docker

# Or directly with docker-compose
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### 2. Run Fast Tests with Injected Mocks
```bash
# Fast test environment with mock services
docker-compose -f docker-compose.fast-test.yml up --build --abort-on-container-exit
```

### 3. Debug Mode (Keep Containers Running)
```bash
# Start test environment for debugging
docker-compose -f docker-compose.test.yml up --build

# In another terminal, check logs
docker-compose -f docker-compose.test.yml logs app

# Stop when done
docker-compose -f docker-compose.test.yml down
```

## 📋 **Available Commands**

### Make Commands
```bash
make test-docker           # Run integration tests in Docker with dependency injection
make test-unit            # Run unit tests with injected test services
make test-all             # Run all tests (unit + docker)
```

### Direct Docker Commands
```bash
# Test environment with comprehensive service injection
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Fast test environment with lightweight mocks
docker-compose -f docker-compose.fast-test.yml up --build --abort-on-container-exit

# Start environment for debugging
docker-compose -f docker-compose.test.yml up --build

# View logs
docker-compose -f docker-compose.test.yml logs app

# Stop environment
docker-compose -f docker-compose.test.yml down
```

## 🏗️ **Dependency Injection Architecture**

### Container Service Injection

The Docker test environment automatically injects test services via environment variables:

1. **Application Container** (`app`)
   - Environment: `APP_ENV=test`
   - Automatically uses TestServiceContainer
   - Injects: TestDatabaseClient, TestEncryptionService, TestTelegramBot

2. **Test Runner Container** (`test-runner`)
   - Makes HTTP requests to application container
   - Tests realistic API workflows
   - Validates responses from injected test services

### Service Implementations in Containers

```
DOCKER CONTAINER ENVIRONMENT
┌─────────────────────────────────────────────────────────────────┐
│ APP_ENV=test → TestServiceContainer                             │
│                                                                 │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│ │ TestDatabase    │  │ TestEncryption  │  │ TestTelegram    │ │
│ │ Client          │  │ Service         │  │ Bot             │ │
│ │ • Dict storage  │  │ • Base64 mock   │  │ • Log messages  │ │
│ │ • Fast startup  │  │ • Deterministic │  │ • No network    │ │
│ │ • No network    │  │ • Test-friendly │  │ • Offline mode  │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Network Configuration

All services run in an isolated Docker network (`test-network`) which:
- Allows container-to-container communication using service names
- Provides network isolation from host
- Enables testing of service discovery with injected implementations

## 📊 **Test Reports**

After running tests, reports are generated in the `./test-results/` directory:

```
test-results/
├── junit.xml              # JUnit XML report (CI/CD compatible)
├── report.html            # HTML test report
└── coverage/              # Coverage report directory
    └── index.html         # Coverage HTML report
```

### Viewing Reports

```bash
# Open HTML test report
open test-results/report.html

# Open coverage report
open test-results/coverage/index.html

# View test summary
cat test-results/junit.xml
```

## 🔧 **Configuration**

### Environment Variables for Dependency Injection

The Docker test environment uses these environment variables:

```bash
# Dependency Injection Configuration
APP_ENV=test                        # Triggers test service injection
FLASK_ENV=testing                   # Flask testing mode
FLASK_DEBUG=False                   # Disable debug in container
PORT=8080                          # Application port

# Test Service Configuration
GCP_PROJECT_ID=test-project        # Mock project ID
WEBHOOK_SECRET=test_webhook_secret_123
TELEGRAM_TOKEN=test_token_123      # Mock token

# Test Environment
INTEGRATION_TEST_MODE=true
APP_URL=http://app:8080           # Container-to-container URL
```

### Docker Compose Configuration

#### Comprehensive Test Environment (`docker-compose.test.yml`)
```yaml
services:
  app:
    build: .
    environment:
      - APP_ENV=test  # Triggers TestServiceContainer injection
      - GCP_PROJECT_ID=test-project
      - WEBHOOK_SECRET=test_webhook_secret_123
    # Application automatically injects test implementations
```

#### Fast Test Environment (`docker-compose.fast-test.yml`)
```yaml
services:
  app:
    build: .
    environment:
      - APP_ENV=test  # Uses lightweight test implementations
    # Optimized for speed with minimal overhead
```

## 🐛 **Debugging**

### Common Issues

#### 1. Docker Not Running
```bash
# Check Docker status
docker info

# Start Docker (macOS)
open -a Docker

# Start Docker (Linux)
sudo systemctl start docker
```

#### 2. Service Injection Issues
```bash
# Verify test services are injected in container
docker-compose -f docker-compose.test.yml exec app python -c "
from flask import current_app
container = current_app.config['service_container']
print(f'Container type: {type(container).__name__}')
print(f'Database: {type(container.get_database_client()).__name__}')
"
```

#### 3. Port Conflicts
```bash
# Check what's using port 8080
lsof -i :8080

# Kill processes using the port
sudo kill -9 $(lsof -t -i:8080)
```

#### 4. Container Build Failures
```bash
# Clean Docker cache
docker system prune -f

# Rebuild without cache
docker-compose -f docker-compose.test.yml build --no-cache
```

### Debugging Test Failures

1. **Inspect running containers**:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   docker-compose -f docker-compose.test.yml logs app
   docker-compose -f docker-compose.test.yml logs test-runner
   ```

2. **Access container shell**:
   ```bash
   docker-compose -f docker-compose.test.yml exec app bash
   ```

3. **Test service injection manually**:
   ```bash
   # From within app container
   python -c "
   from main import create_app
   app = create_app(environment='test')
   print('Test services injected successfully')
   "
   ```

4. **Test endpoints directly**:
   ```bash
   # From within test-runner container
   curl http://app:8080/healthz
   python -c "import requests; print(requests.get('http://app:8080/healthz').json())"
   ```

### Log Analysis

```bash
# View all logs
docker-compose -f docker-compose.test.yml logs

# View specific service logs
docker-compose -f docker-compose.test.yml logs -f app

# Follow logs in real-time
docker-compose -f docker-compose.test.yml logs -f --tail=100
```

## 🚀 **CI/CD Integration**

### GitHub Actions

The Docker tests integrate seamlessly with CI/CD:

```yaml
name: Docker Integration Tests

on: [push, pull_request]

jobs:
  docker-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Run Docker Integration Tests with Dependency Injection
      run: |
        docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

    - name: Upload Test Results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: test-results/
```

### Benefits of Dependency Injection in CI

✅ **Fast Execution**: Mock services eliminate network latency
✅ **Reliable Results**: No external dependencies or flaky services
✅ **Identical Logic**: Tests validate same code that runs in production
✅ **Deterministic**: Consistent results across all CI runs

## 🔒 **Security Considerations**

1. **No Real Credentials**: Tests use injected mock services only
2. **Isolated Network**: Containers run in isolated Docker network
3. **Temporary Data**: All data is cleaned up after tests
4. **Mock Services**: No real GCP or Telegram API calls

## 📈 **Performance Tips**

1. **Use Docker Layer Caching**:
   ```bash
   # Pre-build base images
   docker pull python:3.11-slim
   ```

2. **Optimize Test Execution**:
   ```bash
   # Use fast test environment for development
   docker-compose -f docker-compose.fast-test.yml up --build
   ```

3. **Parallel Testing**:
   ```bash
   # Tests run in parallel within container
   pytest -n auto tests/docker/
   ```

## 📚 **Additional Resources**

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [pytest Documentation](https://docs.pytest.org/)
- [TelegramGroupie Testing Guide](TESTING.md)

## 🆘 **Support**

If you encounter issues:

1. Check the [Common Issues](#common-issues) section
2. Review container logs: `docker-compose -f docker-compose.test.yml logs`
3. Verify service injection: Check that APP_ENV=test is set
4. Test environment detection: Ensure TestServiceContainer is used
5. Clean Docker system: `docker system prune -f`

---

This Docker testing guide provides comprehensive coverage of containerized testing with the **TelegramGroupie** dependency injection architecture. The system ensures fast, reliable testing while validating the exact same application logic that runs in production.
