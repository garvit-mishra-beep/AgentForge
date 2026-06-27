# Factory function to create provider instances
def create_provider(provider_type: str, config: ProviderConfig) -> AIProvider:
    """Create a provider instance based on type and configuration."""
    if provider_type == "openai":
        return OpenAIProvider(config)
    elif provider_type == "anthropic":
        return AnthropicProvider(config)
    elif provider_type == "google":
        return GoogleProvider(config)
    elif provider_type == "ollama":
        return OllamaProvider(config)
    elif provider_type in ["openrouter", "groq", "openai-compatible"]:
        return OpenAICompatibleProvider(config)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


# Helper function to determine provider type from model name
def get_provider_from_model(model: str) -> str:
    """Determine provider type from model name."""
    model_lower = model.lower()

    if model_lower.startswith("openai/") or any(model in model_lower for model in ["gpt-", "text-embedding"]) or model_lower in ["gpt-4", "gpt-3.5-turbo"]:
        return "openai"
    elif model_lower.startswith("anthropic/") or "claude-" in model_lower:
        return "anthropic"
    elif model_lower.startswith("google/") or "gemini-" in model_lower or "palm-" in model_lower:
        return "google"
    elif model_lower.startswith("ollama/") or ":" in model_lower and not "/" in model_lower:
        # Ollama models often have format like "llama3.2:3b" or "codellama:34b"
        return "ollama"
    elif any(provider in model_lower for provider in ["openrouter", "groq"]):
        if "openrouter" in model_lower:
            return "openrouter"
        elif "groq" in model_lower:
            return "groq"
    elif "/" in model_lower:
        # Handle format like "provider/model-name"
        provider_part = model_lower.split("/")[0]
        if provider_part in ["openai", "anthropic", "google", "ollama", "openrouter", "groq"]:
            return provider_part

    # Default fallback
    return "openai"


# ── BYOK-Enhanced Provider Resolution ────────────────────────────────────

async def get_provider_for_user(
    model: str,
    user_id: str,
    project_id: str | None = None,
    db: AsyncSession = None
) -> tuple[AIProvider, str]:
    """
    Get a provider instance for a specific user and project.
    Returns (provider_instance, provider_type) tuple.

    This function looks up the user's API key and endpoint configuration
    to create a properly configured provider instance.
    """
    if db is None:
        raise ValueError("Database session is required for BYOK provider resolution")

    # Determine the provider type from the model name
    provider_type = get_provider_from_model(model)

    # Try to get user's API key for this provider/project
    key_info = await get_user_api_key(db, user_id, provider_type, project_id)

    # If no key found, try without project-specific (fallback to user-level)
    if not key_info and project_id is not None:
        key_info = await get_user_api_key(db, user_id, provider_type, None)

    # If still no key, check if there are global settings as fallback
    if not key_info:
        # Fallback to global settings (for backward compatibility)
        from core.config import settings

        if provider_type == "openai" and settings.openai_api_key:
            config = ProviderConfig(api_key=settings.openai_api_key)
            return create_provider(provider_type, config), provider_type
        elif provider_type == "anthropic" and settings.anthropic_api_key:
            config = ProviderConfig(api_key=settings.anthropic_api_key)
            return create_provider(provider_type, config), provider_type
        elif provider_type == "google" and settings.google_api_key:
            config = ProviderConfig(api_key=settings.google_api_key)
            return create_provider(provider_type, config), provider_type
        elif provider_type == "ollama":
            # For Ollama, use the base URL from settings
            config = ProviderConfig(
                api_key="",  # Ollama doesn't need an API key
                base_url=settings.ollama_base_url
            )
            return create_provider(provider_type, config), provider_type

        raise ValueError(f"No API key found for provider {provider_type} and no global fallback available")

    # Get endpoint configuration if available
    endpoint_config = await get_user_endpoint_config(
        db, user_id, provider_type, project_id
    )

    # Build provider configuration
    config = ProviderConfig(
        api_key=key_info["key"],
        base_url=endpoint_config.get("base_url") if endpoint_config else None,
        organization=endpoint_config.get("organization") if endpoint_config else None,
    )

    # Add any provider-specific config from the key
    if key_info.get("provider_config"):
        # Merge provider-specific config
        pass  # Could be extended to handle specific provider configs

    return create_provider(provider_type, config), provider_type


async def get_user_endpoint_config(
    db: AsyncSession,
    user_id: str,
    provider: str,
    project_id: str | None
) -> dict | None:
    """Get endpoint configuration for user/provider/project."""
    query = """
        SELECT base_url, api_key_id, headers, config
        FROM api_endpoints
        WHERE user_id = $1 AND provider = $2 AND is_enabled = true
    """
    params = [user_id, provider]
    param_idx = 3

    if project_id is not None:
        query += f" AND project_id = ${param_idx}"
        params.append(project_id)
        param_idx += 1
    else:
        query += " AND project_id IS NULL"

    # Prefer default endpoint, then most recently updated
    query += " ORDER BY is_default DESC, updated_at DESC LIMIT 1"

    row = await db.fetchrow(query, *params)
    if not row:
        return None

    # If endpoint references an API key, use that key instead
    api_key = None
    if row["api_key_id"]:
        key_row = await db.fetchrow(
            "SELECT encrypted_key FROM api_keys WHERE id = $1 AND user_id = $2",
            row["api_key_id"], user_id,
        )
        if key_row:
            # In a real implementation, we would decrypt the key here
            # For now, we'll note that the endpoint has its own key
            pass

    return {
        "base_url": row["base_url"],
        "headers": row["headers"] or {},
        "config": row["config"] or {},
    }


# Helper functions for checking if this is the first key/endpoint
async def _is_first_key_for_user_provider(
    db: AsyncSession, user_id: str, provider: str, project_id: str | None
) -> bool:
    """Check if this is the first key for user/provider/project."""
    query = """
        SELECT COUNT(*) as count
        FROM api_keys
        WHERE user_id = $1 AND provider = $2 AND is_enabled = true
    """
    params = [user_id, provider]

    if project_id is not None:
        query += " AND project_id = $3"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    result = await db.fetchrow(query, *params)
    return result["count"] == 0


async def _is_first_endpoint_for_user_provider(
    db: AsyncSession, user_id: str, provider: str, project_id: str | None
) -> bool:
    """Check if this is the first endpoint for user/provider/project."""
    query = """
        SELECT COUNT(*) as count
        FROM api_endpoints
        WHERE user_id = $1 AND provider = $2 AND is_enabled = true
    """
    params = [user_id, provider]

    if project_id is not None:
        query += " AND project_id = $3"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    result = await db.fetchrow(query, *params)
    return result["count"] == 0


def get_provider(model: str) -> AIProvider:
    """
    Backward compatibility function that returns a provider based on global settings.
    This maintains compatibility with existing code that expects the old API.
    """
    from core.config import settings

    # Determine provider type from model name
    provider_type = get_provider_from_model(model)

    # Fall back to global settings
    if provider_type == "openai" and settings.openai_api_key:
        config = ProviderConfig(api_key=settings.openai_api_key)
        return create_provider(provider_type, config)
    elif provider_type == "anthropic" and settings.anthropic_api_key:
        config = ProviderConfig(api_key=settings.anthropic_api_key)
        return create_provider(provider_type, config)
    elif provider_type == "google" and settings.google_api_key:
        config = ProviderConfig(api_key=settings.google_api_key)
        return create_provider(provider_type, config)
    elif provider_type == "ollama":
        # For Ollama, use the base URL from settings
        config = ProviderConfig(
            api_key="",  # Ollama doesn't need an API key
            base_url=settings.ollama_base_url
        )
        return create_provider(provider_type, config)
    else:
        # Fallback - raise an error if no credentials available
        raise ValueError(f"No API key configured for provider {provider_type}")