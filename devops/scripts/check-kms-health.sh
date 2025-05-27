#!/bin/bash

# 🔐 KMS Key Health Check Script
# This script verifies that the TelegramGroupie KMS key is accessible and functional
# 
# ⚠️ CRITICAL: This key protects ALL encrypted messages. Never delete it!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
PROJECT_ID="${GCP_PROJECT_ID:-tggrpie-stg}"
KEY_NAME="${KMS_KEY_ID:-message-key}"
KEYRING="${KMS_KEY_RING:-telegram-messages}"
LOCATION="${KMS_LOCATION:-global}"

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p PROJECT_ID     GCP Project ID (default: $PROJECT_ID)"
    echo "  -k KEY_NAME       KMS Key name (default: $KEY_NAME)"
    echo "  -r KEYRING        KMS Keyring name (default: $KEYRING)"
    echo "  -l LOCATION       KMS Location (default: $LOCATION)"
    echo "  -v                Verbose output"
    echo "  -h                Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  GCP_PROJECT_ID    Override project ID"
    echo "  KMS_KEY_ID        Override key name"
    echo "  KMS_KEY_RING      Override keyring name"
    echo "  KMS_LOCATION      Override location"
    exit 1
}

# Parse command line arguments
VERBOSE=false
while getopts "p:k:r:l:vh" opt; do
    case $opt in
        p) PROJECT_ID="$OPTARG" ;;
        k) KEY_NAME="$OPTARG" ;;
        r) KEYRING="$OPTARG" ;;
        l) LOCATION="$OPTARG" ;;
        v) VERBOSE=true ;;
        h) usage ;;
        *) usage ;;
    esac
done

echo -e "${BLUE}🔐 TelegramGroupie KMS Health Check${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Key: ${KEYRING}/${KEY_NAME}${NC}"
echo -e "${BLUE}Location: ${LOCATION}${NC}"
echo ""

# Function to log verbose output
log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${YELLOW}[VERBOSE] $1${NC}"
    fi
}

# Check if gcloud is installed and configured
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ CRITICAL: gcloud CLI is not installed${NC}"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ CRITICAL: Not authenticated with gcloud${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

log_verbose "Setting gcloud project to $PROJECT_ID"
gcloud config set project "$PROJECT_ID" > /dev/null 2>&1

echo -e "${YELLOW}1. Testing key accessibility...${NC}"
if gcloud kms keys describe "$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ KMS key is accessible${NC}"
else
    echo -e "${RED}❌ CRITICAL: KMS key not accessible!${NC}"
    echo -e "${RED}   Key: projects/$PROJECT_ID/locations/$LOCATION/keyRings/$KEYRING/cryptoKeys/$KEY_NAME${NC}"
    exit 1
fi

echo -e "${YELLOW}2. Checking key state and protection...${NC}"
KEY_STATE=$(gcloud kms keys describe "$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" \
    --format="value(primary.state)")

DESTROY_DURATION=$(gcloud kms keys describe "$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" \
    --format="value(destroyScheduledDuration)")

log_verbose "Key state: $KEY_STATE"
log_verbose "Destroy protection: $DESTROY_DURATION"

if [ "$KEY_STATE" = "ENABLED" ]; then
    echo -e "${GREEN}✅ Key state is ENABLED${NC}"
elif [ "$KEY_STATE" = "DESTROY_SCHEDULED" ]; then
    echo -e "${RED}❌ CRITICAL: Key is scheduled for destruction!${NC}"
    echo -e "${RED}   Run immediately: gcloud kms keys restore $KEY_NAME --keyring=$KEYRING --location=$LOCATION${NC}"
    exit 1
else
    echo -e "${RED}❌ WARNING: Key state is $KEY_STATE${NC}"
    exit 1
fi

if [ -n "$DESTROY_DURATION" ]; then
    echo -e "${GREEN}✅ Key has destruction protection (${DESTROY_DURATION})${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING: No destruction protection configured${NC}"
fi

echo -e "${YELLOW}3. Testing encryption capability...${NC}"
TEST_DATA="health-check-$(date +%s)"
TEMP_DIR=$(mktemp -d)
PLAINTEXT_FILE="$TEMP_DIR/test-plain.txt"
CIPHERTEXT_FILE="$TEMP_DIR/test-cipher.bin"
DECRYPTED_FILE="$TEMP_DIR/test-decrypted.txt"

log_verbose "Created temp directory: $TEMP_DIR"
echo "$TEST_DATA" > "$PLAINTEXT_FILE"

# Test encryption
if gcloud kms encrypt \
    --plaintext-file="$PLAINTEXT_FILE" \
    --ciphertext-file="$CIPHERTEXT_FILE" \
    --key="$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ KMS encryption working${NC}"
    log_verbose "Successfully encrypted test data"
else
    echo -e "${RED}❌ CRITICAL: KMS encryption failed!${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${YELLOW}4. Testing decryption capability...${NC}"
# Test decryption
if gcloud kms decrypt \
    --ciphertext-file="$CIPHERTEXT_FILE" \
    --plaintext-file="$DECRYPTED_FILE" \
    --key="$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" > /dev/null 2>&1; then
    
    DECRYPTED_DATA=$(cat "$DECRYPTED_FILE")
    if [ "$DECRYPTED_DATA" = "$TEST_DATA" ]; then
        echo -e "${GREEN}✅ KMS decryption working${NC}"
        log_verbose "Successfully decrypted and verified test data"
    else
        echo -e "${RED}❌ CRITICAL: Decrypted data doesn't match!${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
else
    echo -e "${RED}❌ CRITICAL: KMS decryption failed!${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo -e "${YELLOW}5. Checking IAM permissions...${NC}"
# Check if the current user/service account has necessary permissions
if gcloud kms keys get-iam-policy "$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ IAM permissions accessible${NC}"
    log_verbose "IAM policy retrieval successful"
else
    echo -e "${YELLOW}⚠️  WARNING: Cannot access IAM policies (may be normal for service accounts)${NC}"
fi

echo -e "${YELLOW}6. Checking key version history...${NC}"
VERSION_COUNT=$(gcloud kms keys versions list \
    --key="$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" \
    --format="value(name)" | wc -l)

log_verbose "Found $VERSION_COUNT key versions"
if [ "$VERSION_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Key has $VERSION_COUNT version(s)${NC}"
else
    echo -e "${RED}❌ CRITICAL: No key versions found!${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"
log_verbose "Cleaned up temporary files"

echo ""
echo -e "${GREEN}🎉 KMS Key Health Check PASSED${NC}"
echo -e "${BLUE}Key is fully functional and protected${NC}"

# Output summary for monitoring systems
if [ "$VERBOSE" = true ]; then
    echo ""
    echo -e "${BLUE}=== HEALTH CHECK SUMMARY ===${NC}"
    echo "Project: $PROJECT_ID"
    echo "Key: $KEYRING/$KEY_NAME"
    echo "Location: $LOCATION"
    echo "State: $KEY_STATE"
    echo "Protection: $DESTROY_DURATION"
    echo "Versions: $VERSION_COUNT"
    echo "Status: HEALTHY"
    echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
fi

exit 0 