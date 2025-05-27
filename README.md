# Telegram Bot Framework 🚀

A production-ready Telegram bot framework with enterprise-grade features including encrypted message storage, dependency injection architecture, and comprehensive testing.

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TELEGRAM BOT FRAMEWORK                           │
└─────────────────────────────────────────────────────────────────────────────┘

ENVIRONMENTS
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│     PRODUCTION      │    │      STAGING        │    │      TESTING        │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ ProductionService   │    │ ProductionService   │    │   TestService       │
│ Container           │    │ Container           │    │   Container         │
│                     │    │                     │    │                     │
│ • Real Firestore    │    │ • Real Firestore    │    │ • Mock Firestore    │
│ • Real KMS          │    │ • Real KMS          │    │ • Mock KMS          │
│ • Real Telegram     │    │ • Real Telegram     │    │ • Mock Telegram     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘

APPLICATION LOGIC (IDENTICAL ACROSS ALL ENVIRONMENTS)
┌─────────────────────────────────────────────────────────────────────────────┐
│  main.py → service_container.py → interfaces.py → implementations/         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## ✨ **Key Features**

- 🔐 **End-to-end encryption** with Google Cloud KMS
- 🏗️ **Dependency injection** architecture for clean testing
- 🐳 **Docker containerization** with multi-stage builds
- 🧪 **Comprehensive testing** (unit, integration, Docker)
- 📊 **Production monitoring** and health checks
- 🚀 **Cloud-native deployment** ready for Google Cloud Run
- 🔄 **CI/CD pipeline** with GitHub Actions
- 📝 **Enterprise documentation** and security practices

## 🚀 **Quick Start**

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized testing)
- Google Cloud CLI (for production deployment)

### 1. Clone and Setup

```bash
git clone <your-repository-url>
cd <your-project-directory>
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r infrastructure/requirements/requirements.txt
```

### 2. Configuration

Copy the environment template and configure for your deployment:

```bash
cp configuration/environment.env.template configuration/production.env
# Edit configuration/production.env with your values
```

Required environment variables:
```bash
GCP_PROJECT_ID=your-project-id
TELEGRAM_TOKEN=your-bot-token
WEBHOOK_SECRET=your-webhook-secret
KMS_LOCATION=global
KMS_KEY_RING=your-key-ring-name
KMS_KEY_ID=your-key-id
```

### 3. Local Development

```bash
# Run with test environment (uses mocks)
APP_ENV=test python main.py

# Test the API
curl http://localhost:8080/healthz
curl http://localhost:8080/messages
```

## 🧪 **Testing**

### Quick Test Commands

```bash
# Unit tests (fast)
make test-unit

# Docker tests (comprehensive)
make test-docker

# All tests with coverage
make test-coverage
```

### Manual Testing

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Docker integration tests
docker-compose -f infrastructure/docker/docker-compose.test.yml up --build --abort-on-container-exit
```

## 🐳 **Docker Deployment**

### Build and Run

```bash
# Build the image
docker build -f infrastructure/docker/Dockerfile -t telegram-bot:latest .

# Run locally
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=your-project \
  -e TELEGRAM_TOKEN=your-token \
  -e WEBHOOK_SECRET=your-secret \
  telegram-bot:latest
```

### Docker Compose

```bash
# Test environment
docker-compose -f infrastructure/docker/docker-compose.test.yml up

# Fast test environment
docker-compose -f infrastructure/docker/docker-compose.fast-test.yml up
```

## ☁️ **Cloud Deployment**

### Google Cloud Run

1. **Setup GCP Project:**
```bash
./devops/scripts/setup-gcp-project.sh -p your-project-id -e production
```

2. **Deploy:**
```bash
./devops/scripts/deploy.sh -p your-project-id -t your-telegram-token -s your-webhook-secret
```

3. **Set Webhook:**
```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
     -d "url=https://your-service-url/webhook/${WEBHOOK_SECRET}"
```

## 📁 **Project Structure**

```
📦 telegram-bot-framework/
├── 📄 main.py              # Flask application (entry point)
├── 📄 interfaces.py        # Core interfaces and contracts
├── 📄 encryption.py        # Encryption utilities
├── 📄 Makefile             # Build automation and development commands
├── 📄 README.md            # Project overview and quick start
├── 📄 SECURITY.md          # Security policies and reporting
├── 📄 .gitignore           # Git ignore patterns
├── 📁 src/
│   ├── 📁 core/
│   │   └── 📄 service_container.py    # Dependency injection containers
│   └── 📁 implementations/
│       ├── 📄 production.py           # Production implementations
│       └── 📄 test.py                 # Test/mock implementations
├── 📁 infrastructure/
│   ├── 📁 docker/                     # Docker configurations
│   ├── 📁 requirements/               # Python dependencies
│   └── 📄 build.sh                    # Build and deployment script
├── 📁 devops/
│   └── 📁 scripts/                    # Deployment and automation scripts
├── 📁 configuration/
│   ├── 📄 environment.env.template    # Environment configuration template
│   └── 📄 *.yaml                      # Configuration files
├── 📁 tests/
│   ├── 📁 unit/                       # Unit tests
│   └── 📁 docker/                     # Docker integration tests
└── 📁 docs/                           # Documentation
```

## 🔧 **Development Commands**

```bash
# Development
make dev-setup          # Set up development environment
make dev-run            # Run in development mode
make dev-test           # Run tests in development

# Testing
make test-unit          # Run unit tests
make test-docker        # Run Docker tests
make test-coverage      # Run tests with coverage

# Building
make build              # Build Docker image
make build-test         # Build test image

# Deployment
make deploy-staging     # Deploy to staging
make deploy-production  # Deploy to production

# Utilities
make clean              # Clean up build artifacts
make lint               # Run code linting
make format             # Format code
```

## 🔐 **Security Features**

- **Encrypted Storage**: All messages encrypted with Google Cloud KMS
- **Secret Management**: Environment-based secret configuration
- **Input Validation**: Comprehensive request validation
- **Security Headers**: Production-ready security headers
- **Audit Logging**: Complete audit trail for all operations

## 📊 **Monitoring & Observability**

- **Health Checks**: Built-in health monitoring endpoints
- **Structured Logging**: JSON-formatted logs for analysis
- **Metrics**: Application and infrastructure metrics
- **Error Tracking**: Comprehensive error reporting
- **Performance Monitoring**: Request timing and throughput tracking

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test-all`
5. Submit a pull request

## 📚 **Documentation**

- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Testing Guide](docs/TESTING.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [Security Policies](SECURITY.md)
- [Branch Protection Setup](docs/BRANCH_PROTECTION_SETUP.md)

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 **Support**

For support and questions:
- Check the documentation in the `docs/` directory
- Review the troubleshooting guides
- Open an issue for bugs or feature requests

---

**Built with ❤️ for production-ready Telegram bot development**
