# Contributing

## Local Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-org/agentforge.git
cd agentforge

# Copy environment file
cp .env.example .env

# Start infrastructure
docker compose up -d postgres redis qdrant

# Install backend dependencies
cd apps/api
pip install -r requirements.txt

# Install web dependencies
cd apps/web
npm install

# Run migrations
cd apps/api
alembic upgrade head
```

## Coding Standards

### Python (Backend)
- **Formatter**: [Ruff](https://docs.astral.sh/ruff/)
- **Type hints**: Required for all function signatures
- **Async**: Use `async/await` for I/O-bound operations
- **Imports**: Standard library → third-party → local (absolute imports)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Docstrings**: Google-style for public APIs

### TypeScript/React (Frontend)
- **Formatter**: Prettier with Tailwind CSS plugin
- **TypeScript**: Strict mode enabled
- **Components**: Functional components with hooks
- **State**: Zustand for global state
- **Styling**: Tailwind CSS

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, semicolons)
- `refactor`: Code change that neither fixes nor adds
- `test`: Adding or updating tests
- `chore`: Maintenance, dependencies, CI
- `perf`: Performance improvement
- `security`: Security fix
- `ops`: Operations and infrastructure

### Scopes
- `api` — Backend API
- `web` — Frontend
- `packages` — Shared packages
- `docs` — Documentation
- `infra` — Infrastructure (Docker, CI)
- `config` — Configuration

### Examples
```
feat(api): add agent invocation rate limiting
fix(web): resolve infinite re-render in workflow editor
docs(api): update authentication flow documentation
security(api): validate JWT audience and issuer claims
```

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready, protected |
| `develop` | Integration branch |
| `feat/*` | Feature branches |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation |
| `release/*` | Release preparation |

### Workflow
```mermaid
gitGraph
    commit
    branch develop
    checkout develop
    branch feat/new-agent-endpoint
    checkout feat/new-agent-endpoint
    commit
    commit
    checkout develop
    merge feat/new-agent-endpoint
    branch release/v0.2.0
    checkout release/v0.2.0
    commit
    checkout main
    merge release/v0.2.0
    tag "v0.2.0"
```

## Pull Request Workflow

1. **Create a branch** from `develop`:
   ```bash
   git checkout develop
   git pull
   git checkout -b feat/my-feature
   ```

2. **Make changes** and commit following commit conventions.

3. **Run tests** before pushing:
   ```bash
   cd apps/api && pytest
   cd apps/web && npm run lint
   ```

4. **Push and open a PR** to the `develop` branch:
   ```bash
   git push -u origin feat/my-feature
   ```

5. **PR Requirements**:
   - Title follows commit conventions
   - Description explains the change and motivation
   - All CI checks pass (tests, lint, type-check)
   - At least one review approval
   - No merge conflicts with `develop`

6. **Merge** using "Squash and Merge".

## Code Review Guidelines

- Review for correctness, security, and performance
- Check that tenant isolation is maintained
- Verify error handling covers failure paths
- Ensure observability (logging/metrics) is added for new operations
- Confirm documentation is updated for API changes

## Testing Guidelines

- Write tests for new features and bug fixes
- Aim for 80%+ coverage on backend code
- Use `pytest-asyncio` for async test support
- Mock external services (LLM, Qdrant, Redis) in unit tests
- Add integration tests for cross-service flows

## Need Help?

- Check [docs/](docs/) for detailed documentation
- Open a [Discussion](https://github.com/your-org/agentforge/discussions)
- File an [Issue](https://github.com/your-org/agentforge/issues) for bugs
