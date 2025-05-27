# 🔐 **KMS Key Protection & Backup Guide**

> **⚠️ CRITICAL WARNING: The KMS encryption key is the MASTER KEY for all encrypted messages. If deleted, ALL stored messages become permanently unreadable with NO recovery possible.**

---

## 🚨 **Mandatory Key Protection Rules**

### ❌ **NEVER DELETE THE KMS KEY**
- **Never run** `gcloud kms keys destroy`
- **Never delete** the KMS keyring
- **Never delete** the GCP project without migrating keys first
- **Always verify** scripts before running them in production

### ✅ **Current Protection Status**
Your KMS key has the following built-in protections:

```bash
# Check current protection status
gcloud kms keys describe message-key \
    --keyring=telegram-messages \
    --location=global \
    --project=tggrpie-stg
```

**Protection Features:**
- **30-Day Destruction Protection**: Key cannot be immediately deleted
- **Scheduled Destruction**: Manual recovery possible within 30 days
- **Version History**: Multiple key versions maintained automatically  
- **IAM Protection**: Limited access via service accounts only

---

## 📋 **KMS Key Information**

### Current Production Key Details
```
Project: tggrpie-stg
Location: global  
Keyring: telegram-messages
Key ID: message-key
Algorithm: GOOGLE_SYMMETRIC_ENCRYPTION
Protection: SOFTWARE (30-day recovery)
Purpose: ENCRYPT_DECRYPT
```

### Key Path (for scripts)
```
projects/tggrpie-stg/locations/global/keyRings/telegram-messages/cryptoKeys/message-key
```

---

## 🛡️ **Additional Protection Measures**

### 1. **Enable Key Monitoring**

```bash
# Set up monitoring for key usage
gcloud logging sinks create kms-key-monitoring \
    bigquery.googleapis.com/projects/tggrpie-stg/datasets/security_logs \
    --log-filter='resource.type="kms_key" AND protoPayload.resourceName:"message-key"'

# Create alert for key access attempts
gcloud alpha monitoring policies create \
    --policy-from-file=kms-key-alert-policy.yaml
```

### 2. **IAM Protection Audit**

```bash
# Regularly audit who has access to the key
gcloud kms keys get-iam-policy message-key \
    --keyring=telegram-messages \
    --location=global \
    --project=tggrpie-stg

# Verify minimal permissions
gcloud projects get-iam-policy tggrpie-stg \
    --filter="bindings.role:roles/cloudkms.*"
```

### 3. **Key Health Check Script**

Create automated monitoring with `scripts/check-kms-health.sh`:

```bash
#!/bin/bash
# Check KMS key health and alert if issues

PROJECT_ID="tggrpie-stg"
KEY_NAME="message-key"
KEYRING="telegram-messages"
LOCATION="global"

# Test key accessibility
if gcloud kms keys describe "$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo "✅ KMS key is accessible"
else
    echo "❌ CRITICAL: KMS key not accessible!"
    exit 1
fi

# Test encryption/decryption capability
TEST_DATA="health-check-$(date +%s)"
if gcloud kms encrypt \
    --plaintext-file=<(echo "$TEST_DATA") \
    --ciphertext-file=/tmp/health-test.enc \
    --key="$KEY_NAME" \
    --keyring="$KEYRING" \
    --location="$LOCATION" \
    --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo "✅ KMS encryption working"
else
    echo "❌ CRITICAL: KMS encryption failed!"
    exit 1
fi

echo "✅ KMS key health check passed"
```

---

## 💾 **Backup & Recovery Strategies**

### Understanding KMS Backup Limitations

**❌ What CANNOT be backed up:**
- KMS keys themselves (managed by Google)
- Raw key material (never exposed)

**✅ What CAN be protected:**
- Encrypted data (Firestore documents)
- Key metadata and configuration
- IAM policies and permissions
- Application configuration

### 1. **Firestore Data Export**

```bash
# Regular backup of encrypted messages
gcloud firestore export gs://tggrpie-stg-backups/$(date +%Y-%m-%d) \
    --collection-ids=messages \
    --project=tggrpie-stg
```

### 2. **Key Configuration Backup**

```bash
# Export key metadata and IAM policies
mkdir -p backups/kms-config/$(date +%Y-%m-%d)

# Export key description
gcloud kms keys describe message-key \
    --keyring=telegram-messages \
    --location=global \
    --project=tggrpie-stg \
    --format=yaml > backups/kms-config/$(date +%Y-%m-%d)/key-config.yaml

# Export IAM policies
gcloud kms keys get-iam-policy message-key \
    --keyring=telegram-messages \
    --location=global \
    --project=tggrpie-stg \
    --format=yaml > backups/kms-config/$(date +%Y-%m-%d)/key-iam.yaml
```

### 3. **Infrastructure as Code**

Maintain KMS configuration in version control:

```yaml
# infrastructure/kms.yaml
apiVersion: kms.gcp.crossplane.io/v1alpha1
kind: CryptoKey
metadata:
  name: message-key
spec:
  forProvider:
    keyRing: telegram-messages
    location: global
    purpose: ENCRYPT_DECRYPT
    versionTemplate:
      algorithm: GOOGLE_SYMMETRIC_ENCRYPTION
      protectionLevel: SOFTWARE
    destroyScheduledDuration: 2592000s  # 30 days
```

---

## 🔄 **Recovery Procedures**

### If Key is Accidentally Scheduled for Destruction

```bash
# Check if key is scheduled for destruction
gcloud kms keys describe message-key \
    --keyring=telegram-messages \
    --location=global \
    --project=tggrpie-stg \
    --format="value(state)"

# If state is DESTROY_SCHEDULED, restore immediately:
gcloud kms keys restore message-key \
    --keyring=telegram-messages \
    --location=global \
    --project=tggrpie-stg
```

### If Key is Permanently Lost (DISASTER RECOVERY)

**⚠️ WARNING: This scenario means ALL encrypted messages are permanently lost.**

1. **Create new KMS key with different name**
2. **Update application configuration**
3. **Accept that old messages cannot be decrypted**
4. **All new messages will use the new key**

```bash
# Create emergency replacement key
gcloud kms keys create message-key-recovery \
    --keyring=telegram-messages \
    --location=global \
    --purpose=encryption \
    --project=tggrpie-stg

# Update environment variables
export KMS_KEY_ID="message-key-recovery"
```

---

## 📝 **Regular Maintenance Tasks**

### Weekly Tasks
```bash
# 1. Health check
./scripts/check-kms-health.sh

# 2. Backup Firestore data
gcloud firestore export gs://tggrpie-stg-backups/weekly/$(date +%Y-%m-%d)

# 3. Audit key access
gcloud logging read 'resource.type="kms_key"' --limit=100
```

### Monthly Tasks
```bash
# 1. Review IAM permissions
gcloud kms keys get-iam-policy message-key --keyring=telegram-messages --location=global

# 2. Test disaster recovery procedure
./scripts/test-key-recovery.sh

# 3. Update documentation if configuration changes
```

### Quarterly Tasks
```bash
# 1. Review key rotation policy (if needed)
# 2. Audit all scripts for KMS references
# 3. Test backup/restore procedures
# 4. Review monitoring and alerting
```

---

## 🚨 **Emergency Contacts & Procedures**

### If Key Issues Are Detected:

1. **Immediate Actions:**
   - Stop all deployments
   - Check key status: `gcloud kms keys describe ...`
   - Review recent changes in Cloud Console
   - Check monitoring logs

2. **Escalation:**
   - Contact Google Cloud Support (if key is lost)
   - Inform stakeholders about potential data impact
   - Document incident for future prevention

3. **Communication:**
   - Notify users that message history may be affected
   - Provide timeline for resolution
   - Document lessons learned

---

## 📚 **Additional Resources**

- [Google Cloud KMS Documentation](https://cloud.google.com/kms/docs)
- [KMS Key Lifecycle Management](https://cloud.google.com/kms/docs/key-lifecycle)
- [Cloud KMS Best Practices](https://cloud.google.com/kms/docs/best-practices)
- [Disaster Recovery Planning](https://cloud.google.com/solutions/dr-scenarios-planning-guide)

---

## ✅ **Verification Checklist**

Before any major changes, verify:

- [ ] KMS key is accessible and healthy
- [ ] Recent backup exists (< 7 days old)  
- [ ] IAM permissions are correct
- [ ] Monitoring is active
- [ ] Documentation is up-to-date
- [ ] Team is aware of protection requirements

**Remember: The KMS key is irreplaceable. Treat it with the highest level of care.** 