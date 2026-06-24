# AgentOS Setup & Verification Guide

This guide documents the procedures to run, verify, and deploy the AgentOS platform locally or using Docker containers.

---

## 1. Prerequisites
- **Python**: 3.11+ (virtual environment managed via `uv` recommended)
- **Node.js**: v20+ with `npm`
- **Docker** & **Docker Compose**
- **PostgreSQL** & **Redis** (if running locally outside Docker)

---

## 2. Running Locally (Development Mode)

### A. Environment Configuration
Create a `.env` file in the project root with the following variables:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/agents
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-claude-key
```

### B. Launching Database & Cache Services
Make sure local instances of Postgres and Redis are running and correspond to your `.env` connection paths.

### C. Launching the Backend Gateway
Activate your virtual environment and launch FastAPI:
```bash
# Verify uv is installed and install packages
uv pip install -r pyproject.toml --system

# Run database initializer (automatically maps schemas)
python -c "from apps.api.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Start the uvicorn development server
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### D. Launching the Next.js Frontend
In a separate terminal window, build/start the web panel:
```bash
# Navigate to web app
cd apps/web

# Install client packages
npm install

# Start Next.js development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 3. Running with Docker Compose (Production Bundle)

You can spin up all containers (Postgres, Redis, Backend, Frontend) with a single command:
```bash
# Build images and start services in the background
docker-compose up --build -d

# Verify all containers are running
docker-compose ps
```
Services overview inside container group:
- **Next.js Web Panel**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Gateway REST/WS**: [http://localhost:8000](http://localhost:8000)
- **PostgreSQL Port**: `5432`
- **Redis Port**: `6379`

---

## 4. Execution & Verification Tests

### Running Automated Test Suite
To verify memory CRUD, routing, and exception middlewares:
```bash
# Run pytest tests
.venv/Scripts/pytest -v
```
To run specific integration files:
```bash
# Verify project memories
.venv/Scripts/pytest tests/test_memories.py -v
```
