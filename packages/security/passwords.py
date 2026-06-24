"""
Password hashing utilities.

Secure password hashing and verification using passlib.
"""

import logging
from typing import Optional

from passlib.context import CryptContext

from apps.api.core.config import settings

logger = logging.getLogger(__name__)

# ===============================
# PASSWORD CONTEXT
# ===============================


# Cryptographic context for password hashing
pwd_context = CryptContext(schemes=[settings.HASH_ALGORITHM])


# ===============================
# PASSWORD HASHING
# ===============================


def hash_password(password: str) -> str:
    """
    Hash password securely.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Raises:
        ValueError: If hashing fails
    """
    try:
        hashed = pwd_context.hash(password)

        logger.debug("Password hashed successfully")
        return hashed

    except Exception as e:
        logger.error(f"Failed to hash password: {e}")
        raise


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """
    Verify password against hash.

    Args:
        password: Plain text password
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def check_password(
    password: str,
    hashed_password: str,
) -> bool:
    """
    Check if password matches hash (alias for verify_password).

    Args:
        password: Plain text password
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    return verify_password(password, hashed_password)


# ===============================
# PASSWORD VALIDATION
# ===============================


def validate_password(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, errors)
    """
    errors = []

    # Minimum length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")

    # Maximum length
    if len(password) > 100:
        errors.append("Password must be at most 100 characters")

    # Check for uppercase
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    # Check for lowercase
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    # Check for digits
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    # Check for special characters
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?`~" for c in password):
        errors.append("Password must contain at least one special character")

    is_valid = len(errors) == 0

    return is_valid, errors


def needs_rehash(password_hash: str) -> bool:
    """
    Check if password hash needs rehashing.

    Args:
        password_hash: Password hash to check

    Returns:
        True if hash needs rehashing
    """
    try:
        # Check hash version (simplified check)
        if pwd_context.crypt(password_hash):
            # Hash is valid but may need rehashing
            return False
        return True
    except Exception:
        return False


def rehash_password(password: str) -> str:
    """
    Rehash password with stronger settings.

    Args:
        password: Plain text password

    Returns:
        New stronger password hash
    """
    # Increase iterations for stronger hashing
    new_iterations = settings.PBKDF2_ITERATIONS * 2

    new_context = CryptContext(
        schemes=[settings.HASH_ALGORITHM],
        **{
            f"{settings.HASH_ALGORITHM}__rounds": new_iterations,
            f"{settings.HASH_ALGORITHM}__salt_size": settings.PBKDF2_SALT_LENGTH,
        }
    )

    try:
        new_hash = new_context.hash(password)
        logger.info("Password rehashed successfully")
        return new_hash
    except Exception as e:
        logger.error(f"Failed to rehash password: {e}")
        raise


# ===============================
# PASSWORD SCALES
# ===============================


def scale_password_strength(password: str) -> int:
    """
    Scale password strength (1-5).

    Args:
        password: Password to scale

    Returns:
        Strength score (1-5)
    """
    score = 1

    # Length bonus
    length = len(password)
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1

    # Character variety
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?`~" for c in password):
        score += 1

    # Cap at 5
    return min(score, 5)
