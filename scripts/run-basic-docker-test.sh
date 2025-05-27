#!/bin/bash

# Basic Docker Integration Test
# This script demonstrates how to build and test your application in Docker

set -e

echo "🐳 Basic Docker Integration Test for TelegramGroupie"
echo "======================================================"

# Configuration
IMAGE_NAME="telegramgroupie:test"
CONTAINER_NAME="telegramgroupie-test"
TEST_PORT="8081"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

echo "🏗️ Building Docker image..."
docker build -t $IMAGE_NAME .

echo "🚀 Starting container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $TEST_PORT:8080 \
    -e APP_ENV=test \
    -e GCP_PROJECT_ID=test-project \
    -e WEBHOOK_SECRET=test-secret \
    $IMAGE_NAME

echo "⏳ Waiting for application to start..."
sleep 5

echo "🧪 Running basic integration tests..."

# Test 1: Health check
echo "  Testing health endpoint..."
if curl -s http://localhost:$TEST_PORT/healthz | grep -q "ok"; then
    echo "  ✅ Health check passed"
else
    echo "  ❌ Health check failed"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Test 2: Webhook endpoint (should return 404 for wrong secret)
echo "  Testing webhook endpoint..."
if curl -s -w "%{http_code}" http://localhost:$TEST_PORT/webhook/wrong-secret -X POST | grep -q "404"; then
    echo "  ✅ Webhook security test passed"
else
    echo "  ❌ Webhook security test failed"
    exit 1
fi

echo "🎉 Basic integration tests completed successfully!"
echo ""
echo "📊 Test Results:"
echo "  - Application builds correctly in Docker"
echo "  - Container starts successfully"
echo "  - Health endpoint responds"
echo "  - Basic API security works"
echo ""
echo "🔍 To debug, check logs with:"
echo "  docker logs $CONTAINER_NAME"
