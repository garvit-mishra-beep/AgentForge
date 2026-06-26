# Model Registry — AgentForge

**Last Updated:** June 2026

---

## Supported Models

| Model | Provider | Context Window | Max Output | Cost/1K In | Cost/1K Out | Strengths | Weaknesses | Recommended Roles | API Timeout |
|-------|----------|---------------|------------|------------|-------------|-----------|------------|-------------------|-------------|
| GPT-4o | OpenAI | 128K | 16,384 | $0.00250 | $0.01000 | Strong security reasoning, React/TypeScript patterns, structured output | Higher cost, slower than mini variants | Frontend Eng, Security Eng | 60s |
| GPT-4o-mini | OpenAI | 128K | 16,384 | $0.00015 | $0.00060 | Fast, cheap, good enough for simple tasks | Less precise code generation, weaker reasoning | QA (simple cases), rapid prototyping | 30s |
| Claude Sonnet 4.6 | Anthropic | 200K | 8,192 | $0.00300 | $0.01500 | Excellent code generation, follows instructions precisely, long context | Higher cost, lower max output tokens | Backend Eng | 60s |
| Claude Haiku 4.5 | Anthropic | 200K | 4,096 | $0.00025 | $0.00125 | Fast, cheap, good at config files and simple code | Limited max output (4K tokens) | DevOps Eng, simple tasks | 30s |
| Gemini 1.5 Pro | Google | 1,048K | 8,192 | $0.00125 | $0.00500 | Massive context window (1M tokens), strong planning, structured output | Sometimes verbose, occasionally imprecise | Team Lead | 60s |
| Gemini 1.5 Flash | Google | 1,048K | 8,192 | $0.000075 | $0.00030 | Fastest model, cheapest, large context | Weaker reasoning and code quality | Simple tasks, quick drafts | 30s |
| Qwen-72B-Instruct | Alibaba | 32K | 2,048 | $0.00050 | $0.00100 | Cost-effective, surprisingly good at test generation | Limited context (32K), lower max output | QA Engineer | 60s |

---

## Cost Comparison Table

For a typical "Build JWT Auth" task (~18,000 tokens total across 7 agent steps):

| Model Combination | Estimated Cost |
|------------------|---------------|
| All GPT-4o | ~$0.12 |
| Mixed (Lead: Gemini, BE: Claude, Reviewer: GPT-4o, QA: Qwen, Security: GPT-4o) | ~$0.054 |
| All GPT-4o-mini | ~$0.01 |
| All Claude Haiku | ~$0.02 |

---

## Rate Limit Tiers

| Tier | Requests/min | Tokens/min | Models Available |
|------|-------------|------------|-----------------|
| Free | 10 | 50,000 | GPT-4o-mini, Claude Haiku, Gemini 1.5 Flash |
| Pro | 100 | 500,000 | All models |
| Team | 500 | 2,000,000 | All models |
| Enterprise | Custom | Custom | All models + custom models |

---

## Model Selection Rules

1. **Context window requirement** — The model's context window must exceed the total prompt size (system prompt + task description + codebase context + agent memory injection). If the total prompt exceeds the context window, the system selects a model with a larger context or truncates the context (with a warning).

2. **Max output tokens requirement** — The model's max output tokens must be sufficient for the expected output size. For code generation tasks, Claude Sonnet (8K) or GPT-4o (16K) are preferred. For configuration files, Claude Haiku (4K) is sufficient.

3. **Cost optimization** — For non-critical steps (drafting, simple validation), the system prefers cheaper models. For critical steps (code generation, security audit), the system prefers more capable models.

4. **Fallback chain** — If the primary model fails (timeout, rate limit, API error), the system falls back:
   - GPT-4o → GPT-4o-mini → Claude Sonnet
   - Claude Sonnet → Claude Haiku → GPT-4o-mini
   - Gemini 1.5 Pro → Gemini 1.5 Flash → GPT-4o-mini
   - Qwen-72B → GPT-4o-mini → Claude Haiku

---

## Model Registry Validation

When a user assigns a model to a role, the system validates:

```python
def validate_model_assignment(role: str, model_id: str) -> bool:
    model = registry.get(model_id)
    if not model:
        return False

    # Check context window meets role minimum
    role_min_context = ROLE_MIN_CONTEXT[role]  # e.g., Team Lead = 64K
    if model.context_window < role_min_context:
        return False

    # Check model is available on the user's tier
    if model.tier > user.tier:
        return False

    return True
```

---

## Adding a New Model

1. Add entry to `apps/api/core/model_registry.py` with all fields
2. Update this document with the new model's details
3. Add API key handling in `apps/api/core/config.py` if new provider
4. Add fallback chain in `apps/api/agents/providers.py`
