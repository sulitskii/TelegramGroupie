# Deployment Validation

This document describes the deployment validation system that tests the complete message flow from webhook to KMS encryption to API retrieval.

## Overview

The deployment validation script (`devops/scripts/validate-deployment.py`) performs end-to-end testing of a deployed Telegram Bot Framework instance by:

1. **Environment Validation** - Checking required configuration variables
2. **Health Check** - Verifying application is running and responsive
3. **API Authorization** - Testing that message endpoints are properly protected
4. **Webhook Processing** - Sending test Telegram webhook payloads
5. **KMS Encryption/Decryption** - Verifying messages are encrypted in KMS and can be decrypted
6. **Message API Retrieval** - Testing message retrieval through the REST API
7. **Batch Processing** - Validating batch message processing functionality

## Quick Start

### Validate Local Development Server
```bash
# Start local server and validate it
make validate-local
```

### Validate Remote Deployment
```bash
# Using environment file
make validate-deployment BASE_URL=https://your-app.com ENV_FILE=production.env

# Using current environment variables
export WEBHOOK_SECRET=your-webhook-secret
export API_KEY=your-api-key
make validate-deployment BASE_URL=https://your-app.com
```

### Validate with Detailed Report
```bash
# Generate JSON report with all test results
make validate-deployment-with-report BASE_URL=https://your-app.com ENV_FILE=production.env
```

## Usage Examples

### Production Validation
```bash
# Validate production deployment
make validate-production PRODUCTION_URL=https://your-production-app.com

# With custom environment file
make validate-deployment BASE_URL=https://your-app.com ENV_FILE=custom.env
```

### Staging Validation
```bash
# Validate staging deployment
make validate-staging STAGING_URL=https://staging-app.com
```

### CI/CD Integration
```bash
# In your CI/CD pipeline
python devops/scripts/validate-deployment.py \
  --env-file production.env \
  --base-url https://your-app.com \
  --output validation-report.json
```

## Environment Configuration

### Required Environment Variables

The validation script requires these environment variables (either in `.env` file or environment):

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
KMS_LOCATION=global
KMS_KEY_RING=your-key-ring-name
KMS_KEY_ID=your-key-id

# Application Secrets
WEBHOOK_SECRET=your-webhook-secret
API_KEY=your-api-key-for-message-endpoints
```

### Environment File Format

Create a `.env` file with your configuration:

```bash
# production.env
GCP_PROJECT_ID=tggrpie-stg
KMS_LOCATION=global
KMS_KEY_RING=telegram-messages
KMS_KEY_ID=message-key
WEBHOOK_SECRET=your-production-webhook-secret
API_KEY=your-production-api-key
```

## Validation Tests

### 1. Environment Configuration
- ✅ Checks all required environment variables are present
- ✅ Validates GCP project and KMS configuration
- ✅ Ensures webhook and API secrets are configured

### 2. Health Check
- ✅ Tests `GET /healthz` endpoint
- ✅ Verifies application is running and responsive
- ✅ Confirms basic connectivity

### 3. API Authorization
- ✅ Tests that message endpoints require authorization
- ✅ Verifies 401 response for missing API key
- ✅ Confirms API security is properly configured

### 4. Webhook Processing
- ✅ Sends realistic Telegram webhook payload
- ✅ Tests webhook secret validation
- ✅ Verifies message processing pipeline

### 5. KMS Encryption/Decryption
- ✅ Confirms messages are encrypted before storage
- ✅ Tests KMS key accessibility
- ✅ Validates decryption during API retrieval

### 6. Message API Retrieval
- ✅ Tests `GET /messages` endpoint with authorization
- ✅ Verifies test message can be retrieved and decrypted
- ✅ Confirms filtering and pagination work

### 7. Batch Processing
- ✅ Tests `POST /messages/batch` endpoint
- ✅ Validates batch processing functionality
- ✅ Confirms proper response format

## Test Flow

```
1. Generate unique test message
   ↓
2. Send webhook with test message
   ↓
3. Message encrypted with KMS and stored
   ↓
4. Retrieve message via API
   ↓
5. Verify message decrypted correctly
   ↓
6. Test batch processing
   ↓
7. Generate validation report
```

## Output Examples

### Successful Validation
```
🚀 Starting deployment validation for: https://your-app.com
📅 Timestamp: 2024-01-15T10:30:00.000Z
================================================================================
🧪 Test message: DEPLOYMENT_TEST_20240115_103000_abc12345
================================================================================
✅ PASS Environment Configuration: All required environment variables present
✅ PASS Health Check: Application is healthy
✅ PASS API Authorization: API correctly requires authorization
✅ PASS Webhook Processing: Message processed successfully (ID: 1234567)
✅ PASS Message Retrieval: Test message found and decrypted successfully
✅ PASS KMS Encryption/Decryption: Message was encrypted in KMS and decrypted for API response
✅ PASS Batch API: Batch processing successful, returned 5 messages
================================================================================
📊 VALIDATION SUMMARY
   Tests Passed: 7/7
   Success Rate: 100.0%
🎉 DEPLOYMENT VALIDATION SUCCESSFUL!
   All systems are working correctly.
```

### Failed Validation
```
🚀 Starting deployment validation for: https://broken-app.com
📅 Timestamp: 2024-01-15T10:30:00.000Z
================================================================================
🧪 Test message: DEPLOYMENT_TEST_20240115_103000_def67890
================================================================================
✅ PASS Environment Configuration: All required environment variables present
❌ FAIL Health Check: HTTP 503: Service Unavailable
❌ FAIL API Authorization: Request failed: Connection timeout
❌ FAIL Webhook Processing: HTTP 500: Internal Server Error
❌ FAIL Message Retrieval: Request failed: Connection timeout
❌ FAIL KMS Encryption/Decryption: Test not executed due to previous failures
❌ FAIL Batch API: Request failed: Connection timeout
================================================================================
📊 VALIDATION SUMMARY
   Tests Passed: 1/7
   Success Rate: 14.3%
⚠️  DEPLOYMENT VALIDATION FAILED!
   Some tests failed. Check the logs above for details.
```

## Report Generation

### JSON Report Format
```json
{
  "validation_successful": true,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "base_url": "https://your-app.com",
  "test_results": [
    {
      "test": "Environment Configuration",
      "success": true,
      "message": "All required environment variables present",
      "details": {},
      "timestamp": "2024-01-15T10:30:01.000Z"
    },
    {
      "test": "Health Check",
      "success": true,
      "message": "Application is healthy",
      "details": {},
      "timestamp": "2024-01-15T10:30:02.000Z"
    }
  ]
}
```

### Report Storage
Reports are automatically saved to `reports/deployment-validation-YYYYMMDD_HHMMSS.json` when using the `--output` flag or `validate-deployment-with-report` make target.

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Validate Deployment
  run: |
    python devops/scripts/validate-deployment.py \
      --env-file production.env \
      --base-url ${{ secrets.PRODUCTION_URL }} \
      --output validation-report.json
  
- name: Upload Validation Report
  uses: actions/upload-artifact@v3
  with:
    name: deployment-validation-report
    path: validation-report.json
```

### Docker Integration
```bash
# Run validation in Docker container
docker run --rm \
  -v $(pwd):/app \
  -w /app \
  python:3.11 \
  python devops/scripts/validate-deployment.py \
    --env-file production.env \
    --base-url https://your-app.com
```

## Troubleshooting

### Common Issues

#### 1. Missing Environment Variables
```
❌ FAIL Environment Configuration: Missing required variables: WEBHOOK_SECRET, API_KEY
```
**Solution**: Ensure all required variables are set in your `.env` file or environment.

#### 2. Health Check Failure
```
❌ FAIL Health Check: HTTP 503: Service Unavailable
```
**Solution**: Check if the application is running and accessible at the specified URL.

#### 3. API Authorization Issues
```
❌ FAIL API Authorization: API is unprotected (no API_KEY configured)
```
**Solution**: Set the `API_KEY` environment variable in your deployment.

#### 4. Webhook Processing Failure
```
❌ FAIL Webhook Processing: HTTP 500: Internal Server Error
```
**Solution**: Check application logs for errors in webhook processing or KMS access.

#### 5. Message Retrieval Issues
```
❌ FAIL Message Retrieval: Test message not found in API response
```
**Solution**: Verify KMS encryption/decryption is working and database connectivity.

### Debug Mode

For detailed debugging, run the script directly with verbose output:

```bash
python devops/scripts/validate-deployment.py \
  --env-file production.env \
  --base-url https://your-app.com \
  --output debug-report.json
```

## Security Considerations

### Test Message Cleanup
- Test messages are generated with unique timestamps and random suffixes
- Messages are stored in the same database as production data
- Consider implementing cleanup for test messages in production environments

### Sensitive Data
- The validation script does not expose sensitive configuration values
- API keys and secrets are masked in logs
- Test payloads use realistic but non-sensitive data

### Network Security
- All requests use HTTPS in production
- Webhook secrets are validated properly
- API authorization is tested thoroughly

## Best Practices

1. **Regular Validation**: Run validation after each deployment
2. **Environment Isolation**: Use separate `.env` files for different environments
3. **Report Archival**: Save validation reports for audit trails
4. **Automated Testing**: Integrate validation into CI/CD pipelines
5. **Monitoring Integration**: Alert on validation failures
6. **Cleanup Strategy**: Implement cleanup for test messages in production

## Command Reference

### Make Targets
- `make validate-local` - Validate local development server
- `make validate-deployment BASE_URL=<url> [ENV_FILE=<file>]` - Validate any deployment
- `make validate-deployment-with-report BASE_URL=<url> [ENV_FILE=<file>]` - Validate with JSON report
- `make validate-staging STAGING_URL=<url>` - Validate staging environment
- `make validate-production PRODUCTION_URL=<url>` - Validate production environment

### Script Options
- `--env-file <path>` - Path to environment configuration file
- `--base-url <url>` - Base URL of the deployed application
- `--output <path>` - Output file for JSON test results
- `--help` - Show help message and examples

## Related Documentation

- [API Authorization](API_AUTHORIZATION.md) - API security configuration
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [KMS Key Protection](KMS_KEY_PROTECTION.md) - KMS security guidelines
- [Architecture](ARCHITECTURE.md) - System architecture overview 