"""
Model registry for managing AI provider configurations and model routing.
Byok-first (Bring Your Own Key) implementation.
"""

import logging

from core.providers import AIProvider, get_provider_for_user
from core.providers import get_provider as core_get_provider

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for managing AI models and provider configurations."""

    def __init__(self):
        """Initialize the model registry with default model chains."""
        self._model_chains = {
            "baseline": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"],
            "builder": ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"],
            "reviewer": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"],
            "architect": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"],
            "tester": ["gpt-4o", "claude-3-5-sonnet"],
            "security": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"],
            "team_lead": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"],
            "aggregator": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"],
        }

    def get_legacy_chain(self, role: str) -> list[str]:
        """
        Get legacy model chain format for backward compatibility.

        Args:
            role: The role (e.g., 'baseline', 'builder', 'reviewer')

        Returns:
            List of model names in order of preference
        """
        return self._model_chains.get(role, self._model_chains["reviewer"])

    async def get_provider_for_user(
        self,
        user_id: str,
        model: str,
        project_id: str | None = None,
        db_session = None
    ) -> tuple[AIProvider, str]:
        """
        Get a provider instance for a specific user and model.

        Args:
            user_id: The user ID
            model: The model name
            project_id: Optional project ID for project-specific keys
            db_session: Database session

        Returns:
            Configured AIProvider instance and provider type
        """
        if db_session is None:
            raise ValueError("Database session is required for BYOK provider resolution")

        # Get provider instance and type from the BYOK function
        provider_instance, provider_type = await get_provider_for_user(
            model=model,
            user_id=user_id,
            project_id=project_id,
            db=db_session
        )

        return provider_instance, provider_type

    def get_provider_fallback(self, model: str) -> AIProvider:
        """
        Get provider using fallback to global settings (backward compatibility).

        Args:
            model: The model name

        Returns:
            AIProvider instance using global settings
        """
        return core_get_provider(model)


# Global registry instance
_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _registry
    _registry = None


# Backward compatibility functions
def get_legacy_chain(role: str) -> list[str]:
    """Get legacy chain format for direct provider checking."""
    return get_registry().get_legacy_chain(role)


def get_provider(model: str) -> AIProvider:
    """
    Backward compatibility function that mimics the original get_provider.
    This allows existing code to work without modification.
    """
    return get_registry().get_provider_fallback(model)
