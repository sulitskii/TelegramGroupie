#!/bin/bash

# TelegramGroupie Deployment Script
# Builds and deploys the application to Google Cloud Run

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
BUILD_ONLY=false
DEPLOY_ONLY=false
STATUS_ONLY=false
ROLLBACK=false

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p PROJECT_ID     Google Cloud Project ID (required)"
    echo "  -e ENVIRONMENT    Environment: staging|production (default: production)"
    echo "  -r REGION         GCP region (default: us-central1)"
    echo "  -t TOKEN          Telegram bot token (required for deployment)"
    echo "  -s SECRET         Webhook secret (required for deployment)"
    echo "  --build-only      Only build the Docker image"
    echo "  --deploy-only     Only deploy (skip build)"
    echo "  --status          Show deployment status"
    echo "  --rollback        Rollback to previous revision"
    echo "  -h                Show this help"
    echo ""
    echo "Examples:"
    echo "  # Full deployment"
    echo "  $0 -p my-project -t 'bot123:ABC' -s 'webhook-secret'"
    echo ""
    echo "  # Staging deployment"
    echo "  $0 -p my-project-staging -e staging -t 'bot123:ABC' -s 'webhook-secret'"
    echo ""
    echo "  # Build only"
    echo "  $0 -p my-project --build-only"
    echo ""
    echo "  # Check status"
    echo "  $0 -p my-project --status"
    echo ""
    echo "  # Rollback"
    echo "  $0 -p my-project --rollback"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p) PROJECT_ID="$2"; shift 2 ;;
        -e) ENVIRONMENT="$2"; shift 2 ;;
        -r) REGION="$2"; shift 2 ;;
        -t) TELEGRAM_TOKEN="$2"; shift 2 ;;
        -s) WEBHOOK_SECRET="$2"; shift 2 ;;
        --build-only) BUILD_ONLY=true; shift ;;
        --deploy-only) DEPLOY_ONLY=true; shift ;;
        --status) STATUS_ONLY=true; shift ;;
        --rollback) ROLLBACK=true; shift ;;
        -h) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# Check required parameters
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: PROJECT_ID is required${NC}"
    usage
fi

if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo -e "${RED}❌ Error: ENVIRONMENT must be 'staging' or 'production'${NC}"
    exit 1
fi

# Derived values
SERVICE_NAME="telegramgroupie"
if [ "$ENVIRONMENT" != "production" ]; then
    SERVICE_NAME="telegramgroupie-${ENVIRONMENT}"
fi
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed and configured
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Configure gcloud
gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"

# Status check function
check_status() {
    echo -e "${BLUE}📊 Checking deployment status...${NC}"
    
    if gcloud run services describe "$SERVICE_NAME" --region="$REGION" &>/dev/null; then
        echo -e "${GREEN}✅ Service exists${NC}"
        
        # Get service details
        SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')
        REVISION=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.latestReadyRevisionName)')
        TRAFFIC=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.traffic[0].percent)')
        
        echo "🌐 Service URL: $SERVICE_URL"
        echo "📦 Current Revision: $REVISION"
        echo "🚦 Traffic: ${TRAFFIC}%"
        
        # Check health
        echo "🔍 Checking health..."
        if curl -sf "${SERVICE_URL}/" &>/dev/null; then
            echo -e "${GREEN}✅ Service is healthy${NC}"
        else
            echo -e "${YELLOW}⚠️  Service health check failed${NC}"
        fi
        
        # Show recent logs
        echo "📋 Recent logs:"
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" \
            --limit=5 --format="table(timestamp,textPayload)" 2>/dev/null || echo "No recent logs found"
    else
        echo -e "${YELLOW}⚠️  Service not found${NC}"
    fi
}

# Rollback function
rollback_deployment() {
    echo -e "${BLUE}🔄 Rolling back deployment...${NC}"
    
    # Get previous revision
    REVISIONS=$(gcloud run revisions list --service="$SERVICE_NAME" --region="$REGION" --format="value(metadata.name)" --limit=2)
    CURRENT_REVISION=$(echo "$REVISIONS" | head -n 1)
    PREVIOUS_REVISION=$(echo "$REVISIONS" | tail -n 1)
    
    if [ "$CURRENT_REVISION" = "$PREVIOUS_REVISION" ]; then
        echo -e "${YELLOW}⚠️  No previous revision found for rollback${NC}"
        exit 1
    fi
    
    echo "Rolling back from $CURRENT_REVISION to $PREVIOUS_REVISION"
    
    gcloud run services update-traffic "$SERVICE_NAME" \
        --region="$REGION" \
        --to-revisions="$PREVIOUS_REVISION=100"
    
    echo -e "${GREEN}✅ Rollback completed${NC}"
}

# Handle status and rollback operations
if [ "$STATUS_ONLY" = true ]; then
    check_status
    exit 0
fi

if [ "$ROLLBACK" = true ]; then
    rollback_deployment
    exit 0
fi

# For deployment operations, check tokens unless build-only
if [ "$BUILD_ONLY" = false ] && [ "$DEPLOY_ONLY" = false ]; then
    if [ -z "$TELEGRAM_TOKEN" ] || [ -z "$WEBHOOK_SECRET" ]; then
        echo -e "${RED}❌ Error: TELEGRAM_TOKEN and WEBHOOK_SECRET are required for deployment${NC}"
        echo "You can get these from environment variables or pass them as arguments"
        echo ""
        echo "Example:"
        echo "  export TELEGRAM_TOKEN='your-token'"
        echo "  export WEBHOOK_SECRET='your-secret'"
        echo "  $0 -p $PROJECT_ID"
        exit 1
    fi
elif [ "$DEPLOY_ONLY" = true ]; then
    if [ -z "$TELEGRAM_TOKEN" ] || [ -z "$WEBHOOK_SECRET" ]; then
        echo -e "${RED}❌ Error: TELEGRAM_TOKEN and WEBHOOK_SECRET are required for deployment${NC}"
        exit 1
    fi
fi

# Use environment variables if not provided as arguments
TELEGRAM_TOKEN=${TELEGRAM_TOKEN:-$TELEGRAM_TOKEN}
WEBHOOK_SECRET=${WEBHOOK_SECRET:-$WEBHOOK_SECRET}

echo -e "${BLUE}🚀 Deploying TelegramGroupie${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Service: ${SERVICE_NAME}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"
echo ""

# Build phase
if [ "$DEPLOY_ONLY" = false ]; then
    echo -e "${YELLOW}🏗️  Building Docker image...${NC}"
    
    # Run tests first
    echo "🧪 Running tests..."
    if ! pytest tests/ -v; then
        echo -e "${RED}❌ Tests failed. Aborting deployment.${NC}"
        exit 1
    fi
    
    # Build the image
    echo "🐳 Building Docker image..."
    gcloud builds submit --tag "$IMAGE_NAME" --timeout=10m
    
    if [ "$BUILD_ONLY" = true ]; then
        echo -e "${GREEN}✅ Build completed successfully!${NC}"
        echo "Image: $IMAGE_NAME"
        exit 0
    fi
fi

# Load environment configuration if it exists
ENV_FILE="${ENVIRONMENT}.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}📋 Loading environment configuration from ${ENV_FILE}...${NC}"
    source "$ENV_FILE"
fi

# Deployment phase
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"

# Prepare environment variables
ENV_VARS="GCP_PROJECT_ID=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},TELEGRAM_TOKEN=${TELEGRAM_TOKEN}"
ENV_VARS="${ENV_VARS},WEBHOOK_SECRET=${WEBHOOK_SECRET}"
ENV_VARS="${ENV_VARS},LOG_LEVEL=${LOG_LEVEL:-INFO}"

# Add KMS configuration if available
if [ -n "$KMS_LOCATION" ]; then
    ENV_VARS="${ENV_VARS},KMS_LOCATION=${KMS_LOCATION}"
fi
if [ -n "$KMS_KEY_RING" ]; then
    ENV_VARS="${ENV_VARS},KMS_KEY_RING=${KMS_KEY_RING}"
fi
if [ -n "$KMS_KEY_ID" ]; then
    ENV_VARS="${ENV_VARS},KMS_KEY_ID=${KMS_KEY_ID}"
fi

# Deploy to Cloud Run
gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --concurrency=80 \
    --max-instances=100 \
    --set-env-vars="$ENV_VARS"

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}🌐 Service URL: ${SERVICE_URL}${NC}"
echo ""

# Health check
echo -e "${YELLOW}🔍 Running health check...${NC}"
sleep 5  # Wait a moment for service to be ready

if curl -sf "${SERVICE_URL}/" &>/dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed - service may still be starting${NC}"
fi

# Show webhook setup instructions
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo ""
echo "1. Set up your Telegram webhook:"
echo "   curl -X POST \"https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook\" \\"
echo "        -d \"url=${SERVICE_URL}/webhook/${WEBHOOK_SECRET}\""
echo ""
echo "2. Test the webhook:"
echo "   curl \"${SERVICE_URL}/messages?limit=5\""
echo ""
echo "3. Monitor logs:"
echo "   gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\" --limit=50"
echo ""
echo "4. Monitor the service:"
echo "   $0 -p ${PROJECT_ID} -e ${ENVIRONMENT} --status"
echo ""
echo -e "${GREEN}🎉 TelegramGroupie is ready to process messages!${NC}" 