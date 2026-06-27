# AgentForge V1 BYOK-First Platform Architecture

## Target Architecture

AgentForge V1 will transition to a Bring Your Own Key (BYOK)-first platform where:
- Each user owns and manages their own API keys for all supported providers
- Keys are stored encrypted per-user (and optionally per-project) in the database
- Provider selection is dynamic based on user credentials, model capabilities, and fallback chains
- All AI provider interactions are isolated per user/project to prevent cross-tenant contamination
- Cost tracking and usage analytics are tied to individual user consumption
- Local model support is treated as a first-class provider option alongside cloud APIs

## Provider Abstraction Layer

### Core Abstraction
Maintain the existing `AIProvider` abstract base class:
```python
class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int | None = None,
        timeout_s: float | None = None,
    ) -> ChatResponse:
        ...
```

### Provider Instances
Provider instances will no longer read from global settings. Instead:
- Each provider instance receives credentials and configuration via constructor
- Provider instances are short-lived and created per-request with user-specific credentials
- Shared HTTP client pool remains for connection efficiency

### Supported Providers
1. **OpenAI** - Official API and OpenAI-compatible endpoints
2. **Anthropic** - Claude API
3. **Google** - Gemini API
4. **Ollama** - Local LLM server
5. **OpenRouter** - Aggregator service
6. **Groq** - High-speed inference
7. **Custom OpenAI-compatible** - Any endpoint adhering to OpenAI chat completions API

## User/Project/Agent Key Management

### Key Storage Model
- **User-level keys**: Primary storage location for API keys
- **Project-level keys**: Optional override for specific projects (inherits from user if not set)
- **Agent-level model selection**: Already exists via `TeamMemberConfig.model` in state

### Database Schema Additions
```sql
-- User API keys (encrypted at rest)
CREATE TABLE IF NOT EXISTS user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NULL REFERENCES projects(id) ON DELETE SET NULL,
    provider VARCHAR(20) NOT NULL,  -- openai, anthropic, google, ollama, openrouter, groq, custom
    encrypted_key TEXT NOT NULL,    -- AES-GCM encrypted API key
    key_preview TEXT NOT NULL,      -- First/last 4 chars for identification
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, project_id, provider)
);

-- Custom endpoint configurations (for OpenAI-compatible)
CREATE TABLE IF NOT EXISTS user_api_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NULL REFERENCES projects(id) ON DELETE SET NULL,
    provider VARCHAR(20) NOT NULL DEFAULT 'custom',
    base_url TEXT NOT NULL,         -- Base URL for API endpoint
    api_key_id UUID NULL REFERENCES user_api_keys(id) ON DELETE SET NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, project_id, provider)
);
```

### Key Management Service
```python
class KeyManagementService:
    async def get_decrypted_key(
        self, 
        user_id: UUID, 
        provider: str, 
        project_id: UUID | None = None
    ) -> str | None:
        """
        Retrieve and decrypt API key for user/provider/project.
        Falls back to user-level key if project-specific not found.
        Returns None if no key found or disabled.
        """
        # Implementation uses EncryptionService to decrypt
    
    async def get_endpoint_config(
        self,
        user_id: UUID,
        provider: str,
        project_id: UUID | None = None
    ) -> dict | None:
        """
        Get base URL and auth configuration for provider.
        For standard providers, returns known endpoints.
        For custom/OpenAI-compatible, returns user-configured endpoint.
    ```

## Provider Resolution

### Enhanced get_provider Function
Replace current keyword-based resolution with credential-aware resolution:

```python
def get_provider(
    model: str,
    user_id: UUID,
    project_id: UUID | None = None,
    prefer_provider: str | None = None
) -> tuple[AIProvider, dict]:
    """
    Returns (provider_instance, provider_config) tuple.
    provider_config contains: base_url, auth_headers, etc.
    """
    # 1. Check for explicit provider preference
    # 2. Check user/project keys for provider availability
    # 3. Fall back to model-based keyword matching with credential validation
    # 4. Raise ProviderNotAvailableError if no working provider found
```

### Provider Configuration
Each provider instance receives:
```python
class OpenAIProvider(AIProvider):
    def __init__(
        self, 
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        organization: str | None = None
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.organization = organization
        # ... rest unchanged
```

Similar pattern for other providers, with Ollama accepting base_url and Google accepting API key.

## Cost Tracking

### Usage Data Collection
Extend `ChatResponse` to include cost estimation:
```python
@dataclass
class ChatResponse:
    content: str
    token_usage: dict | None = None
    duration_ms: float | None = None
    model: str = ""
    provider: str = ""  # Added for cost attribution
    estimated_cost_usd: float | None = None  # New field
```

### Cost Calculation Service
```python
class CostCalculator:
    # Pricing tables per provider/model (updated periodically)
    PRICING = {
        "openai": {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
            # ... etc
        },
        "anthropic": {
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            # ... etc
        },
        # Local models have $0 cost
        "ollama": {"prompt": 0.0, "completion": 0.0}
    }
    
    def calculate_cost(
        self, 
        provider: str, 
        model: str, 
        token_usage: dict
    ) -> float:
        if provider not in self.PRICING or model not in self.PRICING[provider]:
            return 0.0  # Unknown model - no cost estimate
        
        rates = self.PRICING[provider][model]
        prompt_cost = (token_usage.get("prompt_tokens", 0) / 1000) * rates["prompt"]
        completion_cost = (token_usage.get("completion_tokens", 0) / 1000) * rates["completion"]
        return prompt_cost + completion_cost
```

### Usage Tracking Table
```sql
CREATE TABLE IF NOT EXISTS ai_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NULL REFERENCES projects(id) ON DELETE SET NULL,
    provider VARCHAR(20) NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    request_id UUID,  -- Correlation ID for tracing
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Fallback Design

### Enhanced ModelRegistry
Modify `ModelRegistry` to support provider-aware fallback chains:

```python
class ModelRegistry:
    def __init__(self):
        # Define chains as [(provider_hint, model_pattern), ...]
        self._chains = {
            "baseline": [
                ("anthropic", "claude-3-5-sonnet"),
                ("openai", "gpt-4o"),
                ("google", "gemini-1.5-pro"),
                ("ollama", "llama3.1:70b")  # Local fallback
            ],
            "builder": [
                ("openai", "gpt-4o"),
                ("anthropic", "claude-3-5-sonnet"),
                ("google", "gemini-1.5-pro"),
                ("ollama", "codellama:34b")
            ],
            # ... other roles
        }
    
    async def resolve_with_fallback(
        self, 
        role: str, 
        user_id: UUID, 
        project_id: UUID | None = None
    ) -> tuple[str, str, bool]:  # (provider, model, fallback_used)
        """
        Try each (provider, model) in chain until one works with user's credentials.
        Returns the first working combination and whether fallback was used.
        """
        chains = self._chains.get(role, self._chains["reviewer"])
        
        for provider_hint, model_pattern in chains:
            # Find matching models for user that fit the pattern
            available_models = await self._get_available_models(
                user_id, project_id, provider_hint, model_pattern
            )
            
            for model in available_models:
                try:
                    # Test if provider works with credentials
                    provider_instance = await self._get_provider_instance(
                        provider_hint, model, user_id, project_id
                    )
                    # Validate credentials with a minimal call
                    await provider_instance.chat(
                        model=model,
                        system_prompt="test",
                        user_message="hello",
                        max_tokens=1
                    )
                    return (provider_hint, model, len(chains) > 1)
                except ProviderAuthenticationError:
                    continue  # Try next model/provider
                except ProviderNotAvailableError:
                    continue
        
        raise NoAvailableProvidersError(f"No working providers for role {role}")
```

### Circuit Breaker Pattern
Implement per-provider circuit breakers to avoid repeatedly failing providers:
- Track failure rates per (user, provider) over time window
- Temporarily disable provider after threshold of failures
- Automatically retry after cool-down period

## Local Model Support

### Unified Local Provider Interface
Treat all local models as OpenAI-compatible endpoints:
1. **Ollama**: Existing provider, enhanced to accept custom base_url
2. **llama.cpp server**: OpenAI-compatible endpoint
3. **vLLM/TGI**: OpenAI-compatible endpoint
4. **LM Studio**: OpenAI-compatible endpoint

### Local Provider Configuration
Users can configure:
- Base URL for local service
- Model name/path as served by the local endpoint
- Optional API key (if local service requires auth)

### Resource Isolation
Local model execution still uses the secure sandbox (see below) to prevent:
- Resource exhaustion from local model consumption
- Potential escape vectors from model serving frameworks

## Security Considerations

### Key Protection
- All API keys encrypted at rest using AES-GCM with per-instance key
- Encryption key derived from `AGENTFORGE_ENCRYPTION_KEY` environment variable
- Keys never logged or exposed in API responses (only preview shown)
- Memory protection)

### Provider Isolation
- Provider instances created per-request with user-specific credentials
- No cross-contamination between users' API calls
- HTTP client pool shared but requests isolated per-user

### Sandbox Enhancement (from V2 Validation Architecture)
All code execution (including local model inference if applicable) runs in:
- Containerized environment (Docker/runC) or gVisor sandbox
- Strict resource limits (CPU, memory, pids)
- Filesystem: read-only mount for code, tmpfs for workspace
- Network: egress only to approved destinations (no inbound)
- Seccomp / AppArmor profiles to limit syscalls

### Audit Logging: 
   - Provider name and model (never keys)
   - Token usage and cost
   - Success/failure status
   - Timestamp and user ID
 
- Failed authentication attempts logged (without exposing keys)
- All key management operations audited (create, update, delete, use)

## Database Changes Summary

### New Tables
1. `user_api_keys` - Encrypted API keys per user/project/provider
2. `user_api_endpoints` - Custom endpoint configurations (for OpenAI-compatible)
3. `ai_usage` - Token usage and cost tracking

### Modified Tables
- Add `provider` and `model` columns to existing `agent_executions` or `task_messages` for attribution
- Consider adding `usage_id` foreign key to `ai_usage` for detailed tracking

## API Changes

### Updated Endpoints
1. `POST /keys` - Now accepts optional `project_id` for project-scoped keys
2. `GET /keys` - Returns keys with project context when applicable
3. `POST /keys/{id}/set-default` - Mark key as default for user/project
4. `GET /providers/{provider}/models` - List available models for provider (with user auth)
5. `GET /usage` - Usage and cost analytics dashboard data

### Backward Compatibility
- Global settings (`settings.openai_api_key`, etc.) still used as fallback for:
  - System-level operations (background tasks without user context)
  - Legacy integrations not yet migrated
- Deprecation path: log warning when global keys used, plan removal in V2

## Frontend Changes

### Provider Management Page
- Unified view for all providers (cloud and local)
- Per-provider configuration cards showing:
  - Connection status (valid/invalid/never tested)
  - Key preview (or "Not configured")
  - Model selector with recommended models
  - Usage statistics and cost (last 30 days)
  - Test connection button
- "Add Provider" button for each type
- Project scope toggle (when viewing project settings)

### Usage Dashboard
- Time-series charts of token usage and cost per provider
- Breakdown by agent role (builder, reviewer, etc.)
- Cost projection based on current usage
- Export to CSV functionality

### Agent Configuration
- When configuring agent model selection:
  - Dropdown shows models grouped by provider
  - Models unavailable due to missing keys show as disabled with tooltip
  - "Use default" option uses user's global default for that provider
  - Local models clearly labeled with (local) indicator

### Error Handling
- Clear error messages when provider authentication fails
- Guidance on how to add/configure missing provider keys
- Fallback indicators when system uses backup provider/model

## Implementation Priority (Phased)

### Phase 1: Core BYOK Foundation
1. User API key storage and encryption
2. Key management API endpoints
3. Provider abstraction update (constructor injection)
4. ModelRegistry updated for credential-aware resolution
5. Basic cost tracking implementation

### Phase 2: Enhanced Features
1. Project-scoped API keys
2. Custom endpoint configuration (OpenAI-compatible)
3. Fallback/circuit breaker implementation
4. Local model provider enhancements
5. Usage dashboard and analytics

### Phase 3: Operational Excellence
1. Advanced security auditing
2. Global rate limiting per user/provider
3. Key expiration and rotation reminders
4. Admin overview of system-wide usage
5. Performance optimization and caching

## Success Metrics

1. **User Adoption**: >80% of users configure at least one provider key
2. **Security**: Zero credential leakage incidents in production
3. **Reliability**: <1% authentication-related failures after initial configuration
4. **Cost Awareness**: Users actively monitor and optimize their usage
5. **Flexibility**: Seamless switching between cloud and local providers
6. **Backward Compatibility**: Existing deployments continue working with deprecated global keys (with warnings)

This BYOK-first architecture transforms AgentForge from a platform with hardcoded, shared API keys to a truly user-owned AI Development Operating System where security, flexibility, and cost transparency are foundational principles.