#!/bin/bash

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Ensure pip is up to date
echo "📦 Updating pip..."
pip install --upgrade pip

# Install or upgrade dependencies
echo "📦 Installing/upgrading dependencies..."
pip install -r requirements.txt

# Verify Flask is installed
if ! python -c "import flask" &> /dev/null; then
    echo -e "${RED}❌ Flask installation failed. Please check your requirements.txt${NC}"
    exit 1
fi

echo "🔍 Running tests..."
if pytest tests/; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Tests failed. Aborting build.${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate

# Get the project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No Google Cloud project ID found. Please run 'gcloud config set project YOUR_PROJECT_ID' first.${NC}"
    exit 1
fi

echo "🏗️  Building Docker image..."
IMAGE_NAME="gcr.io/${PROJECT_ID}/telegramgroupie"

# Build the image
gcloud builds submit --tag ${IMAGE_NAME}

echo "🚀 Deploying to Cloud Run..."
# Get the current region
REGION=$(gcloud config get-value compute/region 2>/dev/null || echo "us-central1")

# Deploy to Cloud Run
gcloud run deploy telegramgroupie \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe telegramgroupie --platform managed --region ${REGION} --format 'value(status.url)')

echo "🌐 Your service is available at: ${SERVICE_URL}"
echo "📝 Don't forget to set up your webhook with:"
echo "curl -X POST \"https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook\" -d \"url=${SERVICE_URL}/webhook/YOUR_WEBHOOK_SECRET\""
