# Local Development Setup Guide

## Overview
This guide ensures your local development environment matches GitHub CI, allowing you to catch issues locally before pushing.

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

### ✅ Unit Tests
```bash
python -m pytest tests/unit/ -v
```

### ✅ Docker Integration Tests
```bash
# Full Docker tests (matches GitHub CI)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Fast mock tests (optional, for development)
docker compose -f docker-compose.fast-test.yml up --build --abort-on-container-exit
```

### ✅ Security & Quality
```bash
# Security scan
bandit -r . -f json -o bandit-report.json || echo "Review security issues"

# Additional quality checks (optional)
mypy .
pylint main.py
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
TESTING=true
GCP_PROJECT_ID=test-project
WEBHOOK_SECRET=test_webhook_secret_123
TELEGRAM_TOKEN=test_token_123
```

## 4. CI Synchronization

### Docker Compose Files
- `docker-compose.test.yml` - Used by GitHub CI (comprehensive)
- `docker-compose.fast-test.yml` - For fast local development

### GitHub CI Workflows Match Local Commands
- **Ruff**: `ruff check . --output-format=github`
- **Tests**: `pytest tests/unit/ -v`
- **Docker**: `docker compose -f docker-compose.test.yml up --build`

## 5. Common Issues & Solutions

### Issue: "ruff: command not found"
**Solution**: Virtual environment not activated or dev dependencies not installed
```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Issue: Docker tests fail with GCP credentials error
**Solution**: Ensure `TESTING=true` in docker-compose.test.yml
```yaml
environment:
  - TESTING=true  # Use mock services
```

### Issue: Static analysis passes locally but fails in CI
**Solution**: Different Ruff version or configuration
```bash
# Check versions match
ruff --version
# Should match version in requirements-dev.txt
```

## 6. Development Workflow

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

4. **Pre-push full validation**
   ```bash
   # Run ALL checks
   ruff check .
   python -m pytest tests/unit/ -v
   docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
   ```

5. **Only push if ALL checks pass**
   ```bash
   git add -A
   git commit -m "Your commit message"
   git push origin feature/your-feature-name
   ```

## 7. Troubleshooting

### Reset Development Environment
If your environment gets corrupted:
```bash
# Remove virtual environment
rm -rf venv

# Remove Docker containers and images
docker compose -f docker-compose.test.yml down -v
docker system prune -a

# Start fresh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Debug CI Failures
If CI fails but local passes:
1. Check GitHub Actions logs for exact error
2. Ensure exact same commands run locally
3. Verify environment variables match
4. Check file permissions and Docker setup

## 8. IDE Integration

### VS Code Settings
Add to `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

## 9. Git Hooks (Optional)

Set up pre-commit hooks:
```bash
pre-commit install
```

This will run checks automatically before each commit.

---

## Summary
Following this guide ensures:
- ✅ Local environment matches CI exactly
- ✅ Issues are caught before pushing
- ✅ No CI surprises or failures
- ✅ Consistent development experience

**Remember: If CI fails but local doesn't, fix your local environment, don't ignore the CI failure!** 