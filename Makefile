# Telegram Bot Framework - Makefile
# Build automation and development commands for the Telegram bot framework

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[1;37m
NC := \033[0m # No Color

# Project configuration
PROJECT_NAME := telegram-bot-framework
DOCKER_IMAGE := $(PROJECT_NAME)
DOCKER_TAG := latest
COMPOSE_PROJECT_NAME := $(PROJECT_NAME)

# Python configuration
PYTHON := python3
VENV_DIR := venv
REQUIREMENTS := infrastructure/requirements/requirements.txt
DEV_REQUIREMENTS := infrastructure/requirements/requirements-dev.txt

# Test configuration
TEST_TIMEOUT := 300
PYTEST_ARGS := -v --tb=short
COVERAGE_MIN := 80

# Docker configuration
DOCKERFILE := infrastructure/docker/Dockerfile
DOCKERFILE_TEST := infrastructure/docker/Dockerfile.test
COMPOSE_TEST := infrastructure/docker/docker-compose.test.yml
COMPOSE_FAST := infrastructure/docker/docker-compose.fast-test.yml

# Default target
.DEFAULT_GOAL := help

# Ensure we're using the virtual environment
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Check if virtual environment is activated
check-venv:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo -e "$(RED)❌ Virtual environment not activated$(NC)"; \
		echo -e "$(YELLOW)💡 Run: source $(VENV_DIR)/bin/activate$(NC)"; \
		exit 1; \
	fi

# Development Environment Setup
.PHONY: dev-setup
dev-setup: ## 🔧 Set up development environment
	@echo -e "$(BLUE)🔧 Setting up development environment...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo -e "$(YELLOW)📦 Creating virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	@echo -e "$(YELLOW)📦 Installing dependencies...$(NC)"
	@source $(VENV_DIR)/bin/activate && pip install --upgrade pip
	@source $(VENV_DIR)/bin/activate && pip install -r $(REQUIREMENTS)
	@if [ -f "$(DEV_REQUIREMENTS)" ]; then \
		source $(VENV_DIR)/bin/activate && pip install -r $(DEV_REQUIREMENTS); \
	fi
	@echo -e "$(GREEN)✅ Development environment ready!$(NC)"
	@echo -e "$(CYAN)💡 Activate with: source $(VENV_DIR)/bin/activate$(NC)"

.PHONY: dev-clean
dev-clean: ## 🧹 Clean development environment
	@echo -e "$(YELLOW)🧹 Cleaning development environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@rm -rf __pycache__ .pytest_cache .coverage htmlcov
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo -e "$(GREEN)✅ Development environment cleaned$(NC)"

.PHONY: dev-run
dev-run: check-venv ## 🚀 Run application in development mode
	@echo -e "$(BLUE)🚀 Starting development server...$(NC)"
	@APP_ENV=test $(PYTHON) main.py

.PHONY: dev-test
dev-test: check-venv ## 🧪 Run tests in development mode
	@echo -e "$(BLUE)🧪 Running development tests...$(NC)"
	@$(PYTHON) -m pytest tests/unit/ $(PYTEST_ARGS)

# Testing Commands
.PHONY: test-unit
test-unit: check-venv ## 🧪 Run unit tests
	@echo -e "$(BLUE)🧪 Running unit tests...$(NC)"
	@$(PYTHON) -m pytest tests/unit/ $(PYTEST_ARGS) -m "unit"

.PHONY: test-docker
test-docker: ## 🐳 Run Docker integration tests
	@echo -e "$(BLUE)🐳 Running Docker integration tests...$(NC)"
	@if ! command -v docker >/dev/null 2>&1; then \
		echo -e "$(RED)❌ Docker not found. Please install Docker.$(NC)"; \
		exit 1; \
	fi
	@docker compose -f $(COMPOSE_TEST) down -v --remove-orphans 2>/dev/null || true
	@docker compose -f $(COMPOSE_TEST) up --build --abort-on-container-exit
	@docker compose -f $(COMPOSE_TEST) down -v --remove-orphans

.PHONY: test-fast
test-fast: ## ⚡ Run fast Docker tests
	@echo -e "$(BLUE)⚡ Running fast Docker tests...$(NC)"
	@docker compose -f $(COMPOSE_FAST) down -v --remove-orphans 2>/dev/null || true
	@docker compose -f $(COMPOSE_FAST) up --build --abort-on-container-exit
	@docker compose -f $(COMPOSE_FAST) down -v --remove-orphans

.PHONY: test-coverage
test-coverage: check-venv ## 📊 Run tests with coverage report
	@echo -e "$(BLUE)📊 Running tests with coverage...$(NC)"
	@$(PYTHON) -m pytest tests/unit/ --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=$(COVERAGE_MIN)
	@echo -e "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

.PHONY: test-all
test-all: test-unit test-docker ## 🎯 Run all tests
	@echo -e "$(GREEN)✅ All tests completed$(NC)"

# Code Quality
.PHONY: lint
lint: check-venv ## 🔍 Run code linting
	@echo -e "$(BLUE)🔍 Running code linting...$(NC)"
	@ruff check . --output-format=github

.PHONY: lint-fix
lint-fix: check-venv ## 🔧 Fix linting issues
	@echo -e "$(BLUE)🔧 Fixing linting issues...$(NC)"
	@ruff check . --fix

.PHONY: format
format: check-venv ## 🎨 Format code
	@echo -e "$(BLUE)🎨 Formatting code...$(NC)"
	@ruff format .

.PHONY: type-check
type-check: check-venv ## 🔍 Run type checking
	@echo -e "$(BLUE)🔍 Running type checking...$(NC)"
	@mypy . || echo -e "$(YELLOW)⚠️ Type checking completed with warnings$(NC)"

.PHONY: security-scan
security-scan: check-venv ## 🔒 Run security scanning
	@echo -e "$(BLUE)🔒 Running security scan...$(NC)"
	@bandit -r . -f json -o bandit-report.json || echo -e "$(YELLOW)⚠️ Security scan completed - review bandit-report.json$(NC)"

.PHONY: quality-check
quality-check: lint type-check security-scan ## ✅ Run all quality checks
	@echo -e "$(GREEN)✅ All quality checks completed$(NC)"

# Docker Commands
.PHONY: build
build: ## 🏗️ Build Docker image
	@echo -e "$(BLUE)🏗️ Building Docker image...$(NC)"
	@docker build -f $(DOCKERFILE) -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo -e "$(GREEN)✅ Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

.PHONY: build-test
build-test: ## 🏗️ Build test Docker image
	@echo -e "$(BLUE)🏗️ Building test Docker image...$(NC)"
	@docker build -f $(DOCKERFILE_TEST) -t $(DOCKER_IMAGE):test .
	@echo -e "$(GREEN)✅ Test Docker image built: $(DOCKER_IMAGE):test$(NC)"

.PHONY: run-docker
run-docker: build ## 🐳 Run Docker container locally
	@echo -e "$(BLUE)🐳 Running Docker container...$(NC)"
	@docker run -p 8080:8080 \
		-e APP_ENV=test \
		-e GCP_PROJECT_ID=test-project \
		-e TELEGRAM_TOKEN=test-token \
		-e WEBHOOK_SECRET=test-secret \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: docker-clean
docker-clean: ## 🧹 Clean Docker resources
	@echo -e "$(YELLOW)🧹 Cleaning Docker resources...$(NC)"
	@docker compose -f $(COMPOSE_TEST) down -v --remove-orphans 2>/dev/null || true
	@docker compose -f $(COMPOSE_FAST) down -v --remove-orphans 2>/dev/null || true
	@docker system prune -f
	@echo -e "$(GREEN)✅ Docker resources cleaned$(NC)"

# Environment Management
.PHONY: env-test
env-test: ## 🧪 Start test environment
	@echo -e "$(BLUE)🧪 Starting test environment...$(NC)"
	@docker compose -f $(COMPOSE_TEST) up -d
	@echo -e "$(GREEN)✅ Test environment is running at http://localhost:8080$(NC)"

.PHONY: env-stop
env-stop: ## ⏹️ Stop test environment
	@echo -e "$(YELLOW)⏹️ Stopping test environment...$(NC)"
	@docker compose -f $(COMPOSE_TEST) down
	@docker compose -f $(COMPOSE_FAST) down

.PHONY: env-logs
env-logs: ## 📋 Show environment logs
	@docker compose -f $(COMPOSE_TEST) logs -f

.PHONY: env-health
env-health: ## 🏥 Check environment health
	@echo -e "$(BLUE)🏥 Checking environment health...$(NC)"
	@docker compose -f $(COMPOSE_TEST) exec -T app curl -f http://localhost:8080/healthz || echo "❌ App not healthy"

# Deployment Commands
.PHONY: deploy-staging
deploy-staging: ## 🚀 Deploy to staging environment
	@echo -e "$(BLUE)🚀 Deploying to staging...$(NC)"
	@if [ -z "$$GCP_PROJECT_ID" ]; then \
		echo -e "$(RED)❌ GCP_PROJECT_ID environment variable required$(NC)"; \
		exit 1; \
	fi
	@./devops/scripts/deploy.sh -p "$$GCP_PROJECT_ID" -e staging

.PHONY: deploy-production
deploy-production: ## 🚀 Deploy to production environment
	@echo -e "$(BLUE)🚀 Deploying to production...$(NC)"
	@if [ -z "$$GCP_PROJECT_ID" ]; then \
		echo -e "$(RED)❌ GCP_PROJECT_ID environment variable required$(NC)"; \
		exit 1; \
	fi
	@./devops/scripts/deploy.sh -p "$$GCP_PROJECT_ID" -e production

# Utility Commands
.PHONY: clean
clean: dev-clean docker-clean ## 🧹 Clean all build artifacts
	@echo -e "$(GREEN)✅ All artifacts cleaned$(NC)"

.PHONY: install
install: dev-setup ## 📦 Install dependencies
	@echo -e "$(GREEN)✅ Dependencies installed$(NC)"

.PHONY: update
update: check-venv ## 🔄 Update dependencies
	@echo -e "$(BLUE)🔄 Updating dependencies...$(NC)"
	@pip install --upgrade pip
	@pip install -r $(REQUIREMENTS) --upgrade
	@if [ -f "$(DEV_REQUIREMENTS)" ]; then \
		pip install -r $(DEV_REQUIREMENTS) --upgrade; \
	fi
	@echo -e "$(GREEN)✅ Dependencies updated$(NC)"

.PHONY: freeze
freeze: check-venv ## 📋 Freeze current dependencies
	@echo -e "$(BLUE)📋 Freezing dependencies...$(NC)"
	@pip freeze > requirements-frozen.txt
	@echo -e "$(GREEN)✅ Dependencies frozen to requirements-frozen.txt$(NC)"

# Performance Testing
.PHONY: benchmark
benchmark: ## 📈 Run performance benchmarks
	@echo -e "$(BLUE)📈 Running performance benchmarks...$(NC)"
	@ab -n 1000 -c 10 http://localhost:8080/healthz > /dev/null 2>&1 || echo "Install apache2-utils for benchmarking"

# Documentation
.PHONY: docs
docs: ## 📚 Generate documentation
	@echo -e "$(BLUE)📚 Documentation available in docs/ directory$(NC)"
	@echo -e "$(CYAN)📖 Key documents:$(NC)"
	@echo -e "  • README.md - Project overview"
	@echo -e "  • docs/DEPLOYMENT_GUIDE.md - Deployment instructions"
	@echo -e "  • docs/TESTING.md - Testing guide"
	@echo -e "  • docs/ARCHITECTURE.md - System architecture"

# Information
.PHONY: info
info: ## ℹ️ Show project information
	@echo -e "$(CYAN)📋 Project Information$(NC)"
	@echo -e "Project: $(PROJECT_NAME)"
	@echo -e "Docker Image: $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@echo -e "Python: $(shell $(PYTHON) --version 2>/dev/null || echo 'Not found')"
	@echo -e "Docker: $(shell docker --version 2>/dev/null || echo 'Not found')"
	@echo -e "Virtual Env: $(shell echo $$VIRTUAL_ENV || echo 'Not activated')"

# Branch Protection
.PHONY: verify-branch-protection
verify-branch-protection: ## 🛡️ Verify branch protection settings
	@echo -e "$(BLUE)🛡️ Verifying branch protection settings...$(NC)"
	@if command -v gh >/dev/null 2>&1; then \
		./devops/scripts/verify-branch-protection.sh; \
	else \
		echo -e "$(YELLOW)⚠️ GitHub CLI not installed. Install with: brew install gh$(NC)"; \
		echo -e "$(CYAN)💡 Manual verification:$(NC)"; \
		echo -e "   https://github.com/YOUR-USERNAME/YOUR-REPOSITORY/settings/branches"; \
	fi

.PHONY: setup-branch-protection
setup-branch-protection: ## 🛡️ Show branch protection setup instructions
	@echo -e "$(BLUE)🛡️ Branch Protection Setup Instructions$(NC)"
	@echo -e "$(CYAN)📖 Complete setup guide: docs/BRANCH_PROTECTION_SETUP.md$(NC)"
	@echo -e "$(YELLOW)🔗 Quick setup:$(NC)"
	@echo -e "   1. Go to: https://github.com/YOUR-USERNAME/YOUR-REPOSITORY/settings/branches"
	@echo -e "   2. Add rule for 'main' branch"
	@echo -e "   3. Enable: 'Require pull request reviews before merging'"
	@echo -e "   4. Enable: 'Require status checks to pass before merging'"

# Help
.PHONY: help
help: ## 📖 Show this help message
	@echo -e "$(BLUE)🚀 $(PROJECT_NAME) - Available Commands$(NC)"
	@echo ""
	@echo -e "$(CYAN)📦 Development:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*📦|🔧|🚀|🧪|⚡/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo -e "$(CYAN)🧪 Testing:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🧪|🐳|📊|🎯/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo -e "$(CYAN)🔍 Quality:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🔍|🎨|🔒|✅/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo -e "$(CYAN)🐳 Docker:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🏗️|🐳|🧹/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo -e "$(CYAN)🚀 Deployment:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🚀/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo -e "$(CYAN)🛠️ Utilities:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## .*🧹|📦|🔄|📋|📈|📚|ℹ️|🛡️|📖/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo -e "$(PURPLE)💡 Examples:$(NC)"
	@echo -e "  $(WHITE)make dev-setup$(NC)     # Set up development environment"
	@echo -e "  $(WHITE)make test-all$(NC)      # Run all tests"
	@echo -e "  $(WHITE)make build$(NC)         # Build Docker image"
	@echo -e "  $(WHITE)make deploy-staging$(NC) # Deploy to staging"
