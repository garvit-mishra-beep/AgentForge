# AgentForge — Feature Gap Analysis (2026-06-26)

Effort: S (<1 wk) / M (1–3 wk) / L (>3 wk). Priority blends user value × business value ÷ effort.
Classification: **QW** = Quick Win, **MW** = Medium Win, **MB** = Major Bet.

## Quick Wins (do first)
| Feature | Impact | Effort | Why |
|---|---|---|---|
| Fix file-download/task IDOR + ownership audit | Critical | S | Unblocks any real multi-tenant use |
| Add Redis to docker-compose | Critical | S | App actually boots for anyone |
| Add `tasks/executions(created_by)` indexes | Med | S | Avoids seq scans at scale |
| Refresh-token revocation + `/logout` | High | S/M | Real session security |
| Client route guards + 401→login redirect | High | S | Removes dead-ends |
| Persist Quick-Review history server-side | High | S/M | First real retention hook |
| Externalize rate-limit/metrics to Redis | High | M | Unblocks horizontal scale |
| `aiofiles`/`to_thread` for file I/O | Med | S | Stops event-loop stalls |
| Prompt-injection delimiting + length caps | High | S | Closes the biggest AI attack surface |
| Make CI gates blocking (drop `|| true`) | Med | S | Stops regressions merging |

## Medium Wins
| Feature | Impact | Effort | Why |
|---|---|---|---|
| **GitHub App / PR review bot** | Very High | M/L | Meets devs where they work; retention + virality |
| **CLI + IDE entry point** for Quick Review | Very High | M | Competes where Cursor/Copilot live |
| Collapse review fan-out → 1–2 critics + repair loop | High | M | Real multi-agent value, lower token cost |
| Wire memory into builder+critic; pgvector embeddings | High | M | Memory that actually improves runs |
| Honest benchmark vs single-model on labeled dataset | High (credibility) | M | Replaces the fictional "40%" |
| HttpOnly-cookie auth | High | M | Kills XSS token theft |
| Route-level tests for `/projects`,`/context` + failure paths | Med | M | Covers the riskiest, least-tested surface |
| Sandboxed test execution (make `tester` real) | Med | M/L | Turns a dead agent into a differentiator |
| Stuck/timeout/cancel UI for executions | Med | S/M | Trust in long-running runs |
| Email verification + forgot-password + GitHub OAuth | Med | M | Table-stakes auth + PR-integration enabler |

## Major Bets
| Feature | Impact | Effort | Why |
|---|---|---|---|
| **Repo-aware agentic edits** (clone → plan → multi-file patch → PR) | Very High | L | The actual Devin/Cursor-Agent battlefield |
| Quality moat: continuously-learning critic from accepted/rejected findings | High | L | Turns memory into a defensible data flywheel |
| Team/org workspaces with shared memory + RBAC | High | L | Monetizable B2B tier (needs real RBAC first) |
| Multi-model routing/cost optimization per task | Med | L | Cost story for paying teams |
| Eval harness as a public leaderboard | Med | L | Credibility + marketing in one |

## The uncomfortable strategic read
Most "missing features" are **table stakes vs. competitors**, not differentiators. The only path to
a defensible product is the **quality flywheel** (Major Bet #2): capture which findings developers
accept/reject and feed that back into the critic. Everything else (PR bot, CLI, agentic edits) is
necessary to be *in the game* but is being built faster, with more capital, by Cursor/Devin/Copilot.
Prioritize: (1) become trustworthy (fix P0/P1), (2) ship the one wedge (Quick Review in the dev's
workflow via GitHub/CLI), (3) build the data flywheel that no incumbent has for *your* users.
