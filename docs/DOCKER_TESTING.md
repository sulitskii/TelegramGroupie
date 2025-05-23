# Docker-Based Integration Testing Guide

This guide explains how to set up and run integration tests using Docker containers for the telegram2whatsapp project.

## 🎯 **Overview**

Docker-based integration testing provides:
- **Isolated Environment**: Tests run in clean, reproducible containers
- **Service Dependencies**: Automatic setup of Firestore emulator, Redis, PostgreSQL
- **Network Testing**: Tests real service-to-service communication
- **CI/CD Ready**: Easy integration with automated pipelines
- **Consistent Results**: Same environment across different machines

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

### 1. Run All Integration Tests
```bash
# Using Make (recommended)
make docker-test

# Or directly
./scripts/run-docker-tests.sh
```

### 2. Run Tests with Clean Environment
```bash
# Clean up any previous containers and run fresh tests
make docker-test-clean

# Or directly
./scripts/run-docker-tests.sh --clean
```

### 3. Debug Mode (No Cleanup)
```bash
# Keep containers running after tests for debugging
make docker-test-debug

# Or directly
./scripts/run-docker-tests.sh --no-cleanup
```

## 📋 **Available Commands**

### Make Commands
```bash
make docker-test           # Run integration tests in Docker
make docker-test-clean     # Run tests with cleanup
make docker-test-debug     # Run tests without cleanup (for debugging)
make docker-test-up        # Start test environment only
make docker-test-down      # Stop test environment
make docker-test-logs      # View test logs
```

### Direct Script Usage
```bash
./scripts/run-docker-tests.sh [OPTIONS]

Options:
  -h, --help     Show help message
  -c, --clean    Clean up Docker resources before running
  -v, --verbose  Verbose output
  --no-cleanup   Don't cleanup after tests (for debugging)
```

## 🏗️ **Architecture**

### Docker Services

The Docker test environment includes:

1. **Application Container** (`app`)
   - Runs the main Flask application
   - Uses Python 3.11
   - Connected to all dependency services

2. **Test Runner Container** (`test-runner`)
   - Specialized container for running tests
   - Includes all testing dependencies
   - Generates reports and coverage

3. **Firestore Emulator** (`firestore-emulator`)
   - Google Cloud Firestore emulator
   - Provides local database for testing
   - No authentication required

4. **Redis** (`redis`)
   - For session storage and caching
   - Optional service for extended testing

5. **PostgreSQL** (`test-db`)
   - Additional database for testing
   - Optional service

### Network Configuration

All services run in an isolated Docker network (`test-network`) which:
- Allows services to communicate using service names
- Provides network isolation from host
- Enables testing of service discovery

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

### Environment Variables

The Docker test environment uses these environment variables:

```bash
# Application Configuration
FLASK_ENV=testing
FLASK_DEBUG=False
PORT=8080
TESTING=true
INTEGRATION_TEST_MODE=true

# Database Configuration
FIRESTORE_EMULATOR_HOST=firestore-emulator:8081
GCP_PROJECT_ID=test-project

# Security Configuration
WEBHOOK_SECRET=test_webhook_secret_123

# Test Configuration
APP_URL=http://app:8080
```

### Customizing Configuration

To customize the test environment:

1. **Modify `docker-compose.test.yml`**:
   ```yaml
   services:
     app:
       environment:
         - CUSTOM_VAR=value
   ```

2. **Update test configuration**:
   ```python
   # In tests/test_integration_docker.py
   APP_URL = os.environ.get('APP_URL', 'http://app:8080')
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

#### 2. Port Conflicts
```bash
# Check what's using port 8080
lsof -i :8080

# Kill processes using the port
sudo kill -9 $(lsof -t -i:8080)
```

#### 3. Container Build Failures
```bash
# Clean Docker cache
docker system prune -f

# Rebuild without cache
docker-compose -f docker-compose.test.yml build --no-cache
```

### Debugging Test Failures

1. **Keep containers running**:
   ```bash
   ./scripts/run-docker-tests.sh --no-cleanup
   ```

2. **Inspect running containers**:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   docker-compose -f docker-compose.test.yml logs app
   docker-compose -f docker-compose.test.yml logs test-runner
   ```

3. **Access container shell**:
   ```bash
   docker-compose -f docker-compose.test.yml exec app bash
   docker-compose -f docker-compose.test.yml exec test-runner bash
   ```

4. **Test specific endpoints**:
   ```bash
   # From within test-runner container
   curl http://app:8080/healthz
   python -c "import requests; print(requests.get('http://app:8080/healthz').json())"
   ```

### Log Analysis

```bash
# View all logs
make docker-test-logs

# View specific service logs
docker-compose -f docker-compose.test.yml logs -f app
docker-compose -f docker-compose.test.yml logs -f firestore-emulator

# Follow logs in real-time
docker-compose -f docker-compose.test.yml logs -f --tail=100
```

## 🚀 **CI/CD Integration**

### GitHub Actions

Add to `.github/workflows/docker-tests.yml`:

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
    
    - name: Run Docker Integration Tests
      run: |
        chmod +x scripts/run-docker-tests.sh
        ./scripts/run-docker-tests.sh --clean
    
    - name: Upload Test Results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: test-results/
```

### Other CI Systems

For other CI systems, use:
```bash
# Clean run for CI
./scripts/run-docker-tests.sh --clean --verbose

# Exit code indicates success/failure
echo $?  # 0 = success, non-zero = failure
```

## 🔒 **Security Considerations**

1. **No Real Credentials**: Tests use mock credentials only
2. **Isolated Network**: Containers run in isolated Docker network
3. **Temporary Data**: All data is cleaned up after tests
4. **No External Access**: Services don't expose ports to host by default

## 📈 **Performance Tips**

1. **Use Docker Layer Caching**:
   ```bash
   # Pre-build base images
   docker pull python:3.11-slim
   docker pull gcr.io/google.com/cloudsdktool/cloud-sdk:latest
   ```

2. **Parallel Testing**:
   ```bash
   # Run tests in parallel (if supported)
   pytest -n auto tests/test_integration_docker.py
   ```

3. **Resource Limits**:
   ```yaml
   # In docker-compose.test.yml
   services:
     app:
       deploy:
         resources:
           limits:
             memory: 512M
             cpus: '0.5'
   ```

## 📚 **Additional Resources**

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [pytest Documentation](https://docs.pytest.org/)
- [Google Cloud Firestore Emulator](https://cloud.google.com/firestore/docs/emulator)

## 🆘 **Support**

If you encounter issues:

1. Check the [Common Issues](#common-issues) section
2. Review container logs: `make docker-test-logs`
3. Run in debug mode: `make docker-test-debug`
4. Check Docker system status: `docker system df`
5. Clean Docker system: `docker system prune -f` 