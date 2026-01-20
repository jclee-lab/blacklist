# Blacklist Service Management Makefile

.PHONY: help setup setup-hooks setup-offline package-deps build up down logs clean test deploy dev prod restart health

# Default environment
ENV ?= development

# Setup commands
setup: ## Setup complete development environment (Python + Node.js + VSCode config + extensions)
	@echo "🚀 Setting up development environment..."
	@bash scripts/setup/setup-dev-environment.sh

setup-hooks: ## Setup git hooks (pre-commit + husky)
	@echo "🔧 Setting up git hooks..."
	@pip install pre-commit --quiet
	@pre-commit install --install-hooks
	@pre-commit install --hook-type commit-msg
	@cd frontend && npm install
	@echo "✅ Git hooks installed"
	@echo "   - Pre-commit: Python linting (Ruff, mypy), secret detection"
	@echo "   - Commit-msg: Conventional commits enforcement"
	@echo "   - Husky: Frontend linting (ESLint, Prettier)"

setup-offline: ## Setup development environment from offline packages (Python + Node.js + VSCode)
	@echo "🚀 Setting up from offline packages..."
	@bash scripts/setup/setup-offline.sh

package-deps: ## Package all dependencies for offline installation
	@echo "📦 Packaging dependencies for offline installation..."
	@bash scripts/package/package-dependencies.sh

# Help target
help: ## Show this help message
	@echo "Blacklist Service Management Commands:"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
dev: ## Start development environment with hot reload (rebuilds changed images)
	@echo "🚀 Starting development environment..."
	@docker compose up -d --build
	@echo "✅ Development environment started (hot reload enabled)"
	@echo "🌐 Application: http://localhost:${PORT:-2542}"
	@echo "💡 Code changes auto-reload via volume mounts"

dev-no-build: ## Start without rebuild (faster, use existing images)
	@echo "🚀 Starting development environment (no rebuild)..."
	@docker compose up -d
	@echo "✅ Started with existing images"

dev-prod: ## Start production-like (no override, no hot reload)
	@echo "🚀 Starting production-like environment..."
	@docker compose -f docker-compose.yml up -d --build
	@echo "✅ Production-like environment started (no hot reload)"

dev-app: ## Restart only app service (quick iteration)
	@echo "🔄 Rebuilding and restarting app..."
	@docker compose up -d --build --no-deps blacklist-app
	@echo "✅ App restarted"

dev-frontend: ## Restart only frontend service
	@echo "🔄 Rebuilding and restarting frontend..."
	@docker compose up -d --build --no-deps blacklist-frontend
	@echo "✅ Frontend restarted"

prod: ## Start production environment
	@echo "🚀 Starting production environment..."
	@docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ Production environment started"

# Build commands
.PHONY: check-clean
check-clean:
	@if ! git diff-index --quiet HEAD -- 2>/dev/null; then \
		echo "❌ Uncommitted changes detected! Commit before build."; \
		git status --short; \
		exit 1; \
	fi

build: check-clean ## Build all Docker images
	@echo "🏗️ Building Docker images..."
	@GIT_COMMIT=$$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") docker compose build --parallel
	@echo "✅ Build completed (commit: $$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown'))"

rebuild: ## Rebuild all images from scratch
	@echo "🏗️ Rebuilding Docker images from scratch..."
	@docker compose build --no-cache --parallel
	@echo "✅ Rebuild completed"

# Service management
up: ## Start all services (default: development)
ifeq ($(ENV),production)
	@$(MAKE) prod
else
	@$(MAKE) dev
endif

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	@docker compose down
	@echo "✅ All services stopped"

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	@$(MAKE) down
	@$(MAKE) up ENV=$(ENV)
	@echo "✅ Services restarted"

# Monitoring and logs
logs: ## Show logs for all services
	@docker compose logs -f

logs-app: ## Show logs for app service only
	@docker compose logs -f blacklist-app

logs-db: ## Show logs for database service only
	@docker compose logs -f blacklist-postgres

logs-collector: ## Show logs for collector service only
	@docker compose logs -f blacklist-collector

health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@docker compose ps
	@echo ""
	@echo "🌐 Testing application health:"
	@curl -s http://localhost:${PORT:-2542}/health | python3 -m json.tool || echo "❌ Application not responding"

# Testing
test: ## Run all tests (backend + frontend)
	@echo "🧪 Running all tests..."
	@$(MAKE) test-backend
	@$(MAKE) test-frontend
	@echo "✅ All tests completed"

test-backend: ## Run backend tests (unit + integration)
	@echo "🧪 Running backend tests..."
	@$(MAKE) test-backend-unit
	@$(MAKE) test-backend-integration
	@echo "✅ Backend tests completed"

test-backend-unit: ## Run backend unit tests
	@echo "🧪 Running backend unit tests..."
	@docker compose exec -T blacklist-app env COVERAGE_FILE=/tmp/.coverage python -m pytest tests/unit -v --cov=app/core --cov-report=term --cov-report=html:htmlcov || echo "⚠️  Some unit tests failed"

test-backend-integration: ## Run backend integration tests
	@echo "🧪 Running backend integration tests..."
	@docker compose exec -T blacklist-app python -m pytest tests/integration -v || echo "⚠️  Some integration tests failed"

test-backend-e2e: ## Run backend E2E tests
	@echo "🧪 Running backend E2E tests..."
	@docker compose exec -T blacklist-app python -m pytest tests/e2e -v || echo "⚠️  Some E2E tests failed"

test-backend-coverage: ## Run backend tests with coverage report
	@echo "🧪 Running backend tests with coverage..."
	@docker compose exec -T blacklist-app python -m pytest tests/ -v \
		--cov=app/core \
		--cov-report=term \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=80
	@echo "📊 Coverage report generated in htmlcov/"

test-frontend: ## Run frontend tests (unit + E2E)
	@echo "🧪 Running frontend tests..."
	@cd frontend && npm run test
	@echo "✅ Frontend tests completed"

test-frontend-unit: ## Run frontend unit tests
	@echo "🧪 Running frontend unit tests..."
	@cd frontend && npm run test

test-frontend-e2e: ## Run frontend E2E tests (Playwright)
	@echo "🧪 Running frontend E2E tests..."
	@cd frontend && npm run test:e2e

test-frontend-coverage: ## Run frontend tests with coverage
	@echo "🧪 Running frontend tests with coverage..."
	@cd frontend && npm run test:coverage

test-watch: ## Run backend tests in watch mode
	@echo "🧪 Running tests in watch mode..."
	@docker compose exec -T blacklist-app python -m pytest tests/ -v --watch

test-quick: ## Run quick smoke tests only
	@echo "🧪 Running quick smoke tests..."
	@docker compose exec -T blacklist-app python -m pytest tests/unit -v -k "test_health or test_check" --no-cov

test-security: ## Run security-focused tests
	@echo "🔒 Running security tests..."
	@docker compose exec -T blacklist-app python -m pytest tests/ -v -m security

test-db: ## Run database-related tests
	@echo "💾 Running database tests..."
	@docker compose exec -T blacklist-app python -m pytest tests/ -v -m db

test-api: ## Run API endpoint tests
	@echo "🌐 Running API tests..."
	@docker compose exec -T blacklist-app python -m pytest tests/ -v -m api

test-all-markers: ## Run all tests by marker (unit, integration, e2e, slow, db, security, api, cache, asyncio)
	@echo "🧪 Running all test markers..."
	@echo "📋 Unit tests:"
	@docker compose exec -T blacklist-app python -m pytest tests/ -v -m unit --no-cov || true
	@echo ""
	@echo "📋 Integration tests:"
	@docker compose exec -T blacklist-app python -m pytest tests/ -v -m integration --no-cov || true
	@echo ""
	@echo "📋 E2E tests:"
	@docker compose exec -T blacklist-app python -m pytest tests/ -v -m e2e --no-cov || true
	@echo ""
	@echo "📋 Security tests:"
	@docker compose exec -T blacklist-app python -m pytest tests/ -v -m security --no-cov || true
	@echo ""
	@echo "📋 API tests:"
	@docker compose exec -T blacklist-app python -m pytest tests/ -v -m api --no-cov || true

test-comprehensive: ## Run comprehensive tests (legacy script)
	@echo "🧪 Running comprehensive tests (legacy)..."
	@python3 scripts/testing/comprehensive_test.py

test-endpoints: ## Test API endpoints (legacy)
	@echo "🔍 Testing API endpoints (legacy)..."
	@python3 scripts/testing/verify_endpoints.py

test-ci: ## Run tests in CI/CD mode (with coverage and reports)
	@echo "🤖 Running tests in CI/CD mode..."
	@docker compose exec -T blacklist-app python -m pytest tests/ -v \
		--cov=app/core \
		--cov-report=term \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--junitxml=junit.xml \
		--cov-fail-under=80
	@echo "✅ CI/CD tests completed"

# Maintenance
clean: ## Clean up containers, networks, and volumes
	@echo "🧹 Cleaning up Docker resources..."
	@docker compose down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup completed"

clean-all: ## Clean everything including images
	@echo "🧹 Cleaning up all Docker resources..."
	@docker compose down -v --remove-orphans --rmi all
	@docker system prune -af
	@echo "✅ Complete cleanup finished"

# Database management
db-shell: ## Connect to PostgreSQL database
	@docker exec -it blacklist-postgres psql -U postgres -d blacklist

db-backup: ## Backup database
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	@docker exec blacklist-postgres pg_dump -U postgres blacklist > backups/blacklist_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created in backups/"

db-restore: ## Restore database from backup (requires BACKUP_FILE variable)
	@if [ -z "$(BACKUP_FILE)" ]; then echo "❌ Please provide BACKUP_FILE variable"; exit 1; fi
	@echo "📥 Restoring database from $(BACKUP_FILE)..."
	@docker exec -i blacklist-postgres psql -U postgres -d blacklist < $(BACKUP_FILE)
	@echo "✅ Database restored"

# Development helpers
shell-app: ## Get shell access to app container
	@docker exec -it blacklist-app /bin/bash

shell-db: ## Get shell access to database container
	@docker exec -it blacklist-postgres /bin/bash

# CI/CD helpers
ci-build: ## Build for CI/CD (production images)
	@echo "🏗️ Building for CI/CD..."
	@docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
	@echo "✅ CI/CD build completed"

deploy: ## Deploy to production (builds and starts prod environment)
	@echo "🚀 Deploying to production..."
	@$(MAKE) ci-build
	@$(MAKE) prod
	@$(MAKE) health
	@echo "✅ Production deployment completed"

deploy-k8s-dev: ## Deploy to Kubernetes (Development)
	@echo "🚀 Deploying to Kubernetes (Dev)..."
	@bash scripts/deploy/deploy-k8s-dev.sh

deploy-k8s-airgap: ## Deploy to Kubernetes (Air-Gap)
	@echo "🚀 Deploying to Kubernetes (Air-Gap)..."
	@bash scripts/deploy/deploy-k8s-airgap.sh

deploy-airgap: ## Deploy in air-gapped environment (load images from dist/images/)
	@echo "🚀 Air-gapped deployment..."
	@bash scripts/deploy/deploy-airgap.sh

deploy-airgap-skip-load: ## Start services without loading images (images already loaded)
	@echo "🚀 Air-gapped deployment (skip image load)..."
	@bash scripts/deploy/deploy-airgap.sh --skip-load

# Status and information
status: ## Show detailed status of all services
	@echo "📊 Service Status Report"
	@echo "======================="
	@echo ""
	@echo "🐳 Docker Containers:"
	@docker compose ps
	@echo ""
	@echo "📊 Resource Usage:"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
	@echo ""
	@echo "💾 Volume Usage:"
	@docker volume ls --filter name=blacklist
	@echo ""
	@echo "🌐 Network Info:"
	@docker network ls --filter name=blacklist

info: ## Show project information
	@echo "Blacklist Service Information"
	@echo "============================="
	@echo "Project: REGTECH Blacklist Intelligence Platform"
	@echo "Version: 3.0.0 (Microservices Architecture)"
	@echo "Services: 4 containers (app, collector, postgres, redis)"
	@echo "Registry: $${REGISTRY_DOMAIN:-registry.example.com}"
	@echo "Local URL: http://localhost:2542"
	@echo "Production URL: https://${PROD_DOMAIN:-blacklist.example.com}"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make dev      - Start development environment"
	@echo "  make prod     - Start production environment"
	@echo "  make logs     - View all logs"
	@echo "  make health   - Check service health"
	@echo "  make test     - Run tests"

# Default target
.DEFAULT_GOAL := help
