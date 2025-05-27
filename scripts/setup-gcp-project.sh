#!/bin/bash

# TelegramGroupie GCP Project Setup Script
# This script sets up a new GCP project with all required services and resources
#
# ⚠️ CRITICAL: This script creates KMS encryption keys that protect ALL message data.
# Once created, NEVER delete these keys or all encrypted messages become unreadable!
# The keys have 30-day destruction protection, but prevention is critical.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REGION="us-central1"
KMS_LOCATION="global"
ENVIRONMENT="production"

# Usage function
usage() {
    echo "Usage: $0 -p PROJECT_ID [-r REGION] [-e ENVIRONMENT] [-l KMS_LOCATION]"
    echo ""
    echo "Options:"
    echo "  -p PROJECT_ID     Google Cloud Project ID (required)"
    echo "  -r REGION         GCP region (default: us-central1)"
    echo "  -e ENVIRONMENT    Environment: staging|production (default: production)"
    echo "  -l KMS_LOCATION   KMS location (default: global)"
    echo "  -h                Show this help"
    echo ""
    echo "Example:"
    echo "  $0 -p my-telegramgroupie-prod -e production"
    echo "  $0 -p my-telegramgroupie-staging -e staging -r europe-west1"
    exit 1
}

# Parse command line arguments
while getopts "p:r:e:l:h" opt; do
    case $opt in
        p) PROJECT_ID="$OPTARG" ;;
        r) REGION="$OPTARG" ;;
        e) ENVIRONMENT="$OPTARG" ;;
        l) KMS_LOCATION="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
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
KMS_KEY_RING="telegramgroupie-messages-${ENVIRONMENT}"
KMS_KEY_ID="message-key-${ENVIRONMENT}"
SERVICE_NAME="telegramgroupie"
if [ "$ENVIRONMENT" != "production" ]; then
    SERVICE_NAME="telegramgroupie-${ENVIRONMENT}"
fi

echo -e "${BLUE}🚀 Setting up TelegramGroupie on GCP${NC}"
echo -e "${BLUE}Project ID: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"
echo -e "${BLUE}KMS Location: ${KMS_LOCATION}${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Error: Not authenticated with gcloud${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

echo -e "${YELLOW}⚙️  Configuring gcloud...${NC}"
gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"

echo -e "${YELLOW}🔌 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudkms.googleapis.com \
    firestore.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com

echo -e "${YELLOW}🔥 Setting up Firestore...${NC}"
# Check if Firestore is already initialized
if ! gcloud firestore databases list --format="value(name)" | grep -q "$PROJECT_ID"; then
    echo "Initializing Firestore in native mode..."
    gcloud firestore databases create --region="$REGION"
else
    echo "Firestore already initialized"
fi

echo -e "${YELLOW}🔐 Setting up Cloud KMS...${NC}"
# Create KMS key ring
if ! gcloud kms keyrings describe "$KMS_KEY_RING" --location="$KMS_LOCATION" &>/dev/null; then
    echo "Creating KMS key ring: $KMS_KEY_RING"
    gcloud kms keyrings create "$KMS_KEY_RING" --location="$KMS_LOCATION"
else
    echo "KMS key ring already exists: $KMS_KEY_RING"
fi

# Create KMS key
if ! gcloud kms keys describe "$KMS_KEY_ID" --keyring="$KMS_KEY_RING" --location="$KMS_LOCATION" &>/dev/null; then
    echo "Creating KMS key: $KMS_KEY_ID"
    gcloud kms keys create "$KMS_KEY_ID" \
        --keyring="$KMS_KEY_RING" \
        --location="$KMS_LOCATION" \
        --purpose=encryption
    
    echo -e "${RED}🚨 CRITICAL WARNING:${NC}"
    echo -e "${RED}   The KMS key '$KMS_KEY_ID' was just created.${NC}"
    echo -e "${RED}   NEVER delete this key or all encrypted messages become unreadable!${NC}"
    echo -e "${RED}   Read docs/KMS_KEY_PROTECTION.md for protection guidelines.${NC}"
    echo ""
else
    echo "KMS key already exists: $KMS_KEY_ID"
fi

echo -e "${YELLOW}👤 Setting up IAM permissions...${NC}"
# Get the default compute service account
COMPUTE_SA="${PROJECT_ID//[^0-9]/}-compute@developer.gserviceaccount.com"
echo "Setting up permissions for service account: $COMPUTE_SA"

# Grant KMS permissions
gcloud kms keys add-iam-policy-binding "$KMS_KEY_ID" \
    --keyring="$KMS_KEY_RING" \
    --location="$KMS_LOCATION" \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"

# Grant Firestore permissions
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/datastore.user"

# Grant logging permissions
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/logging.logWriter"

echo -e "${YELLOW}📝 Creating Firestore indexes...${NC}"
# Create composite indexes for efficient queries
cat > firestore.indexes.json << EOF
{
  "indexes": [
    {
      "collectionGroup": "messages",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "chat_id",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "messages",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "user_id",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "messages",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "chat_id",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "user_id",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "messages",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "type",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    }
  ]
}
EOF

gcloud firestore indexes composite create --file-path=firestore.indexes.json

echo -e "${YELLOW}📋 Creating environment configuration...${NC}"
# Create environment variables file
cat > "${ENVIRONMENT}.env" << EOF
# TelegramGroupie Environment Configuration
# Environment: ${ENVIRONMENT}
# Project: ${PROJECT_ID}

# Required Environment Variables
GCP_PROJECT_ID=${PROJECT_ID}
KMS_LOCATION=${KMS_LOCATION}
KMS_KEY_RING=${KMS_KEY_RING}
KMS_KEY_ID=${KMS_KEY_ID}
LOG_LEVEL=INFO

# Deployment Configuration
SERVICE_NAME=${SERVICE_NAME}
REGION=${REGION}
PORT=8080

# These must be set separately for security:
# TELEGRAM_TOKEN=your-telegram-bot-token
# WEBHOOK_SECRET=your-webhook-secret
EOF

echo -e "${GREEN}✅ GCP Project setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "1. Set your secrets:"
echo "   export TELEGRAM_TOKEN='your-telegram-bot-token'"
echo "   export WEBHOOK_SECRET='your-webhook-secret'"
echo ""
echo "2. Deploy the application:"
echo "   ./scripts/deploy.sh -p ${PROJECT_ID} -e ${ENVIRONMENT}"
echo ""
echo "3. Or manually deploy:"
echo "   gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
echo "   gcloud run deploy ${SERVICE_NAME} \\"
echo "     --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \\"
echo "     --region ${REGION} \\"
echo "     --allow-unauthenticated \\"
echo "     --set-env-vars=\"\$(cat ${ENVIRONMENT}.env | grep -v '^#' | tr '\n' ',')\""
echo ""
echo -e "${BLUE}📁 Files created:${NC}"
echo "   - ${ENVIRONMENT}.env (environment configuration)"
echo "   - firestore.indexes.json (database indexes)"
echo ""
echo -e "${BLUE}🔗 Useful links:${NC}"
echo "   - Cloud Console: https://console.cloud.google.com/home/dashboard?project=${PROJECT_ID}"
echo "   - Cloud Run: https://console.cloud.google.com/run?project=${PROJECT_ID}"
echo "   - Firestore: https://console.cloud.google.com/firestore/data?project=${PROJECT_ID}"
echo "   - KMS: https://console.cloud.google.com/security/kms?project=${PROJECT_ID}" 