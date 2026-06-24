.PHONY: dev dev-api dev-web build test lint clean migrate

# Start all services via Docker Compose
dev:
	docker compose up -d
	@echo "Waiting for services..."
	@sleep 5
	$(MAKE) dev-api

# Start API locally (requires Docker services running)
dev-api:
	cd apps/api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start web locally
dev-web:
	cd apps/web && npm run dev

# Build all Docker images
build:
	docker compose build

# Run tests
test:
	cd apps/api && python -m pytest

# Lint code
lint:
	cd apps/api && ruff check .
	cd apps/web && npm run lint

# Clean up
clean:
	docker compose down -v
	rm -rf apps/web/.next
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# Install dependencies
install:
	cd apps/web && npm install
	cd apps/api && pip install -r requirements.txt 2>/dev/null || true

# Seed database with sample data
seed:
	cd apps/api && python scripts/seed.py

# Alembic migrations
migrate:
	cd apps/api && alembic upgrade head

migrate-downgrade:
	cd apps/api && alembic downgrade -1

migrate-revision:
	cd apps/api && alembic revision --autogenerate -m "$(message)"

migrate-current:
	cd apps/api && alembic current

migrate-history:
	cd apps/api && alembic history
