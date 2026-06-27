"""
Model registry for managing AI provider configurations and model routing.
Byok-first (Bring Your Own Key) implementation.
"""

from typing import Dict, List, Optional, Tuple
from core.providers import AIProvider, get_provider_for_user, create_provider, ProviderConfig
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for managing AI models and provider configurations."""

    def __init__(self):
        """Initialize the model registry with default model chains."""
        # Define model chains for different roles
        self._model_chains = {
            "baseline": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro", "llama3.1:70b"],
            "builder": ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro", "codellama:34b"],
            "reviewer": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro", "phi4-mini"],
            "architect": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro", "llama3.1:70b"],
            "tester": ["gpt-4o", "claude-3-5-sonnet", "codellama:34b", "deepseek-coder:33b"],
            "security": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro", "llama3.1:70b"],
            "team_lead": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"],
            "aggregator": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"],
        }

    def get_legacy_chain(self, role: str) -> List[str]:
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
        project_id: Optional[str] = None,
        db_session = None
    ) -> AIProvider:
        """
        Get a provider instance for a specific user and model.

        Args:
            user_id: The user ID
            model: The model name
            project_id: Optional project ID for project-specific keys
            db_session: Database session

        Returns:
            Configured AIProvider instance
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

        return provider_instance

    def get_provider_fallback(self, model: str) -> AIProvider:
        """
        Get provider using fallback to global settings (backward compatibility).

        Args:
            model: The model name

        Returns:
            AIProvider instance using global settings
        """
        return get_provider(model)


# Global registry instance
_registry: Optional[ModelRegistry] = None


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