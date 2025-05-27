# Local Development Setup Guide

## Overview
This guide ensures your local development environment matches GitHub CI, using the dependency injection architecture for consistent testing across all environments.

## 🚨 Critical Rule: Never Push Without Local Validation
**Always run all checks locally before pushing to GitHub. If CI fails but local doesn't, your environment is misconfigured.**

## Prerequisites
- Python 3.11+
- Docker Desktop
- Git

## 1. Initial Setup

### Clone and Navigate
```bash
git clone git@github.com:sulitskii/TelegramGroupie.git
cd TelegramGroupie
```

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements-dev.txt
```

## 2. Pre-Push Validation Checklist

### ✅ Static Analysis (Ruff)
```bash
# Check for issues
ruff check . --output-format=github

# Auto-fix what can be fixed
ruff check . --fix

# Verify all issues are resolved
ruff check .
```

### ✅ Unit Tests with Dependency Injection
```bash
# Run unit tests (automatically detects test environment)
python -m pytest tests/unit/ -v

# Explicitly set test environment
APP_ENV=test python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ --cov=. --cov-report=html
```

### ✅ Docker Integration Tests
```bash
# Full Docker tests with dependency injection (matches GitHub CI)
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Fast tests with injected mock services (for development)
docker-compose -f docker-compose.fast-test.yml up --build --abort-on-container-exit
```

### ✅ Security & Quality
```bash
# Security scan
bandit -r . -f json -o bandit-report.json || echo "Review security issues"

# Additional quality checks (optional)
mypy .
```

## 3. Local Environment Configuration

### Virtual Environment Must Be Active
Always ensure your virtual environment is activated:
```bash
echo $VIRTUAL_ENV  # Should show your venv path
which python       # Should point to venv/bin/python
which ruff         # Should point to venv/bin/ruff
```

### Environment Variables for Testing
Create `.env.local` for local testing:
```bash
# Dependency injection environment
APP_ENV=test
GCP_PROJECT_ID=test-project
WEBHOOK_SECRET=test_webhook_secret_123
TELEGRAM_TOKEN=test_token_123

# Alternative (legacy support)
FLASK_ENV=testing
```

### Manual Application Testing
```bash
# Start application with test services
APP_ENV=test python main.py

# Or with Flask development server
APP_ENV=test flask run --debug

# Test endpoints
curl http://localhost:8080/healthz
curl http://localhost:8080/messages
```

## 4. Dependency Injection Development

### Understanding Service Injection

The application automatically detects your environment and injects appropriate services:

```python
# Automatic detection during development
from main import create_app

# Test environment (uses mock services)
app = create_app(environment="test")

# Production environment (uses real GCP services)  
app = create_app(environment="production")
```

### Verifying Service Injection

```bash
# Verify test services are injected
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

Expected output:
```
Database: TestDatabaseClient
Encryption: TestEncryptionService
```

## 5. CI Synchronization

### Docker Compose Files
- `docker-compose.test.yml` - Used by GitHub CI (comprehensive testing with APP_ENV=test)
- `docker-compose.fast-test.yml` - For fast local development (uses injected mocks)

### GitHub CI Workflows Match Local Commands
- **Ruff**: `ruff check . --output-format=github`
- **Tests**: `pytest tests/unit/ -v`
- **Docker**: `docker-compose -f docker-compose.test.yml up --build`

### Environment Variables Consistency
- **Local Development**: `APP_ENV=test`
- **Docker Tests**: `APP_ENV=test` (in docker-compose.test.yml)
- **GitHub CI**: Automatically detected by pytest

## 6. Common Issues & Solutions

### Issue: "ruff: command not found"
**Solution**: Virtual environment not activated or dev dependencies not installed
```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Issue: Tests using production services instead of mocks
**Solution**: Environment not properly detected
```bash
# Verify environment detection
APP_ENV=test python -c "
from service_container import create_service_container
container = create_service_container()
print(f'Container type: {type(container).__name__}')
"
# Should output: TestServiceContainer
```

### Issue: Docker tests fail with service connection errors
**Solution**: Ensure APP_ENV=test is set in docker-compose.test.yml
```yaml
environment:
  - APP_ENV=test  # Use injected test services
```

### Issue: Static analysis passes locally but fails in CI
**Solution**: Different Ruff version or configuration
```bash
# Check versions match
ruff --version
# Should match version in requirements-dev.txt
```

## 7. Development Workflow

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Develop with continuous validation**
   ```bash
   # After each significant change
   ruff check . --fix
   python -m pytest tests/unit/
   ```

4. **Test locally with dependency injection**
   ```bash
   # Start local server with test services
   APP_ENV=test python main.py
   # Test your changes
   ```

5. **Pre-push full validation**
   ```bash
   # Run ALL checks
   ruff check .
   python -m pytest tests/unit/ -v
   docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
   ```

6. **Only push if ALL checks pass**
   ```bash
   git add -A
   git commit -m "Your commit message"
   git push origin feature/your-feature-name
   ```

## 8. Troubleshooting

### Reset Development Environment
If your environment gets corrupted:
```bash
# Remove virtual environment
rm -rf venv

# Remove Docker containers and images
docker-compose -f docker-compose.test.yml down -v
docker system prune -a

# Start fresh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Debug Service Injection Issues
```bash
# Test environment detection
APP_ENV=test python -c "
from main import create_app
app = create_app()
print('Application created successfully with test services')
"

# Test specific service injection
python -c "
from implementations.test import TestDatabaseClient
from implementations.production import ProductionDatabaseClient
print('Import test successful')
"
```

### Debug CI Failures
If CI fails but local passes:
1. Check GitHub Actions logs for exact error
2. Ensure exact same commands run locally
3. Verify environment variables match (APP_ENV=test)
4. Check Docker setup and container logs

## 9. IDE Integration

### VS Code Settings
Add to `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.envFile": "${workspaceFolder}/.env.local"
}
```

### Environment Variables in IDE
Create `.env.local` for IDE integration:
```bash
APP_ENV=test
GCP_PROJECT_ID=test-project
WEBHOOK_SECRET=test_webhook_secret_123
TELEGRAM_TOKEN=test_token_123
```

## 10. Advanced Development

### Testing Both Environments Locally

```bash
# Test with mock services (fast)
APP_ENV=test python main.py

# Test with real services (requires GCP credentials)
unset APP_ENV
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
python main.py
```

### Custom Service Implementations

For advanced development, you can create custom service implementations:

```python
# Custom development service container
from service_container import ServiceContainer
from implementations.test import TestEncryptionService
from implementations.production import ProductionDatabaseClient

class DevServiceContainer(ServiceContainer):
    def get_database_client(self):
        return ProductionDatabaseClient()  # Real database
    
    def get_encryption_service(self):
        return TestEncryptionService()  # Mock encryption
```

## 11. Performance Optimization

### Fast Development Cycle
```bash
# Quick syntax and unit test check
ruff check . && python -m pytest tests/unit/ -x

# Skip slow tests during development
python -m pytest tests/unit/ -m "not slow"

# Run specific test files
python -m pytest tests/unit/test_main.py -v
```

---

## Summary
Following this guide ensures:
- ✅ Local environment matches CI exactly with dependency injection
- ✅ Fast development cycle with injected test services
- ✅ Issues are caught before pushing
- ✅ No CI surprises or failures
- ✅ Consistent development experience across all environments

**Remember: The dependency injection architecture ensures your tests validate the same code that runs in production, just with different service implementations injected!** 