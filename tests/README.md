# Testing Guide

This document explains the streamlined testing approach for TelegramGroupie.

## Test Structure

```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── test_encryption.py   # Encryption service tests
│   ├── test_main.py         # Main application tests
│   └── test_message_retrieval.py  # Message handling tests
├── docker/                  # Lightweight Docker integration tests
│   └── test_integration_docker.py  # Core functionality in Docker
└── README.md               # This file
```

## Test Types

### 1. Unit Tests (`tests/unit/`)
- **Fast**: Run in milliseconds
- **Isolated**: Use mocks, no external dependencies
- **Comprehensive**: Cover core business logic
- **Always run**: Part of every CI pipeline

### 2. Docker Integration Tests (`tests/docker/`)
- **Realistic**: Test in containerized environment
- **Lightweight**: Focus on essential functionality only
- **Reliable**: Fixed Firestore emulator with Java runtime
- **CI-ready**: Run in GitHub Actions
- **Smart cleanup**: Automatic container management

## Running Tests

### Quick Start
```bash
# Run unit tests only (fast, default)
./scripts/run-tests.sh

# Run all tests including Docker (with cleanup)
./scripts/run-tests.sh --docker

# Interactive mode (asks before Docker tests)
./scripts/run-tests.sh --interactive

# Keep containers for debugging (no cleanup)
./scripts/run-tests.sh --docker --no-cleanup

# Show help
./scripts/run-tests.sh --help
```

### Docker Test Cleanup Behavior

The script intelligently manages Docker containers:

**✅ Normal successful run** (`--docker`):
1. **Pre-test cleanup**: Removes any existing containers
2. **Runs tests**: Builds and executes Docker tests
3. **Post-test cleanup**: Removes containers after success

**❌ Failed test run** (`--docker`):
1. **Pre-test cleanup**: Removes any existing containers
2. **Runs tests**: Builds and executes Docker tests
3. **Preserves containers**: Leaves containers running for debugging

**🐛 Debugging mode** (`--docker --no-cleanup`):
1. **No cleanup**: Skips all cleanup operations
2. **Preserves everything**: Containers remain for inspection

### Debugging Failed Tests

When Docker tests fail, containers are preserved automatically:

```bash
# Inspect application logs
docker compose -f docker-compose.test.yml logs app

# Inspect Firestore emulator logs
docker compose -f docker-compose.test.yml logs firestore-emulator

# Get a shell in the app container
docker compose -f docker-compose.test.yml exec app bash

# Clean up when done debugging
docker compose -f docker-compose.test.yml down -v
```

### Manual Commands
```bash
# Unit tests only (fast)
python -m pytest tests/unit/ -v

# Docker tests only (manual)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# All tests with coverage
python -m pytest tests/unit/ --cov=. --cov-report=term-missing

# Clean up Docker manually
docker compose -f docker-compose.test.yml down -v --remove-orphans
```

## What Changed

### ✅ Improvements Made
- **Removed redundant integration tests** that duplicated Docker functionality
- **Fixed Docker setup** with proper Java runtime for Firestore emulator
- **Streamlined GitHub workflow** to focus on essential testing
- **Simplified test configuration** with clear pytest markers
- **Added Java runtime** to Firestore emulator (fixes previous failures)
- **Used Gunicorn** instead of Flask dev server for reliable container testing
- **Created non-interactive test script** with command line options
- **Added intelligent cleanup** with debugging preservation
- **Smart container management** prevents conflicts between runs

### ❌ What Was Removed
- Heavy `tests/integration/` directory with complex threading and mocking
- Redundant Docker test workflows
- Over-complicated CI conditionals
- Duplicate test cases between integration and Docker tests

## CI/CD Pipeline

The GitHub Actions workflow now runs:

1. **Unit Tests** - Fast feedback on core functionality
2. **Docker Tests** - Verify containerized deployment works (with cleanup)
3. **Coverage Report** - Ensure adequate test coverage

All tests must pass for CI to succeed.

## Development Workflow

1. **Write unit tests first** for new features
2. **Run unit tests frequently** during development (`./scripts/run-tests.sh`)
3. **Run Docker tests** before pushing (`./scripts/run-tests.sh --docker`)
4. **Debug failed tests** using preserved containers
5. **CI automatically runs all tests** on pull requests

## Test Markers

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.docker` - Docker integration tests

## Configuration

Tests are configured in `pyproject.toml`:
- Async support enabled
- Clear test markers defined
- Streamlined options for reliability

## Common Scenarios

### Development Testing
```bash
# Quick feedback during development
./scripts/run-tests.sh

# Full testing before commit
./scripts/run-tests.sh --docker
```

### Debugging Issues
```bash
# Test failed? Keep containers for inspection
./scripts/run-tests.sh --docker --no-cleanup

# Inspect what went wrong
docker compose -f docker-compose.test.yml logs app

# Clean up when done
docker compose -f docker-compose.test.yml down -v
```

### CI/CD Integration
```bash
# What CI runs (automatically)
./scripts/run-tests.sh --docker  # With automatic cleanup
```

---

**Need help?** Run `./scripts/run-tests.sh --help` for usage options! 