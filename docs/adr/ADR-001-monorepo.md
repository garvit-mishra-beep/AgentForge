# ADR-001: Monorepo with Turborepo

## Status
Accepted

## Context
AgentForge AI consists of multiple applications (Next.js frontend, FastAPI backend) and shared packages (agent runtime, tools, memory, LLM abstractions). We need a repository structure that enables:

- Code sharing across applications (types, utilities, configurations)
- Unified versioning and release management
- Consistent tooling (linting, formatting, type-checking)
- CI/CD efficiency (caching, selective builds)
- Easy onboarding for new developers

## Alternatives Considered

### 1. Polyrepo (Separate Repos)
- **Pros**: Independent CI/CD, independent versioning, clear ownership boundaries
- **Cons**: Cross-repo changes require multiple PRs, harder to share types, dependency drift, complex local development setup

### 2. Monorepo with Nx
- **Pros**: Powerful computation caching, dependency graph visualization, extensive plugin ecosystem
- **Cons**: Heavier tooling, steep learning curve, Nx Cloud dependency for optimal caching

### 3. Monorepo with Turborepo (Selected)
- **Pros**: Lightweight, fast caching, zero-config for basic setups, native npm/pnpm workspaces support, Vercel ecosystem alignment
- **Cons**: Less mature than Nx, fewer plugins, caching requires remote cache for CI teams

### 4. Simple Workspace (npm/pnpm only)
- **Pros**: Minimal tooling, no extra dependency
- **Cons**: No caching, no dependency graph awareness, manual script orchestration

## Decision
Use **Turborepo** with npm workspaces.

Key configuration:
- `package.json` at root with `workspaces` field
- `turbo.json` for pipeline definitions
- Remote caching via Vercel (production) or local filesystem (development)
- Shared `tsconfig`, `eslint` config, and `prettier` config

## Consequences

### Positive
- Single `npm install` at root installs everything
- `turbo run dev` starts all applications with dependency ordering
- Build caching dramatically reduces CI times
- Shared TypeScript types flow naturally between packages
- easy to add new packages or applications

### Negative
- Repository size grows over time (mitigated by `.gitignore`, sparse checkout)
- CI requires more disk space for all dependencies
- Teams must coordinate on shared dependency upgrades

## Tradeoffs
- Turborepo was chosen over Nx for simplicity. If we later need fine-grained task orchestration or extensive plugin support, migration to Nx is straightforward since both work with npm workspaces.
- Remote caching adds a Vercel dependency. For self-hosted teams, Turborepo supports S3-compatible remote cache.

## References
- [Turborepo Documentation](https://turbo.build/repo/docs)
- [npm Workspaces](https://docs.npmjs.com/cli/v10/using-npm/workspaces)
