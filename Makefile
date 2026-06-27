.PHONY: install test lint typecheck security docker dev run clean benchmark benchmark-mock benchmark-load eval

# ── Python (API) ────────────────────────────────────────────────────

install:
	cd apps/api && pip install -r requirements.txt

test:
	cd apps/api && python -m pytest tests/ -v --tb=short --cov=app --cov=core --cov=agents --cov=models --cov-report=term

lint:
	cd apps/api && ruff check .

format:
	cd apps/api && ruff format .

typecheck:
	cd apps/web && npx tsc --noEmit

security:
	cd apps/api && bandit -r . --severity-level high --confidence-level high
	cd apps/api && safety check --full-report || true

# ── Docker ──────────────────────────────────────────────────────────

docker-build:
	docker build -t agentforge-api:latest -f Dockerfile .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# ── Local Dev ───────────────────────────────────────────────────────

dev:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	cd apps/api && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# ── Benchmarks ──────────────────────────────────────────────────────

benchmark:
	cd apps/api && python -m benchmarks.runner

benchmark-mock:
	cd apps/api && python -m benchmarks.runner --mock --out benchmark_results.json

benchmark-load:
	cd apps/api && python benchmark_load.py --users 5 --duration 10

# ── Evals ───────────────────────────────────────────────────────────

eval:
	cd apps/api && python -m evals.harness

# ── Housekeeping ────────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

pre-commit:
	pre-commit run --all-files

pre-commit-install:
	pre-commit install
