# Developer Experience (DX) Guide — AgentForge

**Last Updated:** June 2026

---

## Hot Reload Setup

### Running All Dev Servers

```bash
pnpm dev
```

This runs:
- **Next.js** on `:3000` with Turbopack (instant HMR)
- **FastAPI** on `:8000` with `uvicorn --reload` (auto-restart on file changes)
- **Packages** (`packages/db`, `packages/types`, `packages/ui`) in watch mode

Any change to `apps/web/`, `apps/api/`, or `packages/*/` triggers an automatic rebuild.

### Running Individually

```bash
pnpm dev:web    # Next.js only
pnpm dev:api    # FastAPI only
pnpm dev:packages  # Watch all packages
```

---

## Recommended VSCode Extensions

Create `.vscode/settings.json` at the project root:

```json
{
  "python.defaultInterpreterPath": "apps/api/.venv/bin/python",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "tailwindCSS.experimental.configFile": "apps/web/tailwind.config.ts",
  "prisma.fileWatcher": true,
  "files.associations": {
    "*.jinja2": "jinja"
  }
}
```

### Extensions to Install

| Extension | ID | Why |
|-----------|-----|-----|
| Pylance | `ms-python.vscode-pylance` | Python type checking |
| Ruff | `charliermarsh.ruff` | Python formatting + linting |
| Prisma | `Prisma.prisma` | Prisma schema syntax highlighting |
| Tailwind CSS IntelliSense | `bradlc.vscode-tailwindcss` | Tailwind class autocomplete |
| REST Client | `humao.rest-client` | Test API endpoints from `.http` files |
| Even Better TOML | `tamasfe.even-better-toml` | TOML support |
| Jinja | `wholroyd.jinja` | Jinja2 template syntax highlighting |

---

## Debugging LangGraph Graphs

### Local Tracing with LangSmith

1. Get a LangSmith API key from [smith.langchain.com](https://smith.langchain.com)
2. Add to `.env`:
```
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=agentforge-dev
```
3. Restart the API — LangGraph will automatically trace every run
4. View traces at https://smith.langchain.com

### Reading State Transition Logs

When tracing is enabled, each LangGraph node execution logs:
- **Input state** — what fields were available when the node started
- **Node output** — what the node returned
- **State updates** — which fields changed after the node ran
- **Router decision** — which edge was taken and why

To view logs locally without LangSmith:
```python
# In any node, add:
logger.info(f"[{node_name}] State keys: {list(state.keys())}")
logger.info(f"[{node_name}] Current step: {state.get('current_step')}")
logger.info(f"[{node_name}] Agent outputs: {list(state.get('agent_outputs', {}).keys())}")
```

### Common Debugging Commands

```python
# In apps/api/agents/graph.py, add this to debug conditional edges:
def review_router(state: AgentState) -> str:
    blocking = state["agent_outputs"].get("reviewer", {}).get("blocking_issues", [])
    logger.info(f"[review_router] Blocking issues found: {len(blocking)}")
    if blocking:
        return "backend_implement"
    return "qa"
```

---

## Inspecting WebSocket Frames

1. Open Chrome DevTools (F12) → **Network** tab
2. Filter by **WS** (WebSocket)
3. Click the connection to `ws://localhost:8000/ws/tasks/{task_id}`
4. Go to the **Messages** tab
5. Filter by `task_id` in the search bar
6. Each row shows: time, direction (↓ received, ↑ sent), message type, payload size

**Frame types to look for:**
- `task_started` — task began execution
- `agent_message` — token-level streaming (frequent, small payloads)
- `agent_complete` — end of an agent step
- `human_interrupt` — waiting for approval
- `task_complete` — final deliverable

---

## pnpm Workspace Gotchas

### Issue: Package not found after adding to workspace

**Fix:** Run `pnpm install` from root to symlink the new package.

### Issue: Changes in `packages/types` not reflected in `apps/web`

**Fix:** Ensure `packages/types` has a `build` script in its `package.json`, and that `apps/web/package.json` has `"@agentforge/types": "workspace:*"`. Then run `pnpm dev:packages`.

### Issue: TypeScript errors in package imports

**Fix:** Check the `exports` field in the package's `package.json`:
```json
{
  "exports": {
    ".": "./index.ts",
    "./*": "./*.ts"
  }
}
```

### Issue: Circular dependency between workspaces

**Fix:** AgentForge enforces: `packages/*` ← `apps/*`. Packages cannot import from apps. If you see a circular dependency, extract the shared code into a new package.

---

## Python venv in apps/api

```bash
# Create virtual environment (one-time)
cd apps/api
python -m venv .venv

# Activate
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

**Important:** Always activate the venv before running `pnpm dev:api` or `pnpm test:api`. The venv is gitignored — each developer creates their own.

---

## Handy Aliases

Add to your shell profile:

```bash
# AgentForge development
alias af-dev="cd ~/projects/agentforge && pnpm dev"
alias af-test="pnpm test:api && pnpm test:web"
alias af-db="pnpm db:migrate && pnpm db:generate"
alias af-logs="docker compose logs -f"
```
