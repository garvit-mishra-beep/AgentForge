# AgentForge — Product Audit (2026-06-26)

## What problem does it claim to solve?
"Multi-agent AI team that writes and reviews code better than a single model." In practice the repo
contains two distinct products bolted together:

1. **Quick Review** — paste code → multi-lens LLM review, no login. *Real, focused, shippable.*
2. **Agent Team Builder** — create a team of roles/models, submit tasks, watch a pipeline execute.
   *Impressive demo, unproven value, heavier UX.*

## Claims vs. reality (the credibility problem)

The repo root holds ~40 self-authored strategy/audit/PRD docs. The recurring headline claims:

| Claim (source) | Reality (evidence) |
|---|---|
| "**40% more bugs caught** than single-model" (`BENCHMARK_SHOWCASE_PRD.md`, `INVESTOR_READINESS_REPORT.md`) | **Hardcoded JSON** in the PRD (`single_model_bugs_found:70, agentforge_bugs_found:98`). **No script computes it.** No result files exist. |
| "8.5/10 production-ready" (`FINAL_8_5_READINESS_REPORT.md`) | IDOR + no token revocation + Redis missing from compose + in-mem metrics. Not production-ready multi-tenant. |
| "Scientific benchmark suite" (`benchmark_scientific.py`) | Defines ~20 tasks then **stops** — no evaluation/grading logic. Abandoned mid-file. |
| "Pipeline catches bugs" (`benchmark_simplified.py`) | "Quality" = counting JSON keys + substring `'"verdict": "pass"'` + `output_length // 200`. **No ground-truth labels, no dataset.** |
| TP>60% / FP<10% targets (`PMF_ACCELERATION_PLAN.md`) | No code measures TP/FP. No labeled dataset is integrated. |

**The `uploads/` directory is the tell:** 64 dirs, each containing only `hello.py` (`def hello(): pass`)
or a trivial `auth_service.py`. The product has been exercised against **toy fixtures**, never against
real, bug-bearing code. There is **no evidence of real usage or validated quality**.

To its credit, `AGENTFORGE_STRATEGIC_VALIDATION_AUDIT.md` is **internally honest** ("uniqueness ≠
differentiation", high failure probability). The dishonesty is concentrated in the investor/benchmark
PRDs, where unmeasured numbers are presented as results.

## PMF / funnel assessment

- **Target user:** individual developers / small teams wanting AI code review.
- **Time-to-first-value:** *excellent for Quick Review* (no login, one paste). *Poor for Team Builder*
  (create team → add roles/models → create task → wait on pipeline).
- **Activation:** Quick Review can be tried anonymously (`app/page.tsx`), the right instinct.
- **Retention:** **no retention mechanic and no users.** Review history is `localStorage`-only
  (`app/page.tsx:87-97`) — lost on browser change; nothing pulls users back.
- **Discoverability:** landing page is clear and well-structured; the *real* product (Team Builder)
  is heavier than the landing implies.

## Missing / low-value / confusing

- **Missing:** persistent review history (server-side), GitHub/PR integration, IDE/CLI entry point,
  any retention loop, real benchmark/quality proof.
- **Low-value:** `tester` agent (proposes tests, never runs them); `architect` vs `reviewer` overlap;
  the `/demo` page is a pure client-side animation (`lib/demo-data.ts`), not the real product.
- **Confusing:** two products (Quick Review vs Team Builder) with one navigation; users won't know
  which is "the thing."
- **Unnecessary complexity:** 8-node pipeline where 1–2 critic passes + a repair loop would do.

## Strongest reason to use it
**Quick Review**: zero-friction, in-browser, multi-perspective LLM review of a code snippet.

## Biggest reason to abandon it
**No proof it beats a single Claude/GPT call**, while costing more tokens and living outside the
editor where developers already get Cursor/Copilot/Claude Code for free-to-cheap.

## Recommendation
Reposition around **Quick Review** as the product. Demote Team Builder to an advanced mode. Stop
publishing unmeasured numbers; ship one **honest** benchmark on labeled code and let it speak.
