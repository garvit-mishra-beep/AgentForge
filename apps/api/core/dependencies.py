"""
Dependency injection helpers for FastAPI endpoints.
"""


from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.encryption import EncryptionService


async def get_db(request: Request) -> AsyncSession:
    """Get database connection from app state."""
    return request.app.state.db


def get_encryption() -> EncryptionService:
    """Get encryption service instance."""
    return EncryptionService()


# Optional: Dependency for current user (if using auth)
async def get_current_user(request: Request) -> str:
    """Get current user ID from request."""
    # This would typically come from auth middleware
    # For now, we'll use a simple approach or depend on the auth module
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        # Fallback to demo user or require authentication
        return "00000000-0000-0000-0000-000000000001"  # Default demo user
    return user_id
