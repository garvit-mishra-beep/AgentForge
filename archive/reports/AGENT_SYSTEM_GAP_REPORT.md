# Agent System Gap Report

**Scope:** The seven agent roles currently in the graph — Team Lead (plan +
deliver), Builder, Reviewer, Tester, Security, Architect, Aggregator. Each
file is small (47–113 lines), each is structurally near-identical to the
others. That symmetry is both the system's strength and its biggest
weakness.

**Verdict:** The agent system has the right *shape* but under-uses the
language-model call it makes. Every node follows the same template:

```
load prompt → wrap inputs → call provider → wrap response → append message
```

There is no **tool use**, no **structured inter-agent dialogue**, no
**mid-graph memory retrieval**, and no **specialized tooling per role**.
The agents are differentiated only by their prompts, not by what they can
actually *do*.

---

## 1. The Current Graph

`apps/api/agents/graph.py`:

```
team_lead_plan → builder → [reviewer, tester, security, architect]
                              ↓ (parallel fan-out)
                          aggregator → team_lead_deliver
```

Routing after builder is dynamic based on `team_config` membership.

State: `apps/api/agents/state.py` — a `TypedDict` with plan, builder output,
review, tester/security/architect/aggregator outputs, delivery, current_step,
messages, errors, timeouts, repository_context, relevant_memories,
learned_signal.

---

## 2. Per-Agent Audit

### Team Lead (plan) — `team_lead_node.py`

**Does:** Receives task + repo context + relevant memories; produces a JSON
plan with `plan_summary` and `steps[]`.

**Weaknesses:**

- Plan is text-only. It has no structure the Builder can act on
  (file paths, signatures, contracts). A real plan should declare
  "modify these N files, add these tests".
- The plan has no acceptance criteria, so the Builder and Reviewer cannot
  verify completion.
- No fallback if the plan is malformed (the Builder silently proceeds with
  whatever JSON shape arrives).

### Builder — `builder_node.py`

**Does:** Receives plan; produces `BuilderOutput(summary, files[])`.

**Weaknesses:**

- The output schema requires `files[].path`, `content`, `language` — but
  *what files should change* is up to the model. The model often invents
  files or rewrites the wrong file.
- No file-existence check: the Builder is asked to "modify" files that may
  not exist, and the orchestrator never validates.
- No diff against the actual repo: if the Builder's plan references
  `apps/api/auth.py` but the file is at `apps/api/app/auth.py`, the user
  gets a delivery summary that doesn't match the actual codebase.
- No test generation. The Builder writes code but no tests. The Tester
  agent (next) is supposed to fill that gap, but in practice Tester
  re-reads the Builder output and writes hypothetical tests without running
  them.

### Reviewer — `reviewer_node.py`

**Does:** Receives builder output + learned_signal; produces `ReviewOutput`.

**Strengths:**

- Uses the validated `ReviewOutput` schema with severity normalization
  (TOP_FINDINGS #19 fixed).
- Wired to the feedback flywheel (`learned_signal`).
- Cap of 3 findings per review (good UX).

**Weaknesses:**

- No access to the actual repository. The reviewer reviews the *builder's
  text*, not the *files*. It cannot verify a bug claim by reading the
  surrounding code.
- `line` numbers in findings refer to the builder output, not to a real
  file. They are not actionable for the developer.
- No severity calibration. The model over-uses "critical".

### Tester — `tester_node.py`

**Does:** Writes tests as JSON.

**Weaknesses:**

- **Tests are never executed.** This is the single most embarrassing gap
  in the system. The Tester agent emits test code; nothing runs it.
- No coverage signal. No "this PR is 80% covered" output.
- No test-runner awareness. No way to tell "use pytest" vs "use jest" vs
  "use go test" without hard-coding.

### Security — `security_node.py`

**Does:** Reviews builder output for security issues.

**Weaknesses:**

- Text review only. No SAST integration (Bandit, Semgrep, CodeQL).
- No CVE / dependency-vulnerability scan.
- No secrets detection (the file_parser handles `text/plain`, so the user
  could paste a file with a hardcoded API key and Security agent might not
  flag it).

### Architect — `architect_node.py`

**Does:** Reviews the Builder's output for architectural fit.

**Weaknesses:**

- Operates on a single task's output, not on the *whole repository*. There
  is no "explain this repo's architecture" capability.
- `quality_score` field is unused. No route, no dashboard, no
  trend line.
- The role is opt-in via `team_config`. Most users never enable it because
  there is no UI surface for team composition beyond the
  `teams` route.

### Aggregator — `aggregator_node.py`

**Does:** Combines outputs from reviewer/tester/security/architect.

**Strengths:**

- Has a smart `_auto_aggregate` fallback (no LLM call) that uses the
  validated `ReviewOutput.verdict` field, not substring matching
  (TOP_FINDINGS #19).
- `overall_verdict` correctly considers all sources.

**Weaknesses:**

- When run with an LLM, the aggregator can overwrite a strict reviewer's
  "fail" verdict with a vague "review_needed" — a real risk.
- No de-duplication. If Reviewer and Tester both raise "missing test for
  X", the user sees it twice.
- No ranking by severity — findings arrive in arbitrary order.

### Team Lead (deliver) — `team_lead_node.py` (second node)

**Does:** Wraps up with a `delivery_summary` and `verdict`.

**Weaknesses:**

- The summary is text. The user gets "Here is what we built" but no diff,
  no file list with line counts, no list of changed files.
- No commit/PR link. The delivery is decoupled from GitHub.

---

## 3. Cross-Cutting Issues

### A-1 — No tool use

Agents cannot read files, run tests, grep the codebase, or query git. Every
agent call is "given a static prompt and static context, produce text". This
is the single largest reason output quality is uneven.

### A-2 — No structured inter-agent dialogue

Reviewer → Aggregator is the only edge with structured handoff. Tester and
Security emit JSON the Aggregator ignores for the most part. Reviewer never
sees Tester's output. Builder never sees Reviewer's findings during a
re-build (the graph has no retry-with-feedback edge today; `review_feedback`
is hardcoded to `""` in `builder_node.py`).

### A-3 — No retry / self-correction

If the Builder's output is malformed, the graph accepts it. If the
Reviewer's JSON has 30 findings when the cap is 3, the model just emits more.
There is no "validate output → if invalid, retry with stricter prompt"
loop.

### A-4 — No mid-graph memory retrieval

The orchestrator pulls `relevant_memories` once. None of the agents can
ask "give me more memories about X" mid-execution.

### A-5 — No symbolic reasoning

Every agent is a single LLM call. There is no:
- Plan-and-execute (Builder should plan + write + verify)
- Critic-revision (Reviewer should propose fix; Builder should revise)
- Self-consistency (run Builder twice, take the better)

### A-6 — No cost / latency observability per agent

`metadata.token_usage` and `metadata.duration_ms` are recorded in the
messages table, but no route or dashboard surfaces them. There's no
"Builder took 18s and cost $0.04" view.

---

## 4. Concrete Fixes Ranked by Impact

### A-7 — Wire the Builder's review feedback (P0)

Change `builder_node.py`:

```python
review_feedback = state.get("review_aggregator_output") or ""
```

…and on retry loops, pass the Reviewer's findings back to the Builder.
This is the smallest possible change with the largest effect on quality.

### A-8 — Run the Tester's tests (P0)

Add a `sandbox` service that executes the Tester-emitted tests in an
isolated environment (Docker container, Pyodide for JS, etc.) and captures
pass/fail counts. Surface as part of the delivery. This single change
repositions Tester from "writing fiction" to "validating reality".

### A-9 — Give agents file-reading tools (P0)

The Builder must be able to read existing files, not just hallucinate them.
The Reviewer must be able to grep the codebase, not just guess. Implement
this as a controlled toolset — read-only — that the agents can call via
the LangGraph `ToolNode` mechanism.

### A-10 — Validate every agent output (P0)

Before accepting a Builder / Reviewer / Tester response:

1. Parse JSON.
2. Validate against the Pydantic schema.
3. If invalid, retry once with a stricter prompt.

The code already has `parse_structured` in `agents/utils.py` — wire it
into every node. Today only the Aggregator uses it.

### A-11 — Add a re-review loop (P0)

The current graph is one-shot: plan → build → review → done. Add an
optional retry edge:

```
aggregator → (if blocking findings) → builder (with review feedback) → reviewer
```

Cap at 2 retries to bound cost.

### A-12 — Add SAST + secrets detection to Security agent (P1)

Don't reinvent. Call Bandit / Semgrep / gitleaks as subprocesses from the
Security node. Augment LLM output with their findings.

### A-13 — Track file paths and line numbers correctly (P1)

The Reviewer emits `line: 42` referring to the Builder's output. It should
emit line numbers referring to the *real file*. Force the Builder prompt to
return file paths that actually exist in the repo; have the orchestrator
verify before passing to Reviewer.

### A-14 — Add structured inter-agent protocol (P1)

Replace free-form `plan`, `builder_output`, `review` strings with typed
Pydantic messages that all nodes share:

```python
class AgentMessage(BaseModel):
    from_role: AgentRole
    to_role: AgentRole | None  # None = broadcast
    kind: Literal["plan", "code", "finding", "test_result", "summary"]
    payload: dict
    severity: Severity | None
```

### A-15 — Add Architect "whole-repo" mode (P1)

Add a route `POST /api/v1/repo/architect` that runs the Architect node
against the parsed repo, not a single task's output. This is what users
expect when they say "explain the architecture".

---

## 5. What is Already Good

- Prompts use the prompt-injection fence (`wrap_task`, `wrap_context`,
  `wrap_memories`).
- Timeouts are per-agent, configurable, and degrade gracefully
  (`timed_out_agents`).
- The Aggregator's `_auto_aggregate` is genuinely clever — it uses
  validated verdicts, not string matching.
- The Reviewer wires in the learned-signal flywheel.
- The Pydantic `agent_outputs.py` defines a shared contract.

---

## 6. Honest Assessment

The agent system is well-named (Team Lead, Builder, Reviewer, etc.) and the
graph topology is sensible. The implementation, however, treats agents as
*prompts* rather than as *actors*. The fix is not "more agents" — the prompt
explicitly forbids that — it's "make each existing agent actually able to do
something".

The four highest-leverage changes are:

1. **Run the tests.** (A-8) Tester that doesn't run tests is theatre.
2. **Give agents file-reading tools.** (A-9) Builder that can't read files
   hallucinates.
3. **Validate outputs.** (A-10) Reviewer that emits garbage shapes gets
   garbage downstream.
4. **Wire review feedback to Builder.** (A-7) Without this, every review is
   decorative.

These four changes are each small (1–2 weeks), all P0, and they
collectively transform the system from "agents that talk about code" to
"agents that operate on code".