# TelegramGroupie Project Context

## 🏢 Project Overview
- **Name**: TelegramGroupie Enterprise Bot
- **Purpose**: Telegram bot that responds with message metadata
- **Deployment**: GCP Cloud Run
- **URL**: https://telegramgroupie-862748873351.us-central1.run.app

## 🔑 Credentials & Configuration
- **Bot Token**: `7910877027:AAH-oPzr3py5UNvWmm_4A3KK3nj5aVx5mqk`
- **Webhook Secret**: `6a8cc29ae4f44959fe4f504d3f08a94f8e7091ce243c9ae9be7322b2cfd3b686`
- **GCP Project**: telegramgroupie (inferred from deployment URL)

## 🛠 Tech Stack
- **Backend**: Flask (Python)
- **Database**: Firestore
- **Encryption**: Google Cloud KMS
- **Bot API**: python-telegram-bot (async)
- **Deployment**: Docker → Cloud Run
- **CI/CD**: GitHub Actions

## 📁 Repository Structure
```
telegram2whatsapp/
├── main.py                    # Main Flask application
├── mock_firestore.py         # Testing mock for Firestore
├── mock_encryption.py        # Testing mock for KMS
├── tests/
│   ├── unit/                 # Unit tests (pytest)
│   └── docker/               # Integration tests
├── .github/workflows/        # CI pipelines
├── docker-compose.test.yml   # Testing environment
└── docs/                     # Documentation
```

## 🎯 Bot Functionality
**Core Feature**: Responds to any message with format:
```
I received message from *username*, in the chat *chat_name*, message id #123
```

**Smart Features**:
- Handles users without usernames (uses first_name)
- Detects private vs group chats
- Encrypts/decrypts messages using KMS
- Stores chat metadata in Firestore

## 🧪 Testing Architecture
- **Testing Mode**: `TESTING=true` env var switches to mocks
- **Unit Tests**: 12 tests covering core functionality
- **Integration Tests**: 6 Docker tests for API endpoints
- **Local Testing**: `docker-compose -f docker-compose.test.yml up`

## 🔧 Common Issues & Solutions
1. **Async in Flask**: Use `asyncio.new_event_loop()` pattern
2. **GCP in Tests**: Always use mocks when `TESTING=true`
3. **Large Commits**: Exclude `.terraform/` directories
4. **Branch Strategy**: Always use feature branches

## 📊 CI/CD Status
- **Repository**: sulitskii/TelegramGroupie
- **Main Workflows**: `python-app.yml`, `static-analysis.yml`
- **Test Command**: `gh pr checks [PR_NUM] --watch`
- **Success Pattern**: All tests green → auto-deployable

## 🚀 Quick Commands
```bash
# Run local tests
python -m pytest tests/unit/ -v
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Create feature branch & PR
git checkout -b feature/feature-name
gh pr create --title "Feature: Name" --body "Description"

# Check CI status
gh pr checks $(gh pr list --head $(git branch --show-current) --json number --jq '.[0].number') --watch
```

---
*Last Updated: Based on successful CI fixes and green PR achievement* 