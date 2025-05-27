# API Authorization

This document describes the authorization mechanism for the Telegram Bot Framework's message API endpoints.

## Overview

The message API endpoints (`/messages` and `/messages/batch`) are protected by API key authorization to ensure only authorized clients can access stored message data.

## Configuration

### Environment Variable

Set the `API_KEY` environment variable to enable authorization:

```bash
export API_KEY="your-secure-api-key-here"
```

**Important Security Notes:**
- Use a strong, randomly generated API key (minimum 32 characters)
- Never commit API keys to version control
- Rotate API keys regularly
- Use different API keys for different environments

### Example API Key Generation

```bash
# Generate a secure random API key
openssl rand -hex 32
# or
python -c "import secrets; print(secrets.token_hex(32))"
```

## Usage

### Making Authorized Requests

Include the API key in the `Authorization` header using the Bearer token format:

```bash
curl -H "Authorization: Bearer your-api-key-here" \
     https://your-app.com/messages
```

### Example Requests

#### Get Messages
```bash
curl -H "Authorization: Bearer abc123def456..." \
     -H "Content-Type: application/json" \
     "https://your-app.com/messages?chat_id=123&limit=50"
```

#### Process Messages Batch
```bash
curl -X POST \
     -H "Authorization: Bearer abc123def456..." \
     -H "Content-Type: application/json" \
     -d '{"chat_id": 123, "batch_size": 100}' \
     https://your-app.com/messages/batch
```

## Security Behavior

### When API_KEY is Configured
- All requests to `/messages` and `/messages/batch` require valid authorization
- Missing `Authorization` header returns `401 Unauthorized`
- Invalid header format returns `401 Unauthorized`
- Wrong API key returns `403 Forbidden`
- Valid API key allows access to the endpoint

### When API_KEY is NOT Configured
- **Warning**: API endpoints are unprotected
- All requests are allowed without authorization
- A warning is logged: "API_KEY not configured - API endpoints are unprotected"

## Error Responses

### 401 Unauthorized - Missing Authorization
```json
{
  "error": "Authorization required"
}
```

### 401 Unauthorized - Invalid Format
```json
{
  "error": "Invalid authorization format. Use 'Bearer <api_key>'"
}
```

### 403 Forbidden - Invalid API Key
```json
{
  "error": "Invalid API key"
}
```

## Protected Endpoints

The following endpoints require API key authorization:

- `GET /messages` - Retrieve messages with filtering and pagination
- `POST /messages/batch` - Process messages in batch

## Unprotected Endpoints

The following endpoints do NOT require authorization:

- `GET /healthz` - Health check endpoint
- `POST /webhook/<secret>` - Telegram webhook (protected by webhook secret)

## Implementation Details

### Authorization Flow

1. Extract `Authorization` header from request
2. Validate header format (`Bearer <token>`)
3. Compare provided token with configured `API_KEY`
4. Allow or deny access based on validation result

### Logging

The authorization system logs the following events:

- `⚠️ API_KEY not configured - API endpoints are unprotected`
- `🔒 Missing Authorization header`
- `🔒 Invalid Authorization header format`
- `🔒 Invalid API key provided: [first 8 chars]...`
- `✅ API key validation successful`

## Best Practices

1. **Use Environment Variables**: Never hardcode API keys in source code
2. **Secure Storage**: Store API keys in secure secret management systems
3. **Regular Rotation**: Change API keys periodically
4. **Monitoring**: Monitor authorization logs for suspicious activity
5. **HTTPS Only**: Always use HTTPS in production to protect API keys in transit
6. **Principle of Least Privilege**: Use different API keys for different applications/users if needed

## Testing

The authorization system includes comprehensive tests covering:

- Missing authorization header
- Invalid authorization format
- Invalid API key
- Valid API key access
- Unprotected behavior when API_KEY not configured

Run tests with:
```bash
make test-unit
``` 