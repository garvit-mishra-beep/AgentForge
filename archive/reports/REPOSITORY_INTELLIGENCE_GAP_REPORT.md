# Repository Intelligence Gap Report

**Scope:** Can AgentForge automatically understand an existing codebase before
working in it? This is the P0 foundation.

**Verdict:** AgentForge has the *scaffolding* for repository intelligence but
not the *engine*. Symbols, imports, dependencies, and chunks are persisted, but
they are never queried to drive decisions, never linked to a graph, and never
exposed to agents in a way that improves output quality. The system reads the
repo like a bag of files, not like a system of related parts.

---

## 1. What Exists Today

### Data model (good)

Migration `007_repository_context.sql` defines a clean schema:

- `repository_contexts` — one row per parsed file.
- `code_symbols` — functions, classes, methods, types.
- `code_imports` — `import` / `from … import` statements.
- `code_dependencies` — resolved cross-file references.
- `code_chunks` — content slices with line ranges and token estimates.

### Parser (partial)

`apps/api/app/file_parser.py` (399 lines) provides:

- Multi-language dispatch via extension map (covers Python, JS/TS, Go, Rust,
  Java, Ruby, PHP, C/C++, C#, Kotlin, Scala, Swift, SQL, Bash, YAML/JSON,
  HTML/CSS, Vue/Svelte).
- A working Python AST parser (`_parse_python`).
- A `_parse_generic` fallback for everything else.
- Emits `ParsedFile` dataclasses with symbols, imports, and chunks.

The README/code paths assert that the parser is "in use", but inspection of
`orchestrator.py` reveals only the SQL hook in `_fetch_repository_context`,
which pulls *chunks* (truncated content) — it does not consult symbols or the
dependency graph at all.

### Storage and ingestion (partial)

- `POST /projects/:id/files` accepts uploads; parsed results are inserted
  (see `routes/projects.py`).
- `repository_contexts` is queryable via `routes/context.py` (525 lines).

### What does NOT exist

- **No symbol-level graph.** The four tables (`symbols`, `imports`,
  `dependencies`, `chunks`) are independent — there is no `code_symbols` →
  `code_symbols` edge table, and `code_dependencies.depends_on_file_id` is a
  weak surrogate.
- **No cross-file reachability.** "What depends on this function?" cannot be
  answered in one query.
- **No blast-radius computation.** Before changing a symbol, there is no way
  to enumerate downstream call sites.
- **No architectural detection.** Layers, boundaries, and conventions are not
  inferred.
- **No ownership inference.** Git blame is never read; CODEOWNERS is not
  consumed.
- **No risky-file scoring.** Criticality is purely importance-based on
  memories.
- **No language-aware context selection.** The same flat list of chunks is
  returned regardless of whether the agent is modifying Python or TypeScript.

---

## 2. Specific Gaps Ranked by Impact

### R-1 — No dependency graph traversal (P0)

Today the dependency table is *populated* but never *traversed*. An agent
asked to "fix the cache invalidation in `cache.py`" has no way to know which
functions across the codebase call into it. This is the single largest gap.

**Effort to close:** 2–3 weeks. Either:
- Add a `code_edges` table (source_symbol → target_symbol) and recursive CTE
  for reachability, **or**
- Adopt a graph layer (Neo4j, Memgraph, Kùzu) as a derived index from the
  existing tables.

### R-2 — No "explain this repo" capability (P0)

There is no route, agent, or prompt that takes "explain how this codebase is
organized" and returns a layered summary. The README claims
"Multi-Agent Teams" with an Architect role, but `architect_node.py` operates
only on a single task's plan/output, never on the whole repository.

**Effort:** 1–2 weeks. Add a `POST /repo/explain` route that runs the
Architect node against a synthesized view of the parsed repo (top-level
modules, layer inference, dependency clusters).

### R-3 — No architectural pattern detection (P1)

Patterns like "this is a layered FastAPI service", "this is a Next.js
App-Router project", "monorepo with pnpm workspaces" are not detected. Agents
have to guess from filename strings. A small rule engine plus embeddings on
top-level directories would be sufficient.

### R-4 — No risky-file / critical-module scoring (P1)

There is no signal for "this file is central to the system". Candidates:

- PageRank over the symbol graph (after R-1).
- Cross-reference count (churn × fan-in).
- Memory-based importance (already exists in `agent_memories.importance` but is
  task-scoped, not module-scoped).

### R-5 — No incremental re-indexing (P1)

`file_parser.py` re-parses an entire file on each upload. There is no
incremental AST diff. For a 5k-file repo, this is fine; for 50k files it is
unacceptable. Realistic V1 fix: hash + mtime cache.

### R-6 — No ownership / contribution signal (P1)

Git is not consumed. `git blame` is never invoked. CODEOWNERS is not parsed.
The Builder agent has no way to say "this is mostly maintained by Alice;
follow her style."

### R-7 — The Python parser is robust; the generic parser is not (P1)

`_parse_python` uses the `ast` module — solid. `_parse_generic` is a regex
heuristic that emits "function"-typed chunks based on indentation alone. For
real adoption, the parser must either:

- Shell out to `tree-sitter` (polyglot, fast, well-tested), **or**
- Use language-server Protocol (LSP) where available.

### R-8 — No "what changed since last review" surface (P1)

When a developer asks for a re-review, the agent has no easy way to compute
the diff since the last successful review. There is no `last_indexed_sha`
column on `repository_contexts`.

---

## 3. What is Already Good

- The schema is correct. `symbols`, `imports`, `dependencies`, `chunks` is
  the right decomposition.
- The parser handles ~30 languages by extension dispatch.
- The Python AST path is genuinely correct (no regex hacks for Python).
- Tenant isolation is enforced on context routes.
- File upload has MIME allowlisting and path-traversal guards.

---

## 4. Architecture Recommendations (P0)

1. **Add `code_edges` (source → target symbols).** Migration 018. Cheap,
   unblocks every downstream capability.
2. **Add `repository_insights` table** with precomputed aggregates:
   symbol count, fan-in, fan-out, file risk score, language breakdown.
3. **Add a `repo_graph` service** that exposes:
   - `get_callers(symbol_id)` — recursive CTE.
   - `get_callees(symbol_id)`.
   - `explain_module(path)` — top-level summary.
   - `find_cycles(path)` — circular dependency detection.
4. **Wire the existing nodes to query the graph.** The Reviewer and Builder
   prompts already receive a `repository_context` field — replace the
   flat-chunk string with a structured slice ("here are the 5 functions in
   this file that depend on what you are about to change").
5. **Adopt tree-sitter** for non-Python languages. Treat it as a dependency,
   not a rewrite — `file_parser.py` can keep its existing dispatch.
6. **Add a `POST /repo/explain` route** running the Architect node over the
   whole repo, returning a layered architecture summary.

---

## 5. Metrics for "Done"

| Metric | Target |
|--------|--------|
| "What calls this function?" queryable in O(fan-in) | <50ms p95 |
| "Explain this repo" returns layered summary | <10s for 10k-file repo |
| Incremental re-indexing of a single file | <200ms p95 |
| Tree-sitter coverage of the 30 declared languages | ≥95% of LOC |
| Symbol graph reflects actual imports | ≥98% precision |

---

## 6. Honest Assessment

The current `repository_contexts` system is closer to "code storage with a
nice schema" than "repository intelligence". It does not yet influence agent
output in measurable ways, and no agent prompt asks for symbols, dependencies,
or call sites.

The path from here to "real repo intelligence" is short — most of the schema
and infrastructure is already in place — but it requires (a) one focused
migration, (b) one graph-query service, (c) one rewrite of how agents receive
context, and (d) tree-sitter adoption. None of these are large on their own;
together they are a 4-week P0 effort.