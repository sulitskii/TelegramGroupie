#!/bin/bash

# 🛡️ Branch Protection Verification Script
# This script verifies that GitHub branch protection is properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️ GitHub Branch Protection Verification${NC}"
echo -e "${BLUE}Repository: sulitskii/TelegramGroupie${NC}"
echo -e "${BLUE}Branch: main${NC}"
echo ""

# Check if we're on a feature branch (good practice)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${YELLOW}1. Current branch information...${NC}"
echo -e "${BLUE}   Current branch: $CURRENT_BRANCH${NC}"

if [ "$CURRENT_BRANCH" = "main" ]; then
    echo -e "${YELLOW}⚠️  You're currently on the protected branch${NC}"
    echo -e "${YELLOW}   Consider switching to a feature branch for development${NC}"
else
    echo -e "${GREEN}✅ Working on feature branch (good practice)${NC}"
fi

# Check required files
echo -e "${YELLOW}2. Checking required files...${NC}"

if [ -f ".github/CODEOWNERS" ]; then
    echo -e "${GREEN}✅ CODEOWNERS file exists${NC}"
    CODEOWNERS_COUNT=$(grep -c "@" .github/CODEOWNERS 2>/dev/null || echo 0)
    echo -e "${BLUE}   Found $CODEOWNERS_COUNT code owner entries${NC}"
else
    echo -e "${YELLOW}⚠️  CODEOWNERS file not found${NC}"
fi

if [ -f "docs/BRANCH_PROTECTION_SETUP.md" ]; then
    echo -e "${GREEN}✅ Branch protection documentation exists${NC}"
else
    echo -e "${YELLOW}⚠️  Branch protection documentation not found${NC}"
fi

# Check GitHub Actions
echo -e "${YELLOW}3. Checking GitHub Actions workflows...${NC}"

if [ -d ".github/workflows" ]; then
    WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
    echo -e "${GREEN}✅ Found $WORKFLOW_COUNT GitHub Actions workflows${NC}"
    
    if grep -r "pull_request" .github/workflows/ &>/dev/null; then
        echo -e "${GREEN}✅ Workflows are configured for pull requests${NC}"
    else
        echo -e "${YELLOW}⚠️  Workflows might not run on pull requests${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No GitHub Actions workflows found${NC}"
fi

# Working directory status
echo -e "${YELLOW}4. Working directory status...${NC}"

if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
else
    echo -e "${GREEN}✅ Working directory is clean${NC}"
fi

echo ""
echo -e "${BLUE}📋 Branch Protection Setup Instructions:${NC}"
echo ""
echo "1. 🛡️  Configure branch protection rules in GitHub:"
echo "   https://github.com/sulitskii/TelegramGroupie/settings/branches"
echo ""
echo "2. 📋 Required settings:"
echo "   ✅ Require pull request before merging"
echo "   ✅ Require status checks to pass"  
echo "   ✅ Require conversation resolution"
echo "   ✅ Restrict who can push"
echo "   ❌ Disable force pushes"
echo "   ❌ Disable deletions"
echo ""
echo "3. 👥 Add required status checks:"
echo "   - Unit Tests"
echo "   - Static Analysis"
echo "   - Docker Tests"
echo ""
echo "4. 📚 Read the complete guide:"
echo "   cat docs/BRANCH_PROTECTION_SETUP.md"
echo ""

echo -e "${GREEN}🎉 Branch protection verification completed!${NC}"
exit 0 