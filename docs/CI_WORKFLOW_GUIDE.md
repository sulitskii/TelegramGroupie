# CI Workflow Guide: Achieving Green Pull Requests

## Project Context: TelegramGroupie Bot
- **Enterprise bot** deployed on GCP Cloud Run
- **Tech Stack**: Flask, Firestore, KMS, Telegram Bot API, Docker
- **Bot Token**: `7910877027:AAH-oPzr3py5UNvWmm_4A3KK3nj5aVx5mqk`
- **Webhook Secret**: `6a8cc29ae4f44959fe4f504d3f08a94f8e7091ce243c9ae9be7322b2cfd3b686`
- **Deployment URL**: `https://telegramgroupie-862748873351.us-central1.run.app`

## 🚀 Efficient Green PR Workflow

### Step 1: Always Create Feature Branches
```bash
# IMPORTANT: Always rebase to latest main before creating feature branches
git checkout main
git stash  # if you have uncommitted changes
git pull origin main

# ALWAYS create a new branch for every feature/fix
git checkout -b feature/your-feature-name
git push -u origin feature/your-feature-name
```

### Step 2: Test Locally Before Pushing
```bash
# Run unit tests (fast)
python -m pytest tests/unit/ -v

# Option A: Fast integration tests with mocks (recommended for development)
docker-compose -f docker-compose.fast-test.yml up --build --abort-on-container-exit

# Option B: Comprehensive integration tests with Firestore emulator (for thorough testing)
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### Step 3: Single-Shot PR Creation & Status Check
```bash
# Commit and push changes
git add -A
git commit -m "descriptive commit message"
git push

# Create PR with descriptive title and body
gh pr create --title "Feature: Your Feature Name" \
  --body "Description of changes and testing completed" \
  --base main --head feature/your-feature-name

# Get PR number and check status in one go
PR_NUM=$(gh pr list --head feature/your-feature-name --json number --jq '.[0].number')
gh pr checks $PR_NUM --watch
```

### Step 4: Common Integration Test Fixes

#### 🔧 Testing Mode Configuration
The app uses `TESTING=true` environment variable to switch to mock services:

**In `docker-compose.test.yml`**:
```yaml
environment:
  - TESTING=true
  - GCP_PROJECT_ID=test-project
  - WEBHOOK_SECRET=test_webhook_secret_123
  - TELEGRAM_TOKEN=test_token_123
```

**In `main.py`**:
```python
TESTING_MODE = os.environ.get("TESTING", "false").lower() == "true"

if TESTING_MODE:
    # Use MockFirestoreClient and MockMessageEncryption
else:
    # Use real GCP services
```

#### 🎯 Integration Test Patterns
Tests should match actual API endpoints:
- `GET /healthz` - Health check
- `POST /webhook/{secret}` - Webhook endpoint
- Handle 404, 405, 400 error cases appropriately

### Step 5: CI Pipeline Structure
- **Unit Tests**: `python -m pytest tests/unit/` (fast feedback)
- **Docker Integration**: `docker-compose -f docker-compose.test.yml up --build`
- **Static Analysis**: bandit, flake8 (via separate workflow)

## 🎯 Key Success Patterns

### 1. Environment Isolation
- **Testing**: Mock all GCP services (Firestore, KMS)
- **Production**: Real GCP service clients
- **Never**: Mix testing and production configurations

### 2. Docker Test Requirements
- Must include all required environment variables
- App must be ready on port 8080 within timeout
- Use `/healthz` endpoint for readiness checks

### 3. Async/Sync Handling
- **Critical**: Proper async handling in Flask webhook
```python
# Correct pattern for Telegram Bot in Flask
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(telegram_bot.send_message(...))
finally:
    loop.close()
```

### 4. Test Endpoint Alignment
- Integration tests must match actual Flask routes
- Remove tests for non-existent endpoints
- Update expected status codes based on actual behavior

## 🚫 Anti-Patterns to Avoid

1. **DON'T**: Push without local testing
2. **DON'T**: Work directly on main branch
3. **DON'T**: Assume CI status without checking
4. **DON'T**: Include large binaries (`.terraform/`) in commits
5. **DON'T**: Test non-existent API endpoints

## 📋 Quick Checklist for Green PRs

- [ ] Feature branch created
- [ ] Local unit tests pass
- [ ] Local Docker integration tests pass
- [ ] Environment variables correctly configured
- [ ] No large binaries in commit
- [ ] Descriptive PR title/description
- [ ] CI status verified via `gh pr checks`

## 🔍 Debugging Failed Tests

### Unit Test Failures
```bash
python -m pytest tests/unit/ -v --tb=short
```

### Docker Integration Failures
```bash
# Check logs for specific failure
docker-compose -f docker-compose.test.yml logs app

# Common issues:
# - Missing environment variables
# - GCP service initialization in testing mode
# - Port binding conflicts
```

### GitHub Actions Failures
```bash
# Check specific workflow run
gh run view --repo sulitskii/TelegramGroupie

# Re-run failed jobs
gh run rerun --repo sulitskii/TelegramGroupie
```

## 📚 Repository Information
- **Owner**: sulitskii
- **Repo**: TelegramGroupie
- **Main Workflows**: `python-app.yml`, `static-analysis.yml`
- **Test Structure**: `tests/unit/`, `tests/docker/`

---
*This guide captures lessons learned from multiple iterations of CI fixes and PR creation.* 