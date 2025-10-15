# Makefile
# Convenience commands for dBank Copilot Docker deployment

.PHONY: help build up down restart logs clean init-data rebuild dev prod

# Default target
help:
	@echo "dBank Copilot - Docker Commands"
	@echo "================================"
	@echo ""
	@echo "Setup & Build:"
	@echo "  make build          - Build all Docker images"
	@echo "  make rebuild        - Rebuild images without cache"
	@echo ""
	@echo "Run Services:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make dev            - Start in development mode (with hot reload)"
	@echo "  make prod           - Start in production mode"
	@echo ""
	@echo "Data Management:"
	@echo "  make init-data      - Run data initialization only"
	@echo "  make reset-data     - Reset database and reinitialize"
	@echo "  make dbt-run        - Run dbt transformations"
	@echo "  make embed          - Regenerate vector embeddings"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-api       - View API logs"
	@echo "  make logs-mcp       - View MCP server logs"
	@echo "  make status         - Check service status"
	@echo ""
	@echo "Database:"
	@echo "  make db-shell       - Connect to PostgreSQL shell"
	@echo "  make db-backup      - Backup database"
	@echo "  make db-restore     - Restore database from backup"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make clean-all      - Remove everything including images"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests in container"
	@echo "  make test-tools     - Test MCP tools"

# ============================================
# Build Commands
# ============================================

build:
	@echo "🏗️  Building Docker images..."
	docker-compose build

rebuild:
	@echo "🏗️  Rebuilding Docker images (no cache)..."
	docker-compose build --no-cache

# ============================================
# Run Commands
# ============================================

up:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo ""
	@echo "✅ Services started!"
	@echo "   Frontend:    http://localhost:3000"
	@echo "   API:         http://localhost:8001"
	@echo "   MCP Server:  http://localhost:8000"
	@echo "   PostgreSQL:  localhost:5433"
	@echo ""
	@echo "Run 'make logs' to view logs"

down:
	@echo "🛑 Stopping all services..."
	docker-compose down

restart:
	@echo "🔄 Restarting services..."
	docker-compose restart

dev:
	@echo "🚀 Starting in DEVELOPMENT mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@make logs

prod:
	@echo "🚀 Starting in PRODUCTION mode..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# ============================================
# Data Management
# ============================================

init-data:
	@echo "📊 Running data initialization..."
	docker-compose up data-init

reset-data:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres; \
		sleep 5; \
		docker-compose up data-init; \
	fi

dbt-run:
	@echo "🔧 Running dbt transformations..."
	docker-compose exec api sh -c "cd dbt_project && dbt run"

embed:
	@echo "🧠 Regenerating vector embeddings..."
	docker-compose exec api python vector_store/llm_driven_embed.py

# ============================================
# Monitoring
# ============================================

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-mcp:
	docker-compose logs -f mcp-server

logs-postgres:
	docker-compose logs -f postgres

logs-init:
	docker-compose logs data-init

status:
	@echo "📊 Service Status:"
	@docker-compose ps

# ============================================
# Database Commands
# ============================================

db-shell:
	@echo "🗄️  Connecting to PostgreSQL..."
	docker-compose exec postgres psql -U dbank_user -d dbank

db-backup:
	@echo "💾 Backing up database..."
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U dbank_user dbank > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup saved to backups/"

db-restore:
	@echo "📥 Restoring database from latest backup..."
	@LATEST=$$(ls -t backups/*.sql 2>/dev/null | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "❌ No backup files found in backups/"; \
	else \
		echo "Restoring from $$LATEST"; \
		cat $$LATEST | docker-compose exec -T postgres psql -U dbank_user dbank; \
		echo "✅ Database restored"; \
	fi

# ============================================
# Testing
# ============================================

test:
	@echo "🧪 Running tests..."
	docker-compose exec api pytest tests/ -v

test-tools:
	@echo "🧪 Testing MCP tools..."
	docker-compose exec api python -m pytest tools/test_*.py -v

test-kb-search:
	@echo "🧪 Testing knowledge base search..."
	docker-compose exec api python tools/kb_search.py

test-kpi:
	@echo "🧪 Testing KPI tools..."
	docker-compose exec api python tools/kpi_tools.py

test-sql:
	@echo "🧪 Testing SQL query tool..."
	docker-compose exec api python tools/sql_query.py

# ============================================
# Cleanup Commands
# ============================================

clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker-compose down -v
	@echo "✅ Cleanup complete"

clean-all:
	@echo "🧹 Removing everything (containers, volumes, images)..."
	docker-compose down -v --rmi all
	@echo "✅ Complete cleanup done"

clean-logs:
	@echo "🧹 Cleaning log files..."
	find . -name "*.log" -type f -delete
	rm -rf dbt_project/logs dbt_project/target
	@echo "✅ Logs cleaned"

# ============================================
# Development Commands
# ============================================

shell-api:
	docker-compose exec api bash

shell-mcp:
	docker-compose exec mcp-server bash

shell-postgres:
	docker-compose exec postgres bash

# Format code
format:
	@echo "🎨 Formatting code..."
	docker-compose exec api black .
	docker-compose exec api isort .

# Check code quality
lint:
	@echo "🔍 Checking code quality..."
	docker-compose exec api flake8 .
	docker-compose exec api mypy .

# ============================================
# Health Checks
# ============================================

health:
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "API Health:"
	@curl -f http://localhost:8001/health 2>/dev/null && echo "✅ API is healthy" || echo "❌ API is down"
	@echo ""
	@echo "MCP Server Health:"
	@curl -f http://localhost:8000/health 2>/dev/null && echo "✅ MCP is healthy" || echo "❌ MCP is down"
	@echo ""
	@echo "Database Health:"
	@docker-compose exec -T postgres pg_isready -U dbank_user && echo "✅ Database is healthy" || echo "❌ Database is down"

# ============================================
# Quick Actions
# ============================================

# Quick start from scratch
quickstart: build up
	@echo ""
	@echo "⏳ Waiting for services to initialize..."
	@sleep 10
	@make health
	@echo ""
	@echo "🎉 dBank Copilot is ready!"

# Full reset and restart
reset: clean build up

# Update and restart
update:
	@echo "🔄 Pulling latest changes and restarting..."
	git pull
	docker-compose pull
	make rebuild
	make restart