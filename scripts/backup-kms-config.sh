#!/bin/bash

# 💾 KMS Configuration & Data Backup Script
# This script backs up KMS key metadata, IAM policies, and Firestore data
# 
# ⚠️ NOTE: The actual KMS key material cannot be backed up (managed by Google)
# This script backs up everything else needed for disaster recovery

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
BACKUP_BUCKET=""
LOCAL_BACKUP=true

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p PROJECT_ID     GCP Project ID (default: $PROJECT_ID)"
    echo "  -k KEY_NAME       KMS Key name (default: $KEY_NAME)"
    echo "  -r KEYRING        KMS Keyring name (default: $KEYRING)"
    echo "  -l LOCATION       KMS Location (default: $LOCATION)"
    echo "  -b BUCKET         GCS bucket for backups (optional)"
    echo "  --local-only      Only create local backups (default)"
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
while [[ $# -gt 0 ]]; do
    case $1 in
        -p) PROJECT_ID="$2"; shift 2 ;;
        -k) KEY_NAME="$2"; shift 2 ;;
        -r) KEYRING="$2"; shift 2 ;;
        -l) LOCATION="$2"; shift 2 ;;
        -b) BACKUP_BUCKET="$2"; LOCAL_BACKUP=false; shift 2 ;;
        --local-only) LOCAL_BACKUP=true; shift ;;
        -h) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

echo -e "${BLUE}💾 TelegramGroupie KMS & Data Backup${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Key: ${KEYRING}/${KEY_NAME}${NC}"
echo -e "${BLUE}Location: ${LOCATION}${NC}"
echo ""

# Create backup directory
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="backups/kms-config/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}📁 Creating backup directory: $BACKUP_DIR${NC}"

# Check if gcloud is installed and configured
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ ERROR: gcloud CLI is not installed${NC}"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID" > /dev/null 2>&1

echo -e "${YELLOW}1. Backing up KMS key configuration...${NC}"
if gcloud kms keys describe "$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" \
    --format=yaml > "$BACKUP_DIR/key-config.yaml"; then
    echo -e "${GREEN}✅ KMS key configuration backed up${NC}"
else
    echo -e "${RED}❌ Failed to backup KMS key configuration${NC}"
    exit 1
fi

echo -e "${YELLOW}2. Backing up KMS key IAM policies...${NC}"
if gcloud kms keys get-iam-policy "$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" \
    --format=yaml > "$BACKUP_DIR/key-iam-policy.yaml"; then
    echo -e "${GREEN}✅ KMS key IAM policies backed up${NC}"
else
    echo -e "${YELLOW}⚠️  Could not backup IAM policies (may require additional permissions)${NC}"
fi

echo -e "${YELLOW}3. Backing up KMS keyring configuration...${NC}"
if gcloud kms keyrings describe "$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" \
    --format=yaml > "$BACKUP_DIR/keyring-config.yaml"; then
    echo -e "${GREEN}✅ KMS keyring configuration backed up${NC}"
else
    echo -e "${RED}❌ Failed to backup KMS keyring configuration${NC}"
fi

echo -e "${YELLOW}4. Backing up key versions...${NC}"
if gcloud kms keys versions list \
    --key="$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" \
    --format=yaml > "$BACKUP_DIR/key-versions.yaml"; then
    echo -e "${GREEN}✅ KMS key versions backed up${NC}"
else
    echo -e "${RED}❌ Failed to backup KMS key versions${NC}"
fi

echo -e "${YELLOW}5. Backing up project IAM policies...${NC}"
if gcloud projects get-iam-policy "$PROJECT_ID" \
    --format=yaml > "$BACKUP_DIR/project-iam-policy.yaml"; then
    echo -e "${GREEN}✅ Project IAM policies backed up${NC}"
else
    echo -e "${YELLOW}⚠️  Could not backup project IAM policies${NC}"
fi

echo -e "${YELLOW}6. Creating backup metadata...${NC}"
cat > "$BACKUP_DIR/backup-metadata.yaml" << EOF
# TelegramGroupie KMS Backup Metadata
# Created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

backup_info:
  timestamp: "$TIMESTAMP"
  project_id: "$PROJECT_ID"
  kms_location: "$LOCATION"
  kms_keyring: "$KEYRING"
  kms_key_name: "$KEY_NAME"
  key_path: "projects/$PROJECT_ID/locations/$LOCATION/keyRings/$KEYRING/cryptoKeys/$KEY_NAME"
  
backup_contents:
  - key-config.yaml         # KMS key configuration
  - key-iam-policy.yaml     # Key-specific IAM policies
  - keyring-config.yaml     # KMS keyring configuration
  - key-versions.yaml       # Key version history
  - project-iam-policy.yaml # Project IAM policies
  - backup-metadata.yaml    # This metadata file

recovery_notes: |
  This backup contains KMS key metadata and configuration.
  The actual key material is managed by Google and cannot be backed up.
  
  To restore:
  1. Recreate the keyring if needed
  2. The key itself cannot be recreated - use the existing key
  3. Apply IAM policies from the backup files
  4. Update application configuration with correct key paths
  
warnings: |
  - The actual encryption key material cannot be backed up or restored
  - If the original key is deleted, encrypted data is permanently lost
  - This backup only helps with configuration restoration
EOF

echo -e "${GREEN}✅ Backup metadata created${NC}"

echo -e "${YELLOW}7. Backing up Firestore data (encrypted messages)...${NC}"
if [ "$LOCAL_BACKUP" = true ]; then
    echo -e "${YELLOW}   Note: For Firestore backup, you need a GCS bucket.${NC}"
    echo -e "${YELLOW}   Run with -b gs://your-backup-bucket to enable Firestore backup.${NC}"
else
    if gcloud firestore export "gs://$BACKUP_BUCKET/firestore/$TIMESTAMP" \
        --collection-ids=messages \
        --project="$PROJECT_ID"; then
        echo -e "${GREEN}✅ Firestore data exported to gs://$BACKUP_BUCKET/firestore/$TIMESTAMP${NC}"
        
        # Add Firestore backup info to metadata
        echo "  firestore_backup: \"gs://$BACKUP_BUCKET/firestore/$TIMESTAMP\"" >> "$BACKUP_DIR/backup-metadata.yaml"
    else
        echo -e "${RED}❌ Failed to backup Firestore data${NC}"
    fi
fi

# Upload to GCS if bucket specified
if [ "$LOCAL_BACKUP" = false ] && [ -n "$BACKUP_BUCKET" ]; then
    echo -e "${YELLOW}8. Uploading backup to GCS...${NC}"
    if gsutil -m cp -r "$BACKUP_DIR" "gs://$BACKUP_BUCKET/kms-config/"; then
        echo -e "${GREEN}✅ Backup uploaded to gs://$BACKUP_BUCKET/kms-config/$TIMESTAMP${NC}"
    else
        echo -e "${RED}❌ Failed to upload backup to GCS${NC}"
    fi
fi

# Create restore script
echo -e "${YELLOW}9. Creating restore script...${NC}"
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
# KMS Configuration Restore Script
# Generated automatically during backup

set -e

echo "🔄 TelegramGroupie KMS Configuration Restore"
echo "⚠️  WARNING: This script only restores configuration, not the actual key material!"
echo ""

# Load metadata
source ./backup-metadata.yaml 2>/dev/null || echo "Could not load metadata"

echo "This would restore configuration for:"
echo "  Project: $PROJECT_ID"
echo "  Keyring: $KEYRING"  
echo "  Key: $KEY_NAME"
echo ""

echo "❌ IMPORTANT: The actual KMS key cannot be restored from backup!"
echo "   If the original key is lost, all encrypted data is permanently unrecoverable."
echo ""
echo "To apply IAM policies from this backup:"
echo "  gcloud kms keys set-iam-policy $KEY_NAME \\"
echo "    --keyring=$KEYRING \\"
echo "    --location=$LOCATION \\"
echo "    --policy-file=key-iam-policy.yaml"
echo ""
EOF

chmod +x "$BACKUP_DIR/restore.sh"
echo -e "${GREEN}✅ Restore script created${NC}"

echo ""
echo -e "${GREEN}🎉 Backup completed successfully!${NC}"
echo -e "${BLUE}Backup location: $BACKUP_DIR${NC}"
echo ""
echo -e "${BLUE}Backup contents:${NC}"
ls -la "$BACKUP_DIR"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "${YELLOW}1. Store this backup in a secure location${NC}"
echo -e "${YELLOW}2. Test the restore procedure periodically${NC}"
echo -e "${YELLOW}3. Remember: KMS key material cannot be backed up!${NC}"

# Create a summary file
echo "Backup completed: $(date)" > backups/last-backup.txt
echo "Location: $BACKUP_DIR" >> backups/last-backup.txt

exit 0 