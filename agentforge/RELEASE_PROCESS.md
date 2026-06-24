# Release Process

## Versioning

AgentForge AI follows [Semantic Versioning 2.0.0](https://semver.org/):

- **Major (1.x.0)**: Breaking changes to public API, database schema, or core behavior
- **Minor (x.1.0)**: New features, backward compatible
- **Patch (x.x.1)**: Bug fixes, security patches, performance improvements

Pre-release versions: `0.1.0-alpha.1`, `0.2.0-beta.1`

## Release Cadence

| Release Type | Cadence |
|---|---|
| Patch | As needed (bug fixes, security) |
| Minor | Monthly |
| Major | Quarterly (pre-1.0: as needed) |

## Release Workflow

### 1. Create Release Branch

```bash
git checkout develop
git pull
git checkout -b release/v0.2.0
```

### 2. Prepare Release

```bash
# Update version in:
# - package.json (root)
# - apps/api/package.json
# - apps/web/package.json

# Update CHANGELOG.md with new version, date, and changes

# Commit preparation
git add .
git commit -m "chore(release): prepare v0.2.0"
```

### 3. Final Testing

```bash
# Run full test suite
cd apps/api && pytest --cov=apps/api

# Run lint
cd apps/api && ruff check .
cd apps/web && npm run lint

# Build check
cd apps/web && npm run build

# Docker build check
docker compose build
```

### 4. Create Pull Request

Open a PR from `release/v0.2.0` → `main`:
- Title: `chore(release): v0.2.0`
- Include changelog summary in description
- Request review from maintainers

### 5. Tag and Release

```bash
# After PR is merged to main
git checkout main
git pull

# Tag the release
git tag -a v0.2.0 -m "v0.2.0 - [summary of changes]"
git push origin v0.2.0
```

### 6. Create GitHub Release

1. Go to GitHub Releases
2. Click "Draft a new release"
3. Select tag `v0.2.0`
4. Title: `v0.2.0`
5. Description: Copy changelog entry
6. Attach any artifacts (if applicable)
7. Publish release

### 7. Merge Back to Develop

```bash
git checkout develop
git merge main
git push
```

## Hotfix Process

For urgent fixes that cannot wait for the next release:

```bash
# From main branch
git checkout main
git checkout -b hotfix/critical-bug-fix

# Fix, commit, test
git commit -m "fix(api): critical bug fix description"

# Open PR to main (fast-track review)
# After merge, tag patch release
git tag -a v0.2.1 -m "v0.2.1 - critical bug fix"
git push origin v0.2.1

# Merge fix back to develop
git checkout develop
git merge main
git push
```

## Pre-Release Checklist

### Quality Gates
- [ ] All tests pass: `pytest`
- [ ] Coverage meets threshold: `pytest --cov=apps/api`
- [ ] Lint passes: `ruff check .`
- [ ] Type check passes: if applicable
- [ ] No known CVEs in dependencies
- [ ] Docker images build successfully

### Documentation
- [ ] CHANGELOG.md updated
- [ ] API reference updated (if endpoints changed)
- [ ] Migration guide updated (if schema changed)
- [ ] Upgrade instructions documented

### Operations
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Release tagged
- [ ] Release notes published on GitHub
