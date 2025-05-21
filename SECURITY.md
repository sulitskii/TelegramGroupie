# Security Policy

## Supported Versions

This project follows semantic versioning. We currently support the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Features

This project implements several security measures:

1. **Webhook Security**
   - All webhook endpoints are protected with a secret path
   - HTTPS is enforced through Google Cloud Run
   - Webhook secret is required for all incoming requests

2. **Environment Variables**
   - Sensitive data (TELEGRAM_TOKEN, WEBHOOK_SECRET) are stored as environment variables
   - Never committed to source control
   - Securely managed in Google Cloud Run

3. **Dependencies**
   - Regular security updates through requirements.txt
   - Python 3.10+ for latest security features
   - All dependencies are pinned to specific versions

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **Do Not** disclose the vulnerability publicly
2. Email the security details to [your-email@example.com]
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

### Response Time
- We will acknowledge receipt of your report within 48 hours
- We will provide a more detailed response within 7 days
- We will keep you informed of our progress

### What to Expect
- If the vulnerability is accepted:
  - We will work on a fix
  - You will be notified when the fix is deployed
  - You will be credited in the security advisory (if desired)
- If the vulnerability is declined:
  - We will provide a detailed explanation
  - You may appeal the decision

## Best Practices

When using this bot:

1. **Token Security**
   - Never share your Telegram bot token
   - Rotate the token if compromised
   - Use environment variables for token storage

2. **Webhook Configuration**
   - Use a strong, random WEBHOOK_SECRET
   - Keep the webhook URL private
   - Regularly rotate the webhook secret

3. **Cloud Run Security**
   - Restrict ingress to Telegram IPs when possible
   - Use the latest Python runtime
   - Keep dependencies updated

## Updates

Security updates will be released as patch versions (1.0.x). We recommend:
- Always using the latest patch version
- Regularly checking for updates
- Testing updates in a staging environment before deployment
