# Blacklist Service Management Makefile

.PHONY: help setup build up down logs clean test deploy dev prod restart health

# Default environment
ENV ?= development

# Setup commands
setup: ## Setup complete development environment (Python + Node.js + VSCode extensions)
	@echo "🚀 Setting up development environment..."
	@bash scripts/setup-dev-environment.sh

# Help target
help: ## Show this help message
	@echo "Blacklist Service Management Commands:"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
dev: ## Start development environment with live reload
	@echo "🚀 Starting development environment..."
	@docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
	@echo "✅ Development environment started"
	@echo "🌐 Application: http://localhost:2542"
	@echo "🗄️ Database: Internal only (use make db-shell for access)"
	@echo "🔴 Redis: Internal only"
	@echo "📦 Collector: Internal only"

prod: ## Start production environment
	@echo "🚀 Starting production environment..."
	@docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ Production environment started"

# Build commands
build: ## Build all Docker images
	@echo "🏗️ Building Docker images..."
	@docker compose build --parallel
	@echo "✅ Build completed"

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
	@curl -s http://localhost:2542/health | python3 -m json.tool || echo "❌ Application not responding"

# Testing
test: ## Run comprehensive tests
	@echo "🧪 Running comprehensive tests..."
	@python3 scripts/comprehensive_test.py

test-endpoints: ## Test API endpoints
	@echo "🔍 Testing API endpoints..."
	@python3 scripts/verify_endpoints.py

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
	@echo "Registry: registry.jclee.me"
	@echo "Local URL: http://localhost:2542"
	@echo "Production URL: https://blacklist.jclee.me"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make dev      - Start development environment"
	@echo "  make prod     - Start production environment"
	@echo "  make logs     - View all logs"
	@echo "  make health   - Check service health"
	@echo "  make test     - Run tests"

# Default target
.DEFAULT_GOAL := help
