import os
import logging
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from apps.api.core.config import settings
from apps.api.dependencies.auth import get_current_active_user
from typing import Any

logger = logging.getLogger(__name__)

router = APIRouter()

class SettingsResponse(BaseModel):
    llm_provider: str
    gemini_configured: bool
    openai_configured: bool
    anthropic_configured: bool
    open_source_configured: bool
    open_source_base_url: str
    open_source_model: str
    planner_provider: str
    developer_provider: str
    tester_provider: str
    reviewer_provider: str

class SettingsUpdate(BaseModel):
    llm_provider: str
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    open_source_api_key: str | None = None
    open_source_base_url: str | None = None
    open_source_model: str | None = None
    planner_provider: str | None = None
    developer_provider: str | None = None
    tester_provider: str | None = None
    reviewer_provider: str | None = None

@router.get("/settings", response_model=SettingsResponse, tags=["Settings"])
async def get_app_settings(user: Any = Depends(get_current_active_user)):
    """
    Retrieve current LLM settings. API keys are masked as booleans.
    """
    return SettingsResponse(
        llm_provider=settings.LLM_PROVIDER,
        gemini_configured=bool(settings.GEMINI_API_KEY),
        openai_configured=bool(settings.OPENAI_API_KEY),
        anthropic_configured=bool(settings.ANTHROPIC_API_KEY),
        open_source_configured=bool(settings.OPEN_SOURCE_API_KEY),
        open_source_base_url=settings.OPEN_SOURCE_BASE_URL,
        open_source_model=settings.OPEN_SOURCE_MODEL,
        planner_provider=settings.PLANNER_PROVIDER,
        developer_provider=settings.DEVELOPER_PROVIDER,
        tester_provider=settings.TESTER_PROVIDER,
        reviewer_provider=settings.REVIEWER_PROVIDER,
    )

@router.post("/settings", tags=["Settings"])
async def update_app_settings(update_data: SettingsUpdate, user: Any = Depends(get_current_active_user)):
    """
    Update LLM configuration and persist to .env file.
    """
    settings.LLM_PROVIDER = update_data.llm_provider
    
    if update_data.gemini_api_key is not None:
        settings.GEMINI_API_KEY = update_data.gemini_api_key.strip() or None
    if update_data.openai_api_key is not None:
        settings.OPENAI_API_KEY = update_data.openai_api_key.strip() or None
    if update_data.anthropic_api_key is not None:
        settings.ANTHROPIC_API_KEY = update_data.anthropic_api_key.strip() or None
    if update_data.open_source_api_key is not None:
        settings.OPEN_SOURCE_API_KEY = update_data.open_source_api_key.strip() or None
    if update_data.open_source_base_url is not None:
        settings.OPEN_SOURCE_BASE_URL = update_data.open_source_base_url.strip()
    if update_data.open_source_model is not None:
        settings.OPEN_SOURCE_MODEL = update_data.open_source_model.strip()
    if update_data.planner_provider is not None:
        settings.PLANNER_PROVIDER = update_data.planner_provider.strip()
    if update_data.developer_provider is not None:
        settings.DEVELOPER_PROVIDER = update_data.developer_provider.strip()
    if update_data.tester_provider is not None:
        settings.TESTER_PROVIDER = update_data.tester_provider.strip()
    if update_data.reviewer_provider is not None:
        settings.REVIEWER_PROVIDER = update_data.reviewer_provider.strip()

    # Write key definitions to local env
    env_lines = [
        f"DATABASE_URL={settings.DATABASE_URL}",
        f"LLM_PROVIDER={settings.LLM_PROVIDER}",
        f"OPEN_SOURCE_BASE_URL={settings.OPEN_SOURCE_BASE_URL}",
        f"OPEN_SOURCE_MODEL={settings.OPEN_SOURCE_MODEL}",
        f"PLANNER_PROVIDER={settings.PLANNER_PROVIDER}",
        f"DEVELOPER_PROVIDER={settings.DEVELOPER_PROVIDER}",
        f"TESTER_PROVIDER={settings.TESTER_PROVIDER}",
        f"REVIEWER_PROVIDER={settings.REVIEWER_PROVIDER}"
    ]
    if settings.GEMINI_API_KEY:
        env_lines.append(f"GEMINI_API_KEY={settings.GEMINI_API_KEY}")
    if settings.OPENAI_API_KEY:
        env_lines.append(f"OPENAI_API_KEY={settings.OPENAI_API_KEY}")
    if settings.ANTHROPIC_API_KEY:
        env_lines.append(f"ANTHROPIC_API_KEY={settings.ANTHROPIC_API_KEY}")
    if settings.OPEN_SOURCE_API_KEY:
        env_lines.append(f"OPEN_SOURCE_API_KEY={settings.OPEN_SOURCE_API_KEY}")

    env_content = "\n".join(env_lines) + "\n"

    try:
        # Create apps/api/.env file
        with open("apps/api/.env", "w") as f:
            f.write(env_content)
        # Create root .env file
        with open(".env", "w") as f:
            f.write(env_content)
        logger.info("Credentials written to apps/api/.env and root .env files successfully.")
    except Exception as e:
        logger.error(f"Failed to save settings to .env files: {e}")

    return {"status": "success", "message": "Settings updated and saved successfully!"}
