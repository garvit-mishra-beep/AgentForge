# GitHub Integration Gap Report

**Scope:** What does AgentForge need to feel GitHub-native — to fit into the
PR review workflow a developer already lives in, rather than asking them to
come to AgentForge?

**Verdict:** AgentForge has the *minimum viable plumbing* for a GitHub App PR
review bot. It can post a review, post a check run, and verify webhooks. It
cannot do most of what a developer expects from a real PR review tool. The
gap between "it works on a hello-world PR" and "I trust it on my team's real
PRs" is the entire P1 surface.

---

## 1. What Exists Today

### GitHub App authentication (good)

`apps/api/app/integrations/github.py`:

- RS256 app JWT minting with clock-skew tolerance (`iat - 60s`).
- `GitHubClient` with installation-token exchange.
- Webhook signature verification (`X-Hub-Signature-256`, constant-time).
- Thin `httpx.AsyncClient` wrapper.

### Webhook + queue (good)

`apps/api/app/routes/github.py`:

- `POST /integrations/github/webhook` — HMAC-verified, dispatches to
  `tracker.create_task` so the 202 returns inside GitHub's timeout.
- `GET /integrations/github/status` — boolean "configured" check.
- Background task calls `handle_pull_request_event`.

### Reviewer + check run (works, narrow)

`default_pr_reviewer` calls the configured model (`github_review_model`),
fences the diff (`wrap_untrusted`, max 12k chars), parses the result via
`ReviewOutput`, and emits findings with severity, file, line, suggestion.

`_findings_to_comments` maps findings to inline review comments.
`create_review` posts the review with `REQUEST_CHANGES` if any critical/high
finding, otherwise `COMMENT`. `create_check_run` posts
`success`/`failure`/`neutral`.

### Storage (good)

Migration `017_github_integration.sql`:

- `github_installations` — installation ID, account, optional user.
- `github_review_runs` — repo, PR, head SHA, files reviewed, findings count,
  blocking count, timestamp.
- Index on `(repo, pr_number)`.

---

## 2. Specific Gaps Ranked by Impact

### G-1 — No diff-aware context (P0)

The PR review bot feeds the model `patch` text alone. There is no access to
the rest of the file, no call graph, no symbol resolution, no tests, no
documentation. Result: findings are good for "obvious bugs" but useless for
"this breaks the cache contract documented elsewhere".

**Effort:** 2 weeks. Pull the file (not just the diff) for any file touched
by the PR. Combine diff + symbol resolution + tests touching that file.
Requires R-1 (the dependency graph).

### G-2 — No incremental / push-triggered review (P0)

The webhook handler only acts on `pull_request` `opened`/`synchronize`/
`reopened`. It ignores:

- `pull_request_review_comment` (developer asks AgentForge a question on a
  review comment).
- `issue_comment` (developer types `/agentforge review` on a PR comment).
- Pushes to a branch without a PR (early feedback).

**Effort:** 1 week. Add handlers for these events.

### G-3 — No suggested changes / patches (P0)

`Finding.suggestion` is plain text. Modern PR review tools (GitHub Copilot
Review, Graphite Reviewer, Coderabbit) post **suggested code blocks** that
the developer can apply with one click. AgentForge does not.

**Effort:** 1 week. When a finding has both a `line` and a `suggestion`,
post it as a `suggestion` block (the GitHub API supports this).

### G-4 — No PR summary / "what changed" (P0)

The current bot posts one big review with `summary` + inline comments.
Modern bots post a top-level summary first ("This PR adds X, refactors Y,
and removes Z. Findings: 3 high, 2 medium.") before findings. This makes
the review readable in mobile / list view.

**Effort:** 1 week. Add a one-shot LLM call to summarize the diff first.

### G-5 — No conversation / follow-up (P1)

If a developer replies to a finding with "@agentforge why?", the bot stays
silent. The webhook ignores `issue_comment` events and there is no
`/agentforge` command handler.

**Effort:** 2 weeks. Webhook handler + intent detection + threaded reply.

### G-6 — No branch awareness (P1)

The bot has no concept of "default branch" or "main vs feature branch". It
will happily review any PR. A real tool ignores PRs against `main` by
default, or refuses to review PRs larger than N lines without an explicit
request.

**Effort:** 1 week. Configurable rules in `github_installations`.

### G-7 — No re-review / status updates (P1)

After a developer pushes a fix, AgentForge will re-review (because of the
`synchronize` action). But it does not update the *existing* check run to
"now passing" — it creates a new one. PRs end up with dozens of stale
check runs.

**Effort:** 1 week. Track the latest `check_run_id` per `(repo, pr,
head_sha)` and update rather than recreate.

### G-8 — No review analytics surface (P1)

`github_review_runs` records the run, but no route or dashboard summarizes
"AgentForge posted 124 findings last week, 38% accepted, 12% rejected, 50%
ignored". The data is there; the surface is missing.

**Effort:** 1 week. Add `/integrations/github/analytics` route and a
dashboard card on the existing `analytics` page.

### G-9 — No multi-file / cross-file reasoning (P1)

The current bot reviews one file's diff at a time and concatenates findings.
It has no concept of "this PR changes three files that must be in sync".
Requires the symbol graph (R-1).

### G-10 — No installation flow from the web app (P1)

The web app has a `settings` page, but no "Connect GitHub" button. The bot
can be installed only by manually configuring env vars and pointing the
App's webhook URL at the server.

**Effort:** 2 weeks. GitHub App OAuth flow in the web UI.

### G-11 — No check suite / required check support (P2)

Real teams want AgentForge as a *required* check on `main`. Today the bot
posts a check run but doesn't expose a way to make it required.

### G-12 — No CODEOWNERS integration (P2)

GitHub has CODEOWNERS files; AgentForge doesn't read them. Combined with R-6
(no ownership signal), this is a coherent gap.

---

## 3. What is Already Good

- Webhook signature verification is correct (constant-time HMAC).
- App JWT minting is correct (clock-skew aware).
- The PR review pipeline runs asynchronously, so GitHub's 10s webhook timeout
  is never blown.
- Findings use the validated `ReviewOutput` schema (TOP_FINDINGS #19 fixed).
- Inline review comments are only posted when a finding has a `line`.
- `REQUEST_CHANGES` is used automatically for blocking findings.
- `github_review_runs` is indexed on `(repo, pr_number)`.

---

## 4. Architecture Recommendations

1. **Adopt GitHub's Check Run API as the canonical surface.** Stop creating
   new check runs on every push; update the existing one.
2. **Add `/agentforge` slash command support.** Reply to comments, ask
   follow-ups, request re-reviews.
3. **Post suggested code blocks** for any finding with a patch.
4. **Web-side OAuth flow** so installation is one click.
5. **PR summary first, then findings.** Two-pass: summary, then per-file
   review.
6. **Branch awareness + size guardrails** in installation config.
7. **Review analytics dashboard** on top of `github_review_runs`.

---

## 5. Metrics for "Done"

| Metric | Target |
|--------|--------|
| Time from `pull_request.opened` to first review posted | <60s |
| PR summary on every review | 100% |
| Suggested-code adoption rate (developer applies the patch) | ≥20% |
| Conversation threads supported (`@agentforge`) | All event types |
| Required-check support on `main` | Configurable per installation |

---

## 6. Honest Assessment

The plumbing is solid. What's missing is the *product surface* that makes the
bot feel like a teammate rather than a webhook listener.

The single largest gap is **G-3 (suggested changes)**. Today's bot is good at
naming problems but not at proposing fixes the developer can apply with one
click. Adding suggested-code blocks is the highest-leverage 1-week change in
the entire P1 surface.

The second largest gap is **G-5 (conversation)**. Real reviewers respond to
replies. A bot that doesn't is not a teammate.

A realistic P1 effort (4–6 weeks) closes G-1, G-2, G-3, G-4, G-5, G-7, G-8,
G-10 — which is the difference between "PR review bot" and "PR review
product".