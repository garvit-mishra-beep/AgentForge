# Local Setup & Environment Reference — AgentForge

This document details the configuration properties, database connection properties, and environment variables needed to build, run, and test AgentForge locally.

---

## 1. Environment Variable Reference (`.env`)

Configure the properties in your local `apps/api/.env` file. Below is a comprehensive reference mapping of every system environment variable:

### Core Configuration
| Variable | Type | Default | Description |
|:---|:---:|:---:|:---|
| `JWT_SECRET` | string | `supersecret` | Signature secret for local PyJWT tokens. |
| `ENCRYPTION_KEY` | string | (Required) | Base64 Fernet key used to encrypt BYOK client keys at rest. |
| `DATABASE_URL` | string | `postgresql://postgres:postgres@localhost:5432/agentforge` | PostgreSQL database connection string. |
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis caching and rate limiting connection string. |

### Fast Demo Mode Configurations
Enable these parameters to configure sub-60-second task completions during live demonstrations:

| Variable | Type | Default | Description |
|:---|:---:|:---:|:---|
| `AGENTFORGE_FAST_DEMO_MODE` | boolean | `false` | Enables short timeouts, single-pass graphs, and limits context history. |
| `AGENTFORGE_MAX_RETRIES` | integer | `0` | Rejection retry limit. If fast demo mode is active, this is forced to `0`. |
| `AGENTFORGE_MAX_OUTPUT_TOKENS` | integer| `512` | Token output generation limit per agent. |
| `AGENTFORGE_MAX_CONTEXT_MESSAGES`| integer| `5` | History limit passed to agents. |
| `AGENTFORGE_MAX_EXECUTION_TIME` | integer | `60` | Hard cap timeout (seconds) for task runs. |

### Agent Individual Node Timeouts
Configure target timeouts (seconds) for individual graph steps:

| Variable | Type | Default | Description |
|:---|:---:|:---:|:---|
| `AGENTFORGE_AGENT_TIMEOUT_LEAD` | integer | `20` | Timeout for the Team Lead plan phase. |
| `AGENTFORGE_AGENT_TIMEOUT_BUILDER` | integer | `30` | Timeout for the Builder node. |
| `AGENTFORGE_AGENT_TIMEOUT_REVIEWER`| integer | `15` | Timeout for the Reviewer node. |
| `AGENTFORGE_AGENT_TIMEOUT_DELIVER` | integer | `15` | Timeout for the Team Lead delivery phase. |

### Global LLM Provider Fallbacks (BYOK Defaults)
System defaults when no User or Project level key is resolved:

| Variable | Type | Default | Description |
|:---|:---:|:---:|:---|
| `OPENAI_API_KEY` | string | - | Global OpenAI API access key. |
| `ANTHROPIC_API_KEY` | string | - | Global Anthropic API access key. |
| `GOOGLE_API_KEY` | string | - | Global Google Gemini API access key. |
| `OLLAMA_BASE_URL` | string | `http://localhost:11434` | Endpoint url for local Ollama providers. |

---

## 2. Infrastructure Setup & Database

### PostgreSQL Configuration
Ensure PostgreSQL has the `pgvector` extension enabled. AgentForge checks this during startup migrations:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Database Migrations
Migrations are managed as raw SQL files in `apps/api/migrations/`. AgentForge automatically executes pending migrations during backend startup. You can manually check migration files under [apps/api/migrations/](file:///c:/Users/garvi/AgentForge/apps/api/migrations/).
