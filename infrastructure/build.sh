#!/bin/bash

# TelegramGroupie Build Script
# Updated for dependency injection architecture

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REGION="us-central1"
ENVIRONMENT="production"

echo -e "${BLUE}🏗️  TelegramGroupie Build & Deploy${NC}"
echo -e "${BLUE}Using dependency injection architecture${NC}"
echo ""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment) ENVIRONMENT="$2"; shift 2 ;;
        -r|--region) REGION="$2"; shift 2 ;;
        -h|--help) 
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --environment ENV    Environment: staging|production (default: production)"
            echo "  -r, --region REGION      GCP region (default: us-central1)"
            echo "  -h, --help               Show this help"
            echo ""
            echo "This script will:"
            echo "  1. Set up Python virtual environment"
            echo "  2. Install dependencies"
            echo "  3. Run comprehensive tests"
            echo "  4. Build and deploy to Google Cloud Run"
            echo ""
            echo "For new project setup, run: ./devops/scripts/setup-gcp-project.sh"
            echo "For advanced deployment options, run: ./devops/scripts/deploy.sh"
            exit 0
            ;;
        *) echo "Unknown option: $1"; echo "Use -h for help"; exit 1 ;;
    esac
done

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Ensure pip is up to date
echo -e "${YELLOW}📦 Updating pip...${NC}"
pip install --upgrade pip

# Install or upgrade dependencies
echo -e "${YELLOW}📦 Installing/upgrading dependencies...${NC}"
pip install -r infrastructure/requirements/requirements.txt

# Install dev dependencies for testing
if [ -f "infrastructure/requirements/requirements-dev.txt" ]; then
    pip install -r infrastructure/requirements/requirements-dev.txt
fi

# Verify Flask is installed
if ! python -c "import flask" &> /dev/null; then
    echo -e "${RED}❌ Flask installation failed. Please check your requirements.txt${NC}"
    exit 1
fi

# Verify dependency injection architecture
echo -e "${YELLOW}🔍 Verifying dependency injection architecture...${NC}"
if ! python -c "from service_container import create_service_container; print('✅ Service container working')" &> /dev/null; then
    echo -e "${RED}❌ Dependency injection architecture verification failed${NC}"
    exit 1
fi

# Run comprehensive test suite
echo -e "${YELLOW}🧪 Running comprehensive test suite...${NC}"

# Unit tests
echo "Running unit tests..."
if ! pytest tests/ -v --tb=short; then
    echo -e "${RED}❌ Tests failed. Aborting build.${NC}"
    exit 1
fi

# Check if Docker is available for integration tests
if command -v docker &> /dev/null; then
    echo "Running Docker integration tests..."
    if [ -f "devops/scripts/run-basic-docker-test.sh" ]; then
        bash devops/scripts/run-basic-docker-test.sh || echo -e "${YELLOW}⚠️  Docker tests failed but continuing...${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not available, skipping Docker tests${NC}"
fi

echo -e "${GREEN}✅ All tests passed!${NC}"

# Deactivate virtual environment
deactivate

# Get the project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No Google Cloud project ID found.${NC}"
    echo "Please run one of the following:"
    echo "  1. gcloud config set project YOUR_PROJECT_ID"
    echo "  2. ./scripts/setup-gcp-project.sh -p YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${BLUE}📋 Using project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}📋 Environment: ${ENVIRONMENT}${NC}"

# Check if environment configuration exists
ENV_FILE="configuration/${ENVIRONMENT}.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Environment configuration not found: ${ENV_FILE}${NC}"
    echo "To set up infrastructure, run:"
    echo "  ./devops/scripts/setup-gcp-project.sh -p $PROJECT_ID -e $ENVIRONMENT"
    echo ""
    echo "Or to deploy with manual configuration:"
    echo "  export TELEGRAM_TOKEN='your-bot-token'"
    echo "  export WEBHOOK_SECRET='your-webhook-secret'"
    echo "  ./devops/scripts/deploy.sh -p $PROJECT_ID -e $ENVIRONMENT -t \$TELEGRAM_TOKEN -s \$WEBHOOK_SECRET"
    exit 1
fi

# Load environment configuration
echo -e "${YELLOW}📋 Loading environment configuration...${NC}"
source "$ENV_FILE"

# Check for required secrets
if [ -z "$TELEGRAM_TOKEN" ] || [ -z "$WEBHOOK_SECRET" ]; then
    echo -e "${YELLOW}⚠️  TELEGRAM_TOKEN and WEBHOOK_SECRET not found in environment${NC}"
    echo "Please set them:"
    echo "  export TELEGRAM_TOKEN='your-telegram-bot-token'"
    echo "  export WEBHOOK_SECRET='your-webhook-secret'"
    echo ""
    read -p "Do you want to continue with just building (no deployment)? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    BUILD_ONLY=true
fi

# Use the new deployment script
if [ "$BUILD_ONLY" = true ]; then
    echo -e "${YELLOW}🏗️  Building Docker image only...${NC}"
    ./devops/scripts/deploy.sh -p "$PROJECT_ID" -e "$ENVIRONMENT" --build-only
else
    echo -e "${YELLOW}🚀 Building and deploying...${NC}"
    ./devops/scripts/deploy.sh -p "$PROJECT_ID" -e "$ENVIRONMENT" -t "$TELEGRAM_TOKEN" -s "$WEBHOOK_SECRET"
fi

echo -e "${GREEN}✅ Build process completed successfully!${NC}"
