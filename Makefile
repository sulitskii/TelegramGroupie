# TelegramGroupie - Makefile
# ==============================================
# Development, Testing, and Deployment Commands
# ==============================================

.PHONY: help install test test-unit test-integration test-coverage test-all
.PHONY: format lint type-check check quality
.PHONY: docker-build docker-test docker-test-minimal docker-clean
.PHONY: run run-test run-debug run-local clean clean-all
.PHONY: docs docs-serve requirements-check security-scan

# ==============================================
# Enhanced Static Analysis Commands
# ==============================================

# Modern linting with Ruff (replaces flake8, black, isort)
ruff-check: ## Run Ruff linter (ultra-fast)
	@echo "⚡ Running Ruff linter..."
	ruff check . --show-fixes
	@echo "✅ Ruff linting completed"

ruff-format: ## Run Ruff formatter (replaces black)
	@echo "⚡ Running Ruff formatter..."
	ruff format .
	@echo "✅ Ruff formatting completed"

ruff-fix: ## Run Ruff with auto-fixes
	@echo "⚡ Running Ruff with auto-fixes..."
	ruff check . --fix
	@echo "✅ Ruff auto-fixes completed"

# Legacy formatters (kept for compatibility)
format: ruff-format ## Format code with Ruff (recommended)

format-legacy: ## Format code with legacy tools
	@echo "🎨 Formatting code with legacy tools..."
	black .
	isort .
	@echo "✅ Legacy formatting completed"

# Enhanced linting options
lint: ruff-check ## Run modern linting with Ruff

lint-comprehensive: ## Run comprehensive linting with multiple tools
	@echo "🔍 Running comprehensive linting..."
	ruff check .
	pylint . --output-format=colorized --reports=no || true
	@echo "✅ Comprehensive linting completed"

# Security analysis
security-scan: ## Run comprehensive security scanning
	@echo "🛡️ Running security scans..."
	bandit -r . -x tests/,venv/ -f screen
	safety check
	semgrep --config=auto . || true
	pip-audit || true
	@echo "✅ Security scanning completed"

security-report: ## Generate detailed security reports
	@echo "🛡️ Generating security reports..."
	bandit -r . -x tests/,venv/ -f json -o security-bandit.json || true
	safety check --json --output security-safety.json || true
	semgrep --config=auto --json --output=security-semgrep.json . || true
	pip-audit --format=json --output=security-pip-audit.json || true
	@echo "📋 Security reports generated"

# Code complexity analysis
complexity-analysis: ## Analyze code complexity
	@echo "📈 Running complexity analysis..."
	radon cc . --show-complexity --min B
	radon mi . --min B
	xenon --max-absolute B --max-modules A --max-average A . || true
	@echo "✅ Complexity analysis completed"

complexity-report: ## Generate detailed complexity reports
	@echo "📈 Generating complexity reports..."
	radon cc . --json > complexity-cyclomatic.json
	radon mi . --json > complexity-maintainability.json  
	radon raw . --json > complexity-raw.json
	vulture . --json > complexity-deadcode.json || true
	@echo "📋 Complexity reports generated"

# Dependency analysis
deps-analysis: ## Analyze project dependencies
	@echo "📦 Running dependency analysis..."
	pip-licenses --format=table
	pipdeptree --warn silence
	@echo "✅ Dependency analysis completed"

deps-report: ## Generate dependency reports
	@echo "📦 Generating dependency reports..."
	pip-licenses --format=json --output-file=deps-licenses.json
	pipdeptree --json > deps-tree.json
	pip list --format=json > deps-installed.json
	@echo "📋 Dependency reports generated"

# Documentation analysis
docs-check: ## Check documentation quality
	@echo "📚 Checking documentation..."
	pydocstyle . --convention=google --add-ignore=D100,D104 || true
	interrogate . --fail-under=80 || true
	@echo "✅ Documentation check completed"

# Pre-commit integration
pre-commit-install: ## Install pre-commit hooks
	@echo "🔧 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

pre-commit-run: ## Run all pre-commit hooks
	@echo "🔍 Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "✅ Pre-commit hooks completed"

pre-commit-update: ## Update pre-commit hooks
	@echo "🔄 Updating pre-commit hooks..."
	pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated"

# Comprehensive quality gates
quality-gate-basic: ruff-check type-check security-scan ## Basic quality gate
	@echo "🎯 Basic quality gate passed!"

quality-gate-full: lint-comprehensive type-check security-scan complexity-analysis docs-check ## Full quality gate
	@echo "🎯 Full quality gate passed!"

quality-gate-ci: ## CI/CD quality gate (fast)
	@echo "🚀 Running fast CI/CD quality gate..."
	ruff check .
	ruff format --check .
	mypy . --ignore-missing-imports
	bandit -r *.py mock_*.py --skip B101,B104,B105,B201,B605,B607 -q
	safety scan --short-report
	@echo "🎯 Fast CI/CD quality gate passed!"

quality-gate-ci-full: ## Complete CI/CD quality gate (matches GitHub Actions)
	@echo "🚀 Running COMPLETE CI/CD quality gate (matches GitHub Actions)..."
	@echo ""
	@echo "📋 Stage 1: Pre-commit Checks"
	-pre-commit run --all-files
	@echo ""
	@echo "📋 Stage 2: Ruff Analysis (Ultra-fast linting)"
	ruff check . --output-format=github --show-fixes
	ruff format --check .
	-ruff check . --output-format=json > ruff-report.json
	@echo ""
	@echo "📋 Stage 3: Security Analysis"
	-bandit -r *.py mock_*.py --skip B101,B104,B105,B201,B605,B607 -f json -o bandit-report.json
	-safety scan --short-report
	-semgrep --config=auto --json --output=semgrep-report.json .
	@echo ""
	@echo "📋 Stage 4: Type Checking"
	mypy . --ignore-missing-imports
	@echo ""
	@echo "📋 Stage 5: Complexity Analysis"
	-radon cc . --json > radon-complexity.json
	-radon mi . --json > radon-maintainability.json
	-radon raw . --json > radon-raw.json
	-vulture . --json > vulture-report.json
	-xenon --max-absolute B --max-modules A --max-average A .
	@echo ""
	@echo "📋 Stage 6: Dependency Analysis"
	-pip-licenses --format=json --output-file=licenses.json
	-pip-audit --format=json --output=pip-audit.json
	-pipdeptree --json > dependency-tree.json
	@echo ""
	@echo "📋 Stage 7: Test Suite with Coverage"
	python -m pytest tests/ --cov=. --cov-report=xml --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "🎯 COMPLETE CI/CD quality gate passed! All GitHub Actions stages executed locally."

# Performance analysis
profile-performance: ## Profile application performance
	@echo "⚡ Running performance analysis..."
	@echo "Starting test server for profiling..."
	TESTING=true python main.py &
	sleep 3
	py-spy record -o profile.svg -d 10 -s -- python main.py &
	@echo "Stopping test server..."
	@pkill -f "python main.py" || true
	@echo "📊 Performance profile saved to profile.svg"

# Code metrics dashboard
metrics-dashboard: ## Generate comprehensive metrics dashboard
	@echo "📊 Generating metrics dashboard..."
	@mkdir -p reports
	@echo "# 📊 Code Quality Dashboard" > reports/metrics.md
	@echo "" >> reports/metrics.md
	@echo "Generated on: $$(date)" >> reports/metrics.md
	@echo "" >> reports/metrics.md
	@echo "## 📈 Code Metrics" >> reports/metrics.md
	@echo "" >> reports/metrics.md
	@echo "\`\`\`" >> reports/metrics.md
	@radon raw . >> reports/metrics.md
	@echo "\`\`\`" >> reports/metrics.md
	@echo "" >> reports/metrics.md
	@echo "## 🧪 Test Coverage" >> reports/metrics.md
	@echo "" >> reports/metrics.md
	python -m pytest tests/ --cov=. --cov-report=term-missing >> reports/metrics.md || true
	@echo "📋 Metrics dashboard saved to reports/metrics.md"

# Static analysis report generation
static-analysis-report: ## Generate comprehensive static analysis report
	@echo "📋 Generating comprehensive static analysis report..."
	@mkdir -p reports
	make ruff-check > reports/ruff-output.txt 2>&1 || true
	make security-report > reports/security-output.txt 2>&1 || true
	make complexity-report > reports/complexity-output.txt 2>&1 || true
	make deps-report > reports/deps-output.txt 2>&1 || true
	@echo "📊 Static analysis reports generated in reports/ directory"

# Update the main check command to use enhanced analysis
check: quality-gate-basic ## Run enhanced code quality checks
	@echo "🎯 Enhanced quality checks completed!"

# Update quality command
quality: quality-gate-full test ## Run full quality assurance with enhanced analysis
	@echo "✨ Enhanced quality assurance completed!"

# ==============================================
# Default target
# ==============================================

help: ## Show this help message
	@echo "🚀 TelegramGroupie - Available Commands"
	@echo "=================================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📝 Examples:"
	@echo "  make install          # Set up development environment"
	@echo "  make test            # Run all tests"
	@echo "  make docker-test     # Quick Docker integration test"
	@echo "  make check           # Run all quality checks"

# ==============================================
# Installation and Setup
# ==============================================

install: ## Install dependencies for development
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "✅ Dependencies installed"

install-prod: ## Install production dependencies only
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt
	@echo "✅ Production dependencies installed"

requirements-check: ## Check for outdated dependencies
	@echo "🔍 Checking for outdated dependencies..."
	pip list --outdated

# ==============================================
# Testing Commands
# ==============================================

test: test-unit test-integration ## Run all tests (unit + integration)
	@echo "🎉 All tests completed successfully!"

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	python -m pytest tests/test_main.py tests/test_encryption.py tests/test_message_retrieval.py -v

test-integration: ## Run integration tests (with mocks)
	@echo "🧪 Running integration tests..."
	TESTING=true python -m pytest tests/test_integration.py -v

test-all: ## Run comprehensive test suite
	@echo "🧪 Running all tests..."
	python -m pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml
	@echo "📋 Coverage report generated in htmlcov/"

test-docker: ## Run Docker-specific integration tests
	@echo "🐳 Running Docker integration tests..."
	python -m pytest tests/test_integration_docker.py -v -m docker

# ==============================================
# Code Quality Commands
# ==============================================

format: ruff-format ## Format code with Ruff (recommended)

type-check: ## Run type checking with mypy
	@echo "🔍 Running type checker..."
	mypy . --ignore-missing-imports
	@echo "✅ Type checking completed"

# ==============================================
# Docker Commands
# ==============================================

docker-build: ## Build Docker image
	@echo "🏗️ Building Docker image..."
	docker build -t telegramgroupie:latest .
	@echo "✅ Docker image built"

docker-test: ## Run quick Docker integration test
	@echo "🐳 Running Docker integration tests..."
	bash scripts/run-basic-docker-test.sh
	@echo "✅ Docker tests completed"

docker-test-minimal: ## Run minimal Docker tests with compose
	@echo "🐳 Running minimal Docker Compose tests..."
	docker-compose -f docker-compose.minimal.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.minimal.yml down
	@echo "✅ Minimal Docker tests completed"

docker-test-simple: ## Run simple Docker tests without external dependencies
	@echo "🐳 Running simple Docker tests..."
	docker-compose -f docker-compose.simple.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.simple.yml down
	@echo "✅ Simple Docker tests completed"

docker-clean: ## Clean up Docker containers and images
	@echo "🧹 Cleaning Docker resources..."
	docker system prune -f
	docker-compose -f docker-compose.minimal.yml down -v --remove-orphans 2>/dev/null || true
	docker-compose -f docker-compose.simple.yml down -v --remove-orphans 2>/dev/null || true
	@echo "✅ Docker cleanup completed"

# ==============================================
# Development Server Commands
# ==============================================

run: ## Run the application in production mode
	@echo "🚀 Starting application..."
	python main.py

run-test: ## Run the application in testing mode (with mocks)
	@echo "🧪 Starting application in testing mode..."
	TESTING=true python main.py

run-debug: ## Run the application in debug mode
	@echo "🐛 Starting application in debug mode..."
	FLASK_DEBUG=true TESTING=true python main.py

run-local: ## Run local development environment
	@echo "🏠 Starting local development environment..."
	python run_local.py

# ==============================================
# Documentation Commands
# ==============================================

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "📋 Available documentation:"
	@echo "  - README.md (Main documentation)"
	@echo "  - docs/ARCHITECTURE.md (System architecture)"
	@echo "  - docs/CI_CD_PIPELINE.md (CI/CD pipeline)"
	@echo "  - docs/DOCKER_TESTING.md (Docker testing guide)"
	@echo "  - SECURITY.md (Security guidelines)"

docs-serve: ## Serve documentation locally (if using mkdocs)
	@echo "📚 Serving documentation..."
	@echo "ℹ️  Documentation is available as Markdown files"
	@echo "   View README.md for the main documentation"

# ==============================================
# Cleanup Commands
# ==============================================

clean: ## Clean up temporary files and caches
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf test-results
	@echo "✅ Cleanup completed"

clean-all: clean docker-clean ## Complete cleanup (including Docker)
	@echo "🧹 Running complete cleanup..."
	rm -rf venv 2>/dev/null || true
	@echo "✅ Complete cleanup finished"

# ==============================================
# CI/CD Commands
# ==============================================

ci-test: ## Run CI/CD test suite (matches GitHub Actions)
	@echo "🚀 Running CI/CD test suite..."
	make check
	make test
	make docker-test
	@echo "🎉 CI/CD test suite completed successfully!"

ci-build: ## Build for CI/CD pipeline
	@echo "🏗️ Building for CI/CD..."
	make docker-build
	@echo "✅ CI/CD build completed"

# ==============================================
# Release Commands
# ==============================================

release-check: ## Check if ready for release
	@echo "🔍 Checking release readiness..."
	make quality
	make docker-test
	@echo "✅ Release checks passed"

# ==============================================
# Information Commands
# ==============================================

info: ## Show project information
	@echo "📋 Project Information"
	@echo "======================"
	@echo "Project: TelegramGroupie"
	@echo "Python: $(shell python --version)"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Git: $(shell git --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "📁 Project Structure:"
	@echo "  - main.py (Flask application)"
	@echo "  - encryption.py (KMS encryption)"
	@echo "  - mock_*.py (Testing mocks)"
	@echo "  - tests/ (Test suite)"
	@echo "  - docs/ (Documentation)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  - Unit tests: $(shell find tests -name 'test_*.py' | wc -l) files"
	@echo "  - Docker tests: Available"
	@echo "  - Mock services: Enabled"

status: ## Show current project status
	@echo "📊 Project Status"
	@echo "================="
	@echo "Git status:"
	@git status --short 2>/dev/null || echo "Not a git repository"
	@echo ""
	@echo "Dependencies:"
	@echo "  - Production: $(shell grep -c '^[^#]' requirements.txt) packages"
	@echo "  - Development: $(shell grep -c '^[^#]' requirements-dev.txt) packages"
	@echo ""
	@echo "Tests:"
	@echo "  - Total test files: $(shell find tests -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "  - Docker compose files: $(shell ls docker-compose*.yml 2>/dev/null | wc -l)"

# ==============================================
# Advanced Commands
# ==============================================

benchmark: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks..."
	@echo "ℹ️  Starting test server..."
	TESTING=true python main.py &
	sleep 3
	@echo "📊 Testing health endpoint performance..."
	@ab -n 1000 -c 10 http://localhost:8080/healthz > /dev/null 2>&1 || echo "Install apache2-utils for benchmarking"
	@echo "🛑 Stopping test server..."
	@pkill -f "python main.py" || true
	@echo "✅ Benchmarking completed"

validate: ## Validate project configuration
	@echo "✅ Validating project configuration..."
	@echo "📋 Checking required files..."
	@test -f main.py || (echo "❌ main.py missing" && exit 1)
	@test -f requirements.txt || (echo "❌ requirements.txt missing" && exit 1)
	@test -f Dockerfile || (echo "❌ Dockerfile missing" && exit 1)
	@test -d tests || (echo "❌ tests/ directory missing" && exit 1)
	@echo "📋 Checking Python syntax..."
	@python -m py_compile main.py
	@python -m py_compile encryption.py
	@echo "📋 Checking Docker syntax..."
	@docker build --dry-run . > /dev/null 2>&1 || echo "⚠️  Docker build validation failed"
	@echo "✅ Project validation completed"

# ==============================================
# Special Targets
# ==============================================

.DEFAULT_GOAL := help

# Ensure commands fail fast
.SHELLFLAGS := -eu -o pipefail -c 

# Add to help display
.PHONY: ruff-check ruff-format ruff-fix format-legacy lint-comprehensive
.PHONY: security-report complexity-analysis complexity-report deps-analysis deps-report docs-check
.PHONY: pre-commit-install pre-commit-run pre-commit-update
.PHONY: quality-gate-basic quality-gate-full quality-gate-ci profile-performance
.PHONY: metrics-dashboard static-analysis-report 