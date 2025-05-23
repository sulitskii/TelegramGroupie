# CI/CD Pipeline Documentation

## 🚀 **Pipeline Overview**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            COMPLETE CI/CD PIPELINE                         │
│                          From Code to Production                           │
└─────────────────────────────────────────────────────────────────────────────┘

GITHUB REPOSITORY
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│ │    Push     │   │    Pull     │   │  Scheduled  │   │   Release   │     │
│ │  to main    │   │   Request   │   │    Runs     │   │     Tag     │     │
│ └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘     │
│       │                 │                 │                 │             │
│       └─────────────────┼─────────────────┼─────────────────┘             │
│                         │                 │                               │
│                         ▼                 ▼                               │
│               ┌─────────────────────────────────────┐                     │
│               │       GITHUB ACTIONS                 │                     │
│               │      Workflow Triggered              │                     │
│               └─────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WORKFLOW STAGES                               │
└─────────────────────────────────────────────────────────────────────────────┘

STAGE 1: PREPARATION
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐
│    CHECKOUT     │───▶│    SETUP        │───▶│      CACHE                  │
│                 │    │                 │    │                             │
│ • Clone repo    │    │ • Python 3.11   │    │ • pip dependencies          │
│ • Get source    │    │ • pip install   │    │ • Docker layers             │
│ • Set refs      │    │ • venv create   │    │ • pytest cache              │
└─────────────────┘    └─────────────────┘    └─────────────────────────────┘

STAGE 2: CODE QUALITY
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐
│     LINT        │    │     FORMAT      │    │     SECURITY                │
│                 │    │                 │    │                             │
│ • flake8        │    │ • black         │    │ • bandit scan               │
│ • pylint        │    │ • isort         │    │ • safety check              │
│ • mypy          │    │ • autopep8      │    │ • dependency audit          │
└─────────────────┘    └─────────────────┘    └─────────────────────────────┘

STAGE 3: TESTING MATRIX
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐
│   UNIT TESTS    │    │  INTEGRATION    │    │    DOCKER TESTS             │
│                 │    │     TESTS       │    │                             │
│ • pytest -v    │    │ • Mock services │    │ • Container build           │
│ • 32 tests      │    │ • HTTP API      │    │ • Integration testing       │
│ • Coverage      │    │ • Real workflow │    │ • Network isolation         │
│ • Fast (~30s)   │    │ • Realistic     │    │ • Production-like           │
└─────────────────┘    └─────────────────┘    └─────────────────────────────┘

STAGE 4: BUILD & PACKAGE
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐
│  DOCKER BUILD   │───▶│   IMAGE TAG     │───▶│      REGISTRY               │
│                 │    │                 │    │                             │
│ • Multi-stage   │    │ • SHA-based     │    │ • Google Container          │
│ • Optimized     │    │ • Version tag   │    │   Registry (GCR)            │
│ • Security      │    │ • Latest tag    │    │ • Vulnerability scan        │
└─────────────────┘    └─────────────────┘    └─────────────────────────────┘

STAGE 5: DEPLOYMENT
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐
│   STAGING       │───▶│   PRODUCTION    │───▶│     VERIFICATION            │
│                 │    │                 │    │                             │
│ • Cloud Run     │    │ • Blue/Green    │    │ • Health checks             │
│ • Test env      │    │ • Zero downtime │    │ • Smoke tests               │
│ • Validation    │    │ • Auto rollback │    │ • Performance tests         │
└─────────────────┘    └─────────────────┘    └─────────────────────────────┘
```

## 🔄 **Detailed Workflow Diagram**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GITHUB ACTIONS WORKFLOW                            │
│                           .github/workflows/                               │
└─────────────────────────────────────────────────────────────────────────────┘

name: CI/CD Pipeline
on: [push, pull_request, schedule]

jobs:
┌─────────────────────────────────────────────────────────────────────────────┐
│ JOB 1: LINTING & FORMATTING                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ runs-on: ubuntu-latest                                                  │ │
│ │ strategy:                                                               │ │
│ │   matrix:                                                               │ │
│ │     python-version: ["3.11"]                                           │ │
│ │                                                                         │ │
│ │ steps:                                                                  │ │
│ │ 1. ✅ Checkout code                                                     │ │
│ │ 2. 🐍 Setup Python 3.11                                                │ │
│ │ 3. 📦 Install dependencies                                              │ │
│ │ 4. 🔍 Run flake8 (linting)                                             │ │
│ │ 5. 🎨 Run black (formatting)                                           │ │
│ │ 6. 📏 Run isort (import sorting)                                       │ │
│ │ 7. 🔒 Run bandit (security)                                            │ │
│ │ 8. 🛡️ Run safety (dependencies)                                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ JOB 2: UNIT TESTING                                                        │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ runs-on: ubuntu-latest                                                  │ │
│ │ needs: [linting]                                                        │ │
│ │                                                                         │ │
│ │ steps:                                                                  │ │
│ │ 1. ✅ Checkout code                                                     │ │
│ │ 2. 🐍 Setup Python 3.11                                                │ │
│ │ 3. 💾 Cache pip dependencies                                            │ │
│ │ 4. 📦 Install requirements                                              │ │
│ │ 5. 🧪 Run pytest with coverage                                         │ │
│ │    └─ pytest tests/ --cov=. --cov-report=xml                          │ │
│ │ 6. 📊 Upload coverage to Codecov                                       │ │
│ │ 7. 📋 Generate test report                                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ JOB 3: INTEGRATION TESTING                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ runs-on: ubuntu-latest                                                  │ │
│ │ needs: [unit-tests]                                                     │ │
│ │                                                                         │ │
│ │ steps:                                                                  │ │
│ │ 1. ✅ Checkout code                                                     │ │
│ │ 2. 🐍 Setup Python 3.11                                                │ │
│ │ 3. 📦 Install dependencies                                              │ │
│ │ 4. 🔧 Setup test environment                                            │ │
│ │    └─ TESTING=true                                                     │ │
│ │ 5. 🧪 Run integration tests                                             │ │
│ │    └─ pytest tests/test_integration.py -v                             │ │
│ │ 6. 📊 Archive test results                                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ JOB 4: DOCKER TESTING                                                      │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ runs-on: ubuntu-latest                                                  │ │
│ │ needs: [integration-tests]                                              │ │
│ │                                                                         │ │
│ │ steps:                                                                  │ │
│ │ 1. ✅ Checkout code                                                     │ │
│ │ 2. 🐳 Setup Docker Buildx                                               │ │
│ │ 3. 🏗️ Build Docker image                                                │ │
│ │    └─ docker build -t telegramgroupie:test .                        │ │
│ │ 4. 🧪 Run Docker integration tests                                      │ │
│ │    └─ bash scripts/run-basic-docker-test.sh                           │ │
│ │ 5. 🔍 Run container security scan                                       │ │
│ │ 6. 📊 Archive Docker test results                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ JOB 5: BUILD & PUBLISH                                                     │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ runs-on: ubuntu-latest                                                  │ │
│ │ needs: [docker-tests]                                                   │ │
│ │ if: github.ref == 'refs/heads/main'                                     │ │
│ │                                                                         │ │
│ │ steps:                                                                  │ │
│ │ 1. ✅ Checkout code                                                     │ │
│ │ 2. 🔑 Authenticate to Google Cloud                                      │ │
│ │ 3. 🐳 Configure Docker for GCR                                          │ │
│ │ 4. 🏗️ Build production image                                            │ │
│ │    └─ docker build -t gcr.io/$PROJECT/telegramgroupie:$SHA .        │ │
│ │ 5. 🚀 Push to Container Registry                                        │ │
│ │ 6. 🔖 Tag with version                                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ JOB 6: DEPLOY TO STAGING                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ runs-on: ubuntu-latest                                                  │ │
│ │ needs: [build-and-publish]                                              │ │
│ │ environment: staging                                                    │ │
│ │                                                                         │ │
│ │ steps:                                                                  │ │
│ │ 1. ✅ Checkout code                                                     │ │
│ │ 2. 🔑 Authenticate to Google Cloud                                      │ │
│ │ 3. 🚀 Deploy to Cloud Run (staging)                                     │ │
│ │    └─ gcloud run deploy telegramgroupie-staging                     │ │
│ │ 4. 🔍 Run smoke tests                                                   │ │
│ │ 5. 📋 Update deployment status                                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ JOB 7: DEPLOY TO PRODUCTION                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ runs-on: ubuntu-latest                                                  │ │
│ │ needs: [deploy-staging]                                                 │ │
│ │ environment: production                                                 │ │
│ │ if: github.ref == 'refs/heads/main' && success()                       │ │
│ │                                                                         │ │
│ │ steps:                                                                  │ │
│ │ 1. ✅ Checkout code                                                     │ │
│ │ 2. 🔑 Authenticate to Google Cloud                                      │ │
│ │ 3. 🚀 Deploy to Cloud Run (production)                                  │ │
│ │    └─ gcloud run deploy telegramgroupie                             │ │
│ │ 4. 🔍 Run health checks                                                 │ │
│ │ 5. 📊 Monitor deployment metrics                                        │ │
│ │ 6. 🎉 Send success notification                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🧪 **Testing Strategy Matrix**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TESTING PYRAMID                               │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │     E2E     │ ← Few, Slow, Expensive
                              │    Tests    │   Real Environment
                              └─────────────┘
                          ┌─────────────────────┐
                          │   Integration       │ ← Some, Medium Speed
                          │      Tests          │   Mock Services
                          └─────────────────────┘
                    ┌─────────────────────────────────┐
                    │         Unit Tests              │ ← Many, Fast, Cheap
                    │       (32 tests)                │   Isolated Functions
                    └─────────────────────────────────┘

UNIT TESTS (Fast, Isolated)
┌─────────────────────────────────────────────────────────────────────────────┐
│ test_main.py                    │ Flask application core functionality       │
│ ├─ test_health_endpoint         │ Health check endpoint                      │
│ ├─ test_webhook_validation      │ Secret validation                          │
│ ├─ test_message_processing      │ Message handling logic                     │
│ └─ test_error_handling          │ Error scenarios                            │
│                                                                             │
│ test_encryption.py              │ Encryption/decryption functionality        │
│ ├─ test_encrypt_message         │ Message encryption                         │
│ ├─ test_decrypt_message         │ Message decryption                         │
│ ├─ test_key_management          │ KMS key operations                         │
│ └─ test_encryption_errors       │ Error scenarios                            │
│                                                                             │
│ test_message_retrieval.py       │ Message API functionality                  │
│ ├─ test_get_messages            │ Message retrieval                          │
│ ├─ test_filtering               │ Chat/user filtering                        │
│ ├─ test_pagination              │ Cursor-based pagination                    │
│ └─ test_batch_processing        │ Bulk operations                            │
└─────────────────────────────────────────────────────────────────────────────┘

INTEGRATION TESTS (Realistic, Mock Services)
┌─────────────────────────────────────────────────────────────────────────────┐
│ test_integration.py             │ End-to-end workflow with mocks             │
│ ├─ test_webhook_to_storage      │ Complete message flow                      │
│ ├─ test_message_encryption      │ Encryption integration                     │
│ ├─ test_api_endpoints           │ REST API functionality                     │
│ └─ test_error_scenarios         │ Failure modes                              │
└─────────────────────────────────────────────────────────────────────────────┘

DOCKER TESTS (Production-like, Containerized)
┌─────────────────────────────────────────────────────────────────────────────┐
│ test_integration_docker.py      │ Container-based integration                │
│ ├─ test_container_startup       │ Docker environment                         │
│ ├─ test_network_isolation       │ Container networking                       │
│ ├─ test_environment_variables   │ Configuration management                   │
│ └─ test_health_monitoring       │ Container health                           │
└─────────────────────────────────────────────────────────────────────────────┘

E2E TESTS (Real Environment, Full Stack)
┌─────────────────────────────────────────────────────────────────────────────┐
│ test_e2e.py                     │ Real Telegram/Cloud integration            │
│ ├─ test_telegram_webhook        │ Real webhook from Telegram                 │
│ ├─ test_firestore_storage       │ Real Firestore operations                  │
│ ├─ test_kms_encryption          │ Real KMS encryption                        │
│ └─ test_production_deployment   │ Cloud Run deployment                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔧 **Build & Deployment Pipeline**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUILD PIPELINE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

SOURCE CODE
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│ │    main.py  │   │ encryption  │   │    tests/   │   │ Dockerfile  │     │
│ │             │   │    .py      │   │             │   │             │     │
│ │ Flask app   │   │ KMS crypto  │   │ Test suite  │   │ Container   │     │
│ └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
DOCKER BUILD PROCESS
┌─────────────────────────────────────────────────────────────────────────────┐
│ FROM python:3.11-slim                                                      │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ STAGE 1: Base Image                                                     │ │
│ │ ├─ Install system dependencies                                          │ │
│ │ ├─ Create non-root user                                                 │ │
│ │ └─ Set up working directory                                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ STAGE 2: Dependencies                                                   │ │
│ │ ├─ Copy requirements.txt                                                │ │
│ │ ├─ pip install --no-cache-dir                                          │ │
│ │ └─ Layer caching optimization                                           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ STAGE 3: Application                                                    │ │
│ │ ├─ Copy source code                                                     │ │
│ │ ├─ Copy mock implementations                                            │ │
│ │ ├─ Set environment variables                                            │ │
│ │ └─ Configure entry point                                                │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
DEPLOYMENT TARGETS
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGING ENVIRONMENT                    │ PRODUCTION ENVIRONMENT              │
│ ┌─────────────────────────────────┐    │ ┌─────────────────────────────────┐ │
│ │ Google Cloud Run                │    │ │ Google Cloud Run                │ │
│ │ ├─ Service: telegramgroupie-  │    │ │ ├─ Service: telegramgroupie   │ │
│ │ │   staging                     │    │ │ │                               │ │
│ │ ├─ Region: us-central1          │    │ │ ├─ Region: us-central1          │ │
│ │ ├─ Memory: 512Mi                │    │ │ ├─ Memory: 1Gi                  │ │
│ │ ├─ CPU: 1                       │    │ │ ├─ CPU: 2                       │ │
│ │ ├─ Concurrency: 10              │    │ │ ├─ Concurrency: 100             │ │
│ │ ├─ Min instances: 0             │    │ │ ├─ Min instances: 1              │ │
│ │ ├─ Max instances: 10            │    │ │ ├─ Max instances: 100            │ │
│ │ └─ Allow unauthenticated: true  │    │ │ ├─ Allow unauthenticated: true  │ │
│ └─────────────────────────────────┘    │ └─────────────────────────────────┘ │
│                                        │                                     │
│ ENVIRONMENT VARIABLES:                 │ ENVIRONMENT VARIABLES:              │
│ ├─ TELEGRAM_TOKEN=***               │ ├─ TELEGRAM_TOKEN=***             │
│ ├─ WEBHOOK_SECRET=***               │ ├─ WEBHOOK_SECRET=***             │
│ ├─ GCP_PROJECT_ID=staging-project   │ ├─ GCP_PROJECT_ID=prod-project     │
│ └─ PORT=8080                        │ └─ PORT=8080                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📊 **Monitoring & Alerting**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OBSERVABILITY STACK                              │
└─────────────────────────────────────────────────────────────────────────────┘

METRICS COLLECTION
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│ │   APPLICATION   │  │   INFRASTRUCTURE│  │        BUSINESS             │ │
│ │    METRICS      │  │     METRICS     │  │       METRICS               │ │
│ │                 │  │                 │  │                             │ │
│ │ • Request rate  │  │ • CPU usage     │  │ • Messages processed/min    │ │
│ │ • Response time │  │ • Memory usage  │  │ • Encryption operations     │ │
│ │ • Error rate    │  │ • Network I/O   │  │ • API calls per endpoint    │ │
│ │ • Throughput    │  │ • Disk usage    │  │ • User engagement           │ │
│ │ • Throughput    │  │ • Disk usage    │  │ • User engagement           │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

LOGGING STRATEGY
┌─────────────────────────────────────────────────────────────────────────────┐
│ STRUCTURED LOGGING (JSON)                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ {                                                                       │ │
│ │   "timestamp": "2024-01-01T12:00:00Z",                                 │ │
│ │   "level": "INFO",                                                      │ │
│ │   "logger": "telegramgroupie",                                        │ │
│ │   "message": "Message processed successfully",                          │ │
│ │   "context": {                                                          │ │
│ │     "message_id": 12345,                                                │ │
│ │     "chat_id": -100123456789,                                           │ │
│ │     "user_id": 987654321,                                               │ │
│ │     "processing_time_ms": 150,                                          │ │
│ │     "encrypted": true                                                   │ │
│ │   },                                                                    │ │
│ │   "request_id": "req_uuid_12345",                                       │ │
│ │   "trace_id": "trace_xyz_789"                                           │ │
│ │ }                                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

ALERTING RULES
┌─────────────────────────────────────────────────────────────────────────────┐
│ CRITICAL ALERTS                        │ WARNING ALERTS                     │
│ ┌─────────────────────────────────┐    │ ┌─────────────────────────────────┐ │
│ │ • Service down (5xx > 50%)      │    │ │ • High response time (>2s)      │ │
│ │ • Error rate > 10%              │    │ │ • Memory usage > 80%            │ │
│ │ • Zero requests for 10 minutes  │    │ │ • CPU usage > 70%               │ │
│ │ • Failed deployments            │    │ │ • Disk usage > 85%              │ │
│ │ • Security breaches             │    │ │ • High request rate             │ │
│ └─────────────────────────────────┘    │ └─────────────────────────────────┘ │
│                                        │                                     │
│ NOTIFICATION CHANNELS:                 │ NOTIFICATION CHANNELS:              │
│ ├─ PagerDuty (immediate)            │ ├─ Slack #alerts                   │
│ ├─ SMS to on-call engineer          │ ├─ Email to team                   │
│ └─ Slack #critical-alerts           │ └─ Dashboard notifications         │
└─────────────────────────────────────────────────────────────────────────────┘

DASHBOARD VIEWS
┌─────────────────────────────────────────────────────────────────────────────┐
│ OPERATIONAL DASHBOARD                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │ │
│ │ │ Request     │ │ Error Rate  │ │ Response    │ │ Throughput  │       │ │
│ │ │ Volume      │ │             │ │ Time        │ │             │       │ │
│ │ │ 📈 1,234/min│ │ 🚨 2.3%     │ │ ⚡ 145ms    │ │ 📊 15msg/s  │       │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │ │
│ │                                                                       │ │
│ │ ┌─────────────────────────────────────────────────────────────────┐   │ │
│ │ │                    Service Health                               │   │ │
│ │ │ ├─ Application: ✅ Healthy                                     │   │ │
│ │ │ ├─ Database: ✅ Healthy                                        │   │ │
│ │ │ ├─ Encryption: ✅ Healthy                                      │   │ │
│ │ │ └─ External APIs: ⚠️ Degraded                                 │   │ │
│ │ └─────────────────────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 **Deployment Strategies**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT STRATEGIES                             │
└─────────────────────────────────────────────────────────────────────────────┘

BLUE-GREEN DEPLOYMENT
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│ BEFORE DEPLOYMENT              │ DURING DEPLOYMENT                          │
│ ┌─────────────────────────┐    │ ┌─────────────────────────┐                │
│ │       BLUE              │    │ │       BLUE              │                │
│ │    (Current)            │    │ │    (Current)            │                │
│ │                         │    │ │                         │                │
│ │ • Version 1.2.3         │    │ │ • Version 1.2.3         │                │
│ │ • 100% traffic          │ ◀──┤ │ • 100% → 0% traffic     │                │
│ │ • Stable                │    │ │ • Stable                │                │
│ └─────────────────────────┘    │ └─────────────────────────┘                │
│                                │                                            │
│ ┌─────────────────────────┐    │ ┌─────────────────────────┐                │
│ │       GREEN             │    │ │       GREEN             │                │
│ │     (Inactive)          │    │ │      (New)              │                │
│ │                         │    │ │                         │                │
│ │ • No deployment         │    │ │ • Version 1.2.4         │                │
│ │ • 0% traffic            │ ────┤ │ • 0% → 100% traffic     │ ◀─ NEW TRAFFIC │
│ │ • Standby               │    │ │ • Testing               │                │
│ └─────────────────────────┘    │ └─────────────────────────┘                │
│                                │                                            │
│ AFTER SUCCESSFUL DEPLOYMENT                                                 │
│ ┌─────────────────────────┐                                                 │
│ │       GREEN             │                                                 │
│ │      (Active)           │                                                 │
│ │                         │                                                 │
│ │ • Version 1.2.4         │                                                 │
│ │ • 100% traffic          │ ◀─ ALL TRAFFIC                                  │
│ │ • Production            │                                                 │
│ └─────────────────────────┘                                                 │
│                                                                             │
│ Blue environment becomes new standby for next deployment                    │
└─────────────────────────────────────────────────────────────────────────────┘

CANARY DEPLOYMENT
┌─────────────────────────────────────────────────────────────────────────────┐
│ TRAFFIC SPLIT STRATEGY                                                      │
│                                                                             │
│ PHASE 1: Initial Canary (5%)      │ PHASE 2: Expand Canary (25%)           │
│ ┌─────────────────────────────┐    │ ┌─────────────────────────────┐       │
│ │ Production v1.2.3           │    │ │ Production v1.2.3           │       │
│ │ ██████████████████████ 95%  │    │ │ ████████████████ 75%        │       │
│ └─────────────────────────────┘    │ └─────────────────────────────┘       │
│ ┌─────────────────────────────┐    │ ┌─────────────────────────────┐       │
│ │ Canary v1.2.4               │    │ │ Canary v1.2.4               │       │
│ │ █ 5%                        │    │ │ ██████ 25%                  │       │
│ └─────────────────────────────┘    │ └─────────────────────────────┘       │
│                                    │                                       │
│ PHASE 3: Full Canary (50%)         │ PHASE 4: Complete (100%)              │
│ ┌─────────────────────────────┐    │ ┌─────────────────────────────┐       │
│ │ Production v1.2.3           │    │ │ New Production v1.2.4       │       │
│ │ ██████████ 50%              │    │ │ ████████████████████ 100%   │       │
│ └─────────────────────────────┘    │ └─────────────────────────────┘       │
│ ┌─────────────────────────────┐    │                                       │
│ │ Canary v1.2.4               │    │ Old version decommissioned            │
│ │ ██████████ 50%              │    │                                       │
│ └─────────────────────────────┘    │                                       │
│                                                                             │
│ AUTOMATED PROGRESSION CRITERIA:                                             │
│ ├─ Error rate < 1%                                                          │
│ ├─ Response time < 200ms                                                    │
│ ├─ No critical alerts                                                       │
│ └─ Successful health checks                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

ROLLBACK STRATEGY
┌─────────────────────────────────────────────────────────────────────────────┐
│ AUTOMATIC ROLLBACK TRIGGERS                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. Error rate > 5% for 2 minutes                                       │ │
│ │ 2. Response time > 5 seconds for 1 minute                              │ │
│ │ 3. Health check failures > 3 consecutive                               │ │
│ │ 4. Critical alert triggered                                             │ │
│ │ 5. Zero successful requests for 30 seconds                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ROLLBACK PROCESS                                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. 🚨 Trigger detected                                                   │ │
│ │ 2. 🛑 Stop traffic to new version                                        │ │
│ │ 3. 🔄 Route 100% traffic to previous version                             │ │
│ │ 4. 📢 Send alert notifications                                           │ │
│ │ 5. 📊 Collect failure metrics                                            │ │
│ │ 6. 🔍 Initiate post-mortem process                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

This comprehensive CI/CD pipeline documentation provides detailed workflows, testing strategies, deployment patterns, and monitoring approaches. The ASCII diagrams ensure compatibility across all documentation systems and provide clear visual representation of the pipeline flow.
