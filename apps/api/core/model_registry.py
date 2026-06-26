"""Model registry with fallback chains for Quick Review roles."""

import logging

from core.config import settings
from core.providers import AIProviderError, get_provider

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Resolves models with fallback chain for each role."""

    def __init__(self) -> None:
        self._chains: dict[str, list[str]] = {
            "baseline": self._parse_list(settings.review_models_baseline),
            "builder": self._parse_list(settings.review_models_builder),
            "reviewer": self._parse_list(settings.review_models_reviewer),
        }

    @staticmethod
    def _parse_list(raw: str) -> list[str]:
        return [m.strip() for m in raw.split(",") if m.strip()]

    def get_chain(self, role: str) -> list[str]:
        return self._chains.get(role, self._chains.get("reviewer", ["phi4-mini"]))

    async def resolve(self, role: str) -> tuple[str, bool]:
        """Returns (model_name, fallback_used). Raises HTTPException 503 if none available."""
        models = self.get_chain(role)
        for i, model in enumerate(models):
            try:
                get_provider(model)
                return model, i > 0
            except ValueError as e:
                logger.warning("Model %s not available for role %s: %s", model, role, e)
                continue
            except Exception as e:
                logger.error("Unexpected error resolving model %s for role %s: %s", model, role, e)
                continue
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"No models available for role '{role}'")


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = None
