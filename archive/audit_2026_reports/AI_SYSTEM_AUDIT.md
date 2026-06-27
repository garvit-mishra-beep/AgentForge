# AgentForge — AI System Audit (2026-06-26)

Scope: `apps/api/agents/` (`graph.py`, `orchestrator.py`, `state.py`, `utils.py`, `nodes/*`,
`prompts/*`) and `apps/api/app/memory_service.py`, `core/providers.py`, `core/model_registry.py`.

## The orchestration is real (not theater)

`apps/api/agents/graph.py:29-68` builds a genuine LangGraph `StateGraph`:

```
team_lead_plan → builder → [conditional fan-out] → {reviewer, tester, security, architect}
                                                    → aggregator → team_lead_deliver → END
```

- All nodes call a real provider via `call_with_timeout()` (`agents/utils.py:49-71`).
- Providers are real SDK clients (`core/providers.py`): OpenAI (`AsyncOpenAI`), Anthropic
  (`AsyncAnthropic`), Google, Ollama (`httpx`). **No mock/stub returns in the production path** —
  mocks exist only in tests (`tests/test_graph.py`, `tests/test_e2e_full_flow.py`).
- `fast_demo_mode` (`core/config.py:38`) only shrinks `max_output_tokens`; it does **not** fake output.

So the headline architecture is implemented as advertised. The problem is **value, not honesty**.

## Per-agent assessment

| Agent (node file) | Real LLM call? | Actual contribution | Redundancy / problem |
|---|---|---|---|
| `team_lead_plan` (`team_lead_node.py:12-58`) | Yes | Decomposes task into a plan; **the only node that receives `relevant_memories`** | Core. Keep. |
| `builder` (`builder_node.py:12-58`) | Yes | Generates code from the plan | Core. Keep. **Does not see memory or reviewer feedback.** |
| `reviewer` (`reviewer_node.py:11-51`) | Yes | Verdict + ≤3 findings on builder output | Overlaps security + architect |
| `security` (`security_node.py:11-46`) | Yes (optional) | OWASP-style review of the *same* builder output | **High overlap with reviewer** |
| `architect` (`architect_node.py:11-46`) | Yes (optional) | Design/structure review of the *same* output | **High overlap with reviewer** |
| `tester` (`tester_node.py:11-46`) | Yes (optional) | Proposes a test plan (not executed) | Could fold into builder; tests are never run |
| `aggregator` (`aggregator_node.py:12-96`) | Sometimes | LLM synthesis **if** an aggregator role is configured; otherwise `_auto_aggregate()` does mechanical JSON key extraction + string join | Weak when it falls back |
| `team_lead_deliver` (`team_lead_node.py:61-110`) | Yes | Final verdict/summary | Core. Keep. |

### The core design flaw
Reviewer, security, architect, and tester **all receive the same inputs** (`task`, `plan`,
`builder_output`) and run in parallel. There is:

- **No specialization gradient** — each is just a differently-prompted pass over identical context.
- **No build↔review loop** — builder generates once; reviewers cannot send it back for repair.
- **~4× token cost** for the review fan-out with no demonstrated quality gain.
- **Aggregation that may be string concatenation** (`aggregator_node.py:71-96`):
  ```python
  return json.dumps({"sources": [...], "verdicts": verdicts,
      "summary": f"Aggregated {sum(1 for v in verdicts if v)} outputs",
      "overall_verdict": "pass" if all("fail" not in v.lower() for v in verdicts) else "review_needed"})
  ```
  A single substring scan for `"fail"` decides the overall verdict in the fallback path.

## Prompt quality

Prompts (`agents/prompts/*.jinja2`) are **thin** (15–35 lines), no few-shot examples, no
chain-of-thought scaffolding, no severity rubric for findings. `security.jinja2` and
`architect.jinja2` are the most substantive (explicit OWASP / design criteria). User and file
content are interpolated directly (see prompt-injection finding in SECURITY_AUDIT.md).

## Memory integration — the biggest waste

- **Write path:** `orchestrator.py:203-295` stores plan/builder/review/delivery as memories after each run. Works.
- **Read path:** `orchestrator.py:96-106` → `get_relevant_memories()` (`memory_service.py:112-162`)
  retrieves before the run. Works.
- **But:** only `team_lead.jinja2:10-14` actually consumes `relevant_memories`. **Builder, reviewer,
  tester, security, architect, aggregator never see retrieved memory.** Memory is effectively
  write-mostly for 7 of 8 agents.
- **Retrieval is keyword ILIKE matching** (`memory_service.py:~98-110`: split context into words >3
  chars, `key/content ILIKE %kw%`). No embeddings, no semantic similarity, no relevance scoring
  beyond `ORDER BY importance DESC, created_at DESC`. The WHERE clause is assembled by
  `' AND '.join(conditions)` (string-built, though values are still `$N`-parameterized).

## Does multi-agent provide measurable value?

**Not as currently built, and there is no measurement proving it does.** A single high-context
model call could produce plan + code + review + tests + security notes in one pass for a fraction
of the tokens. The fan-out buys parallel wall-clock *only if* the runtime executes the branches
concurrently (LangGraph can) — but no latency/quality metric in the repo demonstrates a win, and
the "40% more bugs" claim is hardcoded (see PRODUCT_AUDIT.md). This is **sophisticated engineering
optimizing for architectural elegance over user/token value**.

## Recommended changes

1. **Collapse the review fan-out** to **one "critic" pass with a structured rubric** (or at most
   two: correctness + security), then keep a real **build→critic→repair loop** (1–2 iterations).
   This is where multi-agent earns its cost — iteration, not redundancy.
2. **Feed retrieved memory to builder and the critic**, not just the planner.
3. **Replace keyword memory retrieval with embeddings** (pgvector) + a relevance threshold.
4. **Make `tester` actually run tests** in a sandbox, or delete it — a proposed-but-unexecuted test
   plan is low value.
5. **Always use an LLM aggregator** (or delete aggregation and let `team_lead_deliver` synthesize);
   the string-concatenation fallback should never decide a verdict.
6. **Instrument quality**: log per-agent findings, dedupe rate, and run an honest A/B (single call
   vs. pipeline) on a labeled dataset before claiming superiority.

## 5-line verdict

The AI system is **real but architecturally wasteful**: real LangGraph, real multi-provider LLM
calls, no fakery — but four redundant parallel reviewers over identical context, a missing
build↔review loop, an aggregator that degrades to substring matching, and a memory subsystem read
by only one of eight agents. As designed it likely has **negative token ROI** versus a single
strong model call, and nothing in the repo measures otherwise. The path to value is **iteration and
specialization**, not breadth: fewer agents, a repair loop, embeddings-backed memory wired into the
builder, and an honest benchmark.
