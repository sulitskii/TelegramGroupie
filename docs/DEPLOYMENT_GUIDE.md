# TelegramGroupie Deployment Guide

This guide provides comprehensive instructions for deploying TelegramGroupie to Google Cloud Platform using the dependency injection architecture.

## 🏗️ **Architecture Overview**

TelegramGroupie uses a clean dependency injection architecture that eliminates conditional logic:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT ARCHITECTURE                             │
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

## 🚀 **Quick Start**

### Prerequisites

1. **Google Cloud CLI** installed and authenticated
2. **Docker** (optional, for local testing)
3. **Python 3.11+** with pip
4. **Git** (to clone the repository)

```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Authenticate
gcloud auth login
gcloud auth application-default login
```

### 1. Clone and Setup

```bash
git clone <repository-url>
cd telegram2whatsapp
chmod +x scripts/*.sh
```

### 2. Create GCP Project and Infrastructure

```bash
# Create a new GCP project (if needed)
gcloud projects create my-telegramgroupie-prod
gcloud billing projects link my-telegramgroupie-prod --billing-account=YOUR_BILLING_ACCOUNT

# Set up all infrastructure
./scripts/setup-gcp-project.sh -p my-telegramgroupie-prod -e production
```

### 3. Configure Secrets

```bash
# Set your Telegram bot token and webhook secret
export TELEGRAM_TOKEN="your-bot-token-from-botfather"
export WEBHOOK_SECRET="$(openssl rand -hex 32)"
```

### 4. Deploy

```bash
# Simple deployment
./build.sh

# Or using the deployment script directly
./scripts/deploy.sh -p my-telegramgroupie-prod -t "$TELEGRAM_TOKEN" -s "$WEBHOOK_SECRET"
```

## 📋 **Detailed Deployment Steps**

### Step 1: Infrastructure Setup

The `setup-gcp-project.sh` script creates all necessary GCP resources:

```bash
./scripts/setup-gcp-project.sh -p PROJECT_ID [-e ENVIRONMENT] [-r REGION]
```

**What it does:**
- ✅ Enables required GCP APIs (Cloud Run, Firestore, KMS, etc.)
- ✅ Creates Firestore database in native mode
- ✅ Sets up Cloud KMS key ring and encryption key
- ✅ Configures IAM permissions for Cloud Run service account
- ✅ Creates optimized Firestore indexes
- ✅ Generates environment configuration file

**Options:**
- `-p PROJECT_ID`: GCP project ID (required)
- `-e ENVIRONMENT`: staging or production (default: production)
- `-r REGION`: GCP region (default: us-central1)
- `-l KMS_LOCATION`: KMS location (default: global)

**Example:**
```bash
# Production setup
./scripts/setup-gcp-project.sh -p my-telegramgroupie-prod -e production

# Staging setup in Europe
./scripts/setup-gcp-project.sh -p my-telegramgroupie-staging -e staging -r europe-west1
```

### Step 2: Environment Configuration

After running setup, you'll have an environment file (e.g., `production.env`):

```bash
# Example production.env
GCP_PROJECT_ID=my-telegramgroupie-prod
KMS_LOCATION=global
KMS_KEY_RING=telegramgroupie-messages-production
KMS_KEY_ID=message-key-production
LOG_LEVEL=INFO
SERVICE_NAME=telegramgroupie
REGION=us-central1
PORT=8080
```

**Add your secrets:**
```bash
# Add to the environment file or export
export TELEGRAM_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export WEBHOOK_SECRET="a1b2c3d4e5f6..."
```

### Step 3: Application Deployment

Use the `deploy.sh` script for flexible deployment options:

```bash
./scripts/deploy.sh [OPTIONS]
```

**Options:**
- `-p PROJECT_ID`: Google Cloud Project ID (required)
- `-e ENVIRONMENT`: staging|production (default: production)
- `-r REGION`: GCP region (default: us-central1)
- `-t TOKEN`: Telegram bot token (required for deployment)
- `-s SECRET`: Webhook secret (required for deployment)
- `--build-only`: Only build the Docker image
- `--deploy-only`: Only deploy (skip build)
- `--status`: Show deployment status
- `--rollback`: Rollback to previous revision

**Examples:**

```bash
# Full deployment
./scripts/deploy.sh -p my-project -t "$TELEGRAM_TOKEN" -s "$WEBHOOK_SECRET"

# Build only (for testing)
./scripts/deploy.sh -p my-project --build-only

# Deploy to staging
./scripts/deploy.sh -p my-project-staging -e staging -t "$TELEGRAM_TOKEN" -s "$WEBHOOK_SECRET"

# Check deployment status
./scripts/deploy.sh -p my-project --status

# Emergency rollback
./scripts/deploy.sh -p my-project --rollback
```

### Step 4: Verification

After deployment, verify everything works:

```bash
# Check service status
./scripts/deploy.sh -p my-project --status

# Test the API
SERVICE_URL="https://your-service-url"
curl "${SERVICE_URL}/messages?limit=5"

# Set up Telegram webhook
curl -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
     -d "url=${SERVICE_URL}/webhook/${WEBHOOK_SECRET}"
```

## 🌍 **Multi-Environment Setup**

### Production + Staging Setup

```bash
# 1. Set up production
./scripts/setup-gcp-project.sh -p company-telegramgroupie-prod -e production

# 2. Set up staging
./scripts/setup-gcp-project.sh -p company-telegramgroupie-staging -e staging

# 3. Deploy to staging first
export TELEGRAM_TOKEN_STAGING="staging-bot-token"
export WEBHOOK_SECRET_STAGING="staging-webhook-secret"
./scripts/deploy.sh -p company-telegramgroupie-staging -e staging \
                    -t "$TELEGRAM_TOKEN_STAGING" -s "$WEBHOOK_SECRET_STAGING"

# 4. Deploy to production
export TELEGRAM_TOKEN_PROD="production-bot-token"
export WEBHOOK_SECRET_PROD="production-webhook-secret"
./scripts/deploy.sh -p company-telegramgroupie-prod -e production \
                    -t "$TELEGRAM_TOKEN_PROD" -s "$WEBHOOK_SECRET_PROD"
```

### Multi-Region Deployment

```bash
# Deploy to multiple regions for high availability
./scripts/setup-gcp-project.sh -p my-project-us -e production -r us-central1
./scripts/setup-gcp-project.sh -p my-project-eu -e production -r europe-west1
./scripts/setup-gcp-project.sh -p my-project-asia -e production -r asia-southeast1
```

## 🔧 **Configuration Reference**

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud Project ID | `my-telegramgroupie-prod` |
| `TELEGRAM_TOKEN` | Telegram Bot Token | `1234567890:ABC...` |
| `WEBHOOK_SECRET` | Webhook Secret | `a1b2c3d4e5f6...` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KMS_LOCATION` | KMS key location | `global` |
| `KMS_KEY_RING` | KMS key ring name | `telegramgroupie-messages-{env}` |
| `KMS_KEY_ID` | KMS key ID | `message-key-{env}` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PORT` | Service port | `8080` |

### Cloud Run Configuration

| Setting | Production | Staging |
|---------|------------|---------|
| Memory | 1 GiB | 512 MiB |
| CPU | 1 vCPU | 1 vCPU |
| Concurrency | 80 | 10 |
| Max Instances | 100 | 10 |
| Min Instances | 1 | 0 |

## 🛠️ **Troubleshooting**

### Common Issues

#### 1. Permission Denied Errors

```bash
# Solution: Check IAM permissions
gcloud projects get-iam-policy $PROJECT_ID
gcloud kms keys get-iam-policy $KMS_KEY_ID --keyring=$KMS_KEY_RING --location=$KMS_LOCATION
```

#### 2. Service Won't Start

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telegramgroupie" --limit=50

# Check service status
./scripts/deploy.sh -p $PROJECT_ID --status
```

#### 3. Tests Failing

```bash
# Run tests with verbose output
pytest tests/ -v -s

# Check dependency injection
python -c "from src.core.service_container import create_service_container; print('OK')"
```

#### 4. Environment Variable Issues

```bash
# Check current configuration
gcloud run services describe telegramgroupie --region=$REGION

# Update environment variables
gcloud run services update telegramgroupie --region=$REGION \
    --set-env-vars="NEW_VAR=value"
```

### Debug Commands

```bash
# View service configuration
gcloud run services describe telegramgroupie --region=us-central1

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=20

# Test service health
curl -v https://your-service-url/

# Check KMS permissions
gcloud kms keys get-iam-policy message-key-production \
    --keyring=telegramgroupie-messages-production --location=global
```

## 📊 **Monitoring and Maintenance**

### Health Monitoring

```bash
# Automated health checks
curl -f "https://your-service-url/" || echo "Service down"

# Check service metrics
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"
```

### Log Analysis

```bash
# Application logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telegramgroupie" \
    --format="table(timestamp,textPayload)"

# Error logs only
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=50

# Real-time log streaming
gcloud logging tail "resource.type=cloud_run_revision"
```

### Performance Monitoring

```bash
# Cloud Run metrics
gcloud run services describe telegramgroupie --region=us-central1 \
    --format="table(status.traffic[].revisionName,status.traffic[].percent)"

# Request metrics
gcloud logging read "resource.type=cloud_run_revision" \
    --format="table(timestamp,httpRequest.requestMethod,httpRequest.status)"
```

## 🔄 **CI/CD Integration**

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy TelegramGroupie

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ -v

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${{ secrets.GCP_PROJECT_STAGING }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      - run: |
          ./scripts/deploy.sh \
            -p ${{ secrets.GCP_PROJECT_STAGING }} \
            -e staging \
            -t "${{ secrets.TELEGRAM_TOKEN_STAGING }}" \
            -s "${{ secrets.WEBHOOK_SECRET_STAGING }}"

  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${{ secrets.GCP_PROJECT_PROD }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      - run: |
          ./scripts/deploy.sh \
            -p ${{ secrets.GCP_PROJECT_PROD }} \
            -e production \
            -t "${{ secrets.TELEGRAM_TOKEN_PROD }}" \
            -s "${{ secrets.WEBHOOK_SECRET_PROD }}"
```

## 🔐 **Security Best Practices**

### Secrets Management

1. **Never commit secrets to version control**
2. **Use Google Secret Manager for production secrets**
3. **Rotate webhook secrets regularly**
4. **Use separate Telegram bots for staging/production**

### Infrastructure Security

1. **Enable audit logging**
2. **Use least-privilege IAM roles**
3. **Regular security scanning**
4. **Monitor for suspicious activity**

### Example Secret Manager Setup

```bash
# Store secrets in Google Secret Manager
gcloud secrets create telegram-token --data-file=-
echo "$TELEGRAM_TOKEN" | gcloud secrets versions add telegram-token --data-file=-

gcloud secrets create webhook-secret --data-file=-
echo "$WEBHOOK_SECRET" | gcloud secrets versions add webhook-secret --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding telegram-token \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/secretmanager.secretAccessor"
```

## 📚 **Additional Resources**

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud KMS Documentation](https://cloud.google.com/kms/docs)
- [Google Cloud Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [TelegramGroupie Architecture Guide](./ARCHITECTURE.md)
- [TelegramGroupie Testing Guide](./TESTING.md)

---

## 🎯 **Summary**

This deployment guide provides everything needed to deploy TelegramGroupie to a new GCP project:

1. **🏗️ Infrastructure Setup**: Automated GCP resource creation
2. **🚀 Application Deployment**: Flexible deployment with rollback capabilities  
3. **🔧 Configuration Management**: Environment-specific configurations
4. **📊 Monitoring**: Comprehensive logging and health checks
5. **🔐 Security**: Best practices for secrets and permissions

The dependency injection architecture ensures that the same application code runs identically across all environments, providing confidence in deployments and eliminating environment-specific bugs.

**Ready to deploy? Start with:**
```bash
./scripts/setup-gcp-project.sh -p your-project-id
``` 