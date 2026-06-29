import uuid
from typing import Any

AsyncSession = Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import require_user
from core.dependencies import get_db
from core.encryption import EncryptionService
from core.validation import (
    get_provider_info,
    validate_key_format,
    validate_key_live,
)
from models.schemas import (
    ApiEndpointCreate,
    ApiEndpointResponse,
    ApiEndpointUpdate,
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyUpdate,
    ApiKeyValidateRequest,
    ApiKeyValidateResponse,
    ProviderInfoResponse,
    UsageDataPoint,
    UsageStatsResponse,
)

router = APIRouter(prefix="/keys", tags=["keys"])

_encryption: EncryptionService | None = None


def get_encryption(request: Request) -> EncryptionService:
    global _encryption
    if _encryption is None:
        _encryption = EncryptionService()
    return _encryption


# Helper functions
def _mask_key(raw_key: str) -> str:
    """Create a masked version of the key for display."""
    if not raw_key or len(raw_key) <= 8:
        return "****"

    # Show first 4 and last 4 characters with **** in middle
    if "-" in raw_key:
        # For keys like sk-abcdefg...hijk
        prefix = raw_key[:raw_key.find("-") + 1]
        return f"{prefix}****{raw_key[-4:]}"
    else:
        return f"{raw_key[:4]}****{raw_key[-4:]}"


async def get_user_api_key(
    db: AsyncSession,
    user_id: str,
    provider: str,
    project_id: str | None = None
) -> dict | None:
    """Get decrypted API key for user/provider/project."""
    query = """
        SELECT id, encrypted_key, key_preview, is_enabled, provider_config
        FROM api_keys
        WHERE user_id = $1 AND provider = $2 AND is_enabled = true
    """
    params = [user_id, provider]

    if project_id is not None:
        query += " AND project_id = $3"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    query += " ORDER BY is_default DESC, updated_at DESC LIMIT 1"

    row = await db.fetchrow(query, *params)
    if not row:
        return None

    enc = get_encryption(None)  # type: ignore
    decrypted_key = enc.decrypt(row["encrypted_key"])

    return {
        "id": str(row["id"]),
        "key": decrypted_key,
        "preview": row["key_preview"],
        "is_enabled": row["is_enabled"],
        "provider_config": row["provider_config"] or {}
    }


# API Key Endpoints
@router.get("/providers")
async def list_providers() -> ProviderInfoResponse:
    return ProviderInfoResponse(providers=get_provider_info())


@router.post("/validate")
async def validate_key(
    body: ApiKeyValidateRequest,
    request: Request
) -> ApiKeyValidateResponse:
    provider = body.provider.value
    fmt_valid, fmt_msg = validate_key_format(provider, body.key)
    if not fmt_valid:
        return ApiKeyValidateResponse(
            valid=False,
            provider=body.provider,
            message=fmt_msg,
            format_valid=False,
            live_valid=None,
        )

    live_valid, live_msg = await validate_key_live(provider, body.key)
    return ApiKeyValidateResponse(
        valid=live_valid,
        provider=body.provider,
        message=live_msg,
        format_valid=True,
        live_valid=live_valid,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreate,
    request: Request,
    user_id: str = Depends(require_user),
    project_id: str | None = Query(None, description="Project ID for project-scoped key"),
    db: AsyncSession = Depends(get_db)
) -> ApiKeyResponse:
    enc = get_encryption(request)
    provider = body.provider.value
    raw_key = body.key.strip()

    # Validate key format
    fmt_valid, fmt_msg = validate_key_format(provider, raw_key)
    if not fmt_valid:
        raise HTTPException(status_code=400, detail=fmt_msg)

    # Check if key already exists for this user/provider/project
    query = """
        SELECT id FROM api_keys
        WHERE user_id = $1 AND provider = $2 AND is_enabled = true
    """
    params = [user_id, provider]

    if project_id is not None:
        query += " AND project_id = $3"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    existing = await db.fetchrow(query, *params)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"API key for '{provider}' already exists. Use PUT to update.",
        )

    # Encrypt and store the key
    encrypted = enc.encrypt(raw_key)
    preview = _mask_key(raw_key)

    # Determine if this should be the default key
    is_first_key = await _is_first_key_for_user_provider(db, user_id, provider, project_id)

    key_id = str(uuid.uuid4())

    await db.execute(
        """
        INSERT INTO api_keys
        (id, user_id, project_id, provider, encrypted_key, key_preview, is_enabled, is_default)
        VALUES ($1, $2, $3, $4, $5, $6, true, $7)
        """,
        key_id, user_id, project_id, provider, encrypted, preview, is_first_key
    )

    row = await db.fetchrow(
        """
        SELECT id, provider, key_preview, is_enabled, created_at, updated_at, is_default
        FROM api_keys WHERE id = $1
        """,
        key_id,
    )
    return _row_to_response(row)


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    request: Request,
    user_id: str = Depends(require_user),
    project_id: str | None = Query(None, description="Filter by project ID"),
    include_disabled: bool = Query(False, description="Include disabled keys"),
    db: AsyncSession = Depends(get_db)
) -> list[ApiKeyResponse]:
    # Build query
    query = """
        SELECT id, provider, key_preview, is_enabled, created_at, updated_at, is_default
        FROM api_keys
        WHERE user_id = $1
    """
    params = [user_id]

    if project_id is not None:
        query += " AND project_id = $2"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    if not include_disabled:
        query += " AND is_enabled = true"

    query += " ORDER BY is_default DESC, updated_at DESC"

    rows = await db.fetch(query, *params)
    return [_row_to_response(r) for r in rows]


@router.get("/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db)
) -> ApiKeyResponse:
    row = await db.fetchrow(
        """
        SELECT id, provider, key_preview, is_enabled, created_at, updated_at, is_default
        FROM api_keys
        WHERE id = $1 AND user_id = $2
        """,
        key_id, user_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    return _row_to_response(row)


@router.put("/{key_id}")
async def update_api_key(
    key_id: str,
    body: ApiKeyUpdate,
    request: Request,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db)
) -> ApiKeyResponse:
    enc = get_encryption(request)

    # Verify key belongs to user
    existing = await db.fetchrow(
        "SELECT id, provider, encrypted_key FROM api_keys WHERE id = $1 AND user_id = $2",
        key_id, user_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="API key not found")

    provider = existing["provider"]
    encrypted = existing["encrypted_key"]
    preview = None

    # Update key if provided
    if body.key is not None:
        raw_key = body.key.strip()

        # Validate key format
        fmt_valid, fmt_msg = validate_key_format(provider, raw_key)
        if not fmt_valid:
            raise HTTPException(status_code=400, detail=fmt_msg)

        encrypted = enc.encrypt(raw_key)
        preview = _mask_key(raw_key)

    # Update enabled status if provided
    is_enabled = body.is_enabled if body.is_enabled is not None else None

    # Build update query dynamically
    set_clauses = []
    params = []
    param_idx = 1

    if preview is not None:
        set_clauses.append(f"encrypted_key = ${param_idx}")
        params.append(encrypted)
        param_idx += 1
        set_clauses.append(f"key_preview = ${param_idx}")
        params.append(preview)
        param_idx += 1

    if is_enabled is not None:
        set_clauses.append(f"is_enabled = ${param_idx}")
        params.append(is_enabled)
        param_idx += 1

    if not set_clauses:
        # No changes requested
        row = await db.fetchrow(
            """
            SELECT id, provider, key_preview, is_enabled, created_at, updated_at, is_default
            FROM api_keys WHERE id = $1
            """,
            key_id,
        )
        return _row_to_response(row)

    # Add updated_at and key_id/user_id for WHERE clause
    set_clauses.append("updated_at = NOW()")
    params.extend([key_id, user_id])

    query = f"""
        UPDATE api_keys
        SET {', '.join(set_clauses)}
        WHERE id = ${param_idx} AND user_id = ${param_idx + 1}
        RETURNING id, provider, key_preview, is_enabled, created_at, updated_at, is_default
    """

    row = await db.fetchrow(query, *params)
    return _row_to_response(row)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    result = await db.execute(
        "DELETE FROM api_keys WHERE id = $1 AND user_id = $2",
        key_id, user_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="API key not found")


@router.post("/{key_id}/set-default")
async def set_default_api_key(
    key_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db)
) -> ApiKeyResponse:
    # Verify key belongs to user and get its details
    key_info = await db.fetchrow(
        """
        SELECT id, provider, project_id
        FROM api_keys
        WHERE id = $1 AND user_id = $2
        """,
        key_id, user_id,
    )
    if not key_info:
        raise HTTPException(status_code=404, detail="API key not found")

    # Unset any existing default for this user/provider/project
    await db.execute(
        """
        UPDATE api_keys
        SET is_default = FALSE
        WHERE user_id = $1 AND provider = $2
          AND (project_id = $3 OR (project_id IS NULL AND $3 IS NULL))
        """,
        user_id, key_info["provider"], key_info["project_id"]
    )

    # Set this key as default
    await db.execute(
        "UPDATE api_keys SET is_default = TRUE WHERE id = $1",
        key_id,
    )

    row = await db.fetchrow(
        """
        SELECT id, provider, key_preview, is_enabled, created_at, updated_at, is_default
        FROM api_keys WHERE id = $1
        """,
        key_id,
    )
    return _row_to_response(row)


# API Endpoints Endpoints (for OpenAI-compatible custom endpoints)
@router.post("/endpoints", status_code=status.HTTP_201_CREATED)
async def create_api_endpoint(
    body: ApiEndpointCreate,
    request: Request,
    user_id: str = Depends(require_user),
    project_id: str | None = Query(None, description="Project ID for project-scoped endpoint"),
    db: AsyncSession = Depends(get_db)
) -> ApiEndpointResponse:
    # Validate that if api_key_id is provided, it belongs to the user
    if body.api_key_id:
        key_check = await db.fetchrow(
            "SELECT id FROM api_keys WHERE id = $1 AND user_id = $2 AND is_enabled = true",
            body.api_key_id, user_id,
        )
        if not key_check:
            raise HTTPException(status_code=400, detail="Invalid API key ID or key not enabled")

    # Check if endpoint with this name already exists for user/project/provider
    query = """
        SELECT id FROM api_endpoints
        WHERE user_id = $1 AND provider = $2 AND name = $3
    """
    params = [user_id, body.provider.value, body.name]

    if project_id is not None:
        query += " AND project_id = $4"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    existing = await db.fetchrow(query, *params)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Endpoint '{body.name}' already exists for provider '{body.provider.value}'. Use a different name or update the existing one.",
        )

    # Determine if this should be the default endpoint
    is_first_endpoint = await _is_first_endpoint_for_user_provider(
        db, user_id, body.provider.value, project_id
    )

    endpoint_id = str(uuid.uuid4())

    await db.execute(
        """
        INSERT INTO api_endpoints
        (id, user_id, project_id, provider, name, base_url, api_key_id, is_default, headers, config)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        endpoint_id, user_id, project_id, body.provider.value, body.name,
        body.base_url, body.api_key_id, is_first_endpoint,
        body.headers or {}, body.config or {}
    )

    row = await db.fetchrow(
        """
        SELECT id, user_id, project_id, provider, name, base_url, api_key_id, is_default,
               headers, config, created_at, updated_at
        FROM api_endpoints WHERE id = $1
        """,
        endpoint_id,
    )
    return _endpoint_to_response(row)


@router.get("/endpoints", response_model=list[ApiEndpointResponse])
async def list_api_endpoints(
    request: Request,
    user_id: str = Depends(require_user),
    project_id: str | None = Query(None, description="Filter by project ID"),
    provider: str | None = Query(None, description="Filter by provider"),
    db: AsyncSession = Depends(get_db)
) -> list[ApiEndpointResponse]:
    # Build query
    query = """
        SELECT id, user_id, project_id, provider, name, base_url, api_key_id, is_default,
               headers, config, created_at, updated_at
        FROM api_endpoints
        WHERE user_id = $1
    """
    params = [user_id]
    param_idx = 2

    if project_id is not None:
        query += f" AND project_id = ${param_idx}"
        params.append(project_id)
        param_idx += 1
    else:
        query += " AND project_id IS NULL"

    if provider is not None:
        query += f" AND provider = ${param_idx}"
        params.append(provider)
        param_idx += 1

    query += " ORDER BY is_default DESC, updated_at DESC"

    rows = await db.fetch(query, *params)
    return [_endpoint_to_response(r) for r in rows]


@router.get("/endpoints/{endpoint_id}", response_model=ApiEndpointResponse)
async def get_api_endpoint(
    endpoint_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db)
) -> ApiEndpointResponse:
    row = await db.fetchrow(
        """
        SELECT id, user_id, project_id, provider, name, base_url, api_key_id, is_default,
               headers, config, created_at, updated_at
        FROM api_endpoints
        WHERE id = $1 AND user_id = $2
        """,
        endpoint_id, user_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="API endpoint not found")
    return _endpoint_to_response(row)


@router.put("/endpoints/{endpoint_id}")
async def update_api_endpoint(
    endpoint_id: str,
    body: ApiEndpointUpdate,
    request: Request,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db)
) -> ApiEndpointResponse:
    # Verify endpoint belongs to user
    existing = await db.fetchrow(
        "SELECT id, user_id FROM api_endpoints WHERE id = $1 AND user_id = $2",
        endpoint_id, user_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Validate api_key_id if provided
    if body.api_key_id:
        key_check = await db.fetchrow(
            "SELECT id FROM api_keys WHERE id = $1 AND user_id = $2 AND is_enabled = true",
            body.api_key_id, user_id,
        )
        if not key_check:
            raise HTTPException(status_code=400, detail="Invalid API key ID or key not enabled")

    # Build update query dynamically
    set_clauses = []
    params: list[Any] = []
    param_idx = 1

    if body.name is not None:
        # Check for name conflict (excluding current endpoint)
        conflict_check = await db.fetchrow(
            """
            SELECT id FROM api_endpoints
            WHERE user_id = $1 AND provider = $2 AND name = $3 AND id != $4
            """,
            user_id, existing["provider"], body.name, endpoint_id
        )
        if conflict_check:
            raise HTTPException(status_code=409, detail=f"Endpoint with name '{body.name}' already exists")

        set_clauses.append(f"name = ${param_idx}")
        params.append(body.name)
        param_idx += 1

    if body.base_url is not None:
        set_clauses.append(f"base_url = ${param_idx}")
        params.append(body.base_url)
        param_idx += 1

    if body.api_key_id is not None:
        set_clauses.append(f"api_key_id = ${param_idx}")
        params.append(body.api_key_id)
        param_idx += 1
    elif body.api_key_id is None:  # Explicitly set to NULL
        set_clauses.append(f"api_key_id = ${param_idx}")
        params.append(None)
        param_idx += 1

    if body.is_default is not None:
        set_clauses.append(f"is_default = ${param_idx}")
        params.append(body.is_default)
        param_idx += 1
        # If setting as default, unset others
        if body.is_default:
            await db.execute(
                """
                UPDATE api_endpoints
                SET is_default = FALSE
                WHERE user_id = $1 AND provider = $2
                  AND (project_id = $3 OR (project_id IS NULL AND $3 IS NULL))
                  AND id != $4
                """,
                user_id, existing["provider"], existing["project_id"], endpoint_id
            )

    if body.headers is not None:
        set_clauses.append(f"headers = ${param_idx}")
        params.append(body.headers)
        param_idx += 1

    if body.config is not None:
        set_clauses.append(f"config = ${param_idx}")
        params.append(body.config)
        param_idx += 1

    if not set_clauses:
        # No changes requested
        row = await db.fetchrow(
            """
            SELECT id, user_id, project_id, provider, name, base_url, api_key_id, is_default,
                   headers, config, created_at, updated_at
            FROM api_endpoints WHERE id = $1
            """,
            endpoint_id,
        )
        return _endpoint_to_response(row)

    # Add updated_at and IDs for WHERE clause
    set_clauses.append("updated_at = NOW()")
    params.extend([endpoint_id, user_id])

    query = f"""
        UPDATE api_endpoints
        SET {', '.join(set_clauses)}
        WHERE id = ${param_idx} AND user_id = ${param_idx + 1}
        RETURNING id, user_id, project_id, provider, name, base_url, api_key_id, is_default,
                  headers, config, created_at, updated_at
    """

    row = await db.fetchrow(query, *params)
    return _endpoint_to_response(row)


@router.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_endpoint(
    endpoint_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    result = await db.execute(
        "DELETE FROM api_endpoints WHERE id = $1 AND user_id = $2",
        endpoint_id, user_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="API endpoint not found")


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    request: Request,
    user_id: str = Depends(require_user),
    project_id: str | None = Query(None, description="Filter by project ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db)
) -> UsageStatsResponse:
    # Get usage statistics
    query = """
        SELECT
            provider,
            model,
            COUNT(*) as request_count,
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(cost_usd) as total_cost_usd,
            MIN(timestamp) as first_used,
            MAX(timestamp) as last_used
        FROM ai_usage
        WHERE user_id = $1
    """
    params = [user_id]
    param_idx = 2

    if project_id is not None:
        query += f" AND project_id = ${param_idx}"
        params.append(project_id)
        param_idx += 1
    else:
        query += " AND project_id IS NULL"

    # Add time filter
    query += f" AND timestamp >= NOW() - INTERVAL '{days} days'"
    query += " GROUP BY provider, model ORDER BY total_cost_usd DESC"

    rows = await db.fetch(query, *params)

    # Get daily data for charting
    daily_query = """
        SELECT
            DATE(timestamp) as date,
            SUM(cost_usd) as daily_cost,
            SUM(total_tokens) as daily_tokens
        FROM ai_usage
        WHERE user_id = $1
    """
    daily_params = [user_id]
    daily_param_idx = 2

    if project_id is not None:
        daily_query += f" AND project_id = ${daily_param_idx}"
        daily_params.append(project_id)
        daily_param_idx += 1
    else:
        daily_query += " AND project_id IS NULL"

    daily_query += f" AND timestamp >= NOW() - INTERVAL '{days} days'"
    daily_query += " GROUP BY DATE(timestamp) ORDER BY DATE(timestamp)"

    daily_rows = await db.fetch(daily_query, *daily_params)

    # Format response
    by_provider_model = []
    for row in rows:
        by_provider_model.append({
            "provider": row["provider"],
            "model": row["model"],
            "request_count": row["request_count"],
            "total_prompt_tokens": row["total_prompt_tokens"],
            "total_completion_tokens": row["total_completion_tokens"],
            "total_tokens": row["total_tokens"],
            "total_cost_usd": float(row["total_cost_usd"]),
            "first_used": row["first_used"].isoformat() if row["first_used"] else None,
            "last_used": row["last_used"].isoformat() if row["last_used"] else None,
        })

    daily_data = []
    for row in daily_rows:
        daily_data.append(UsageDataPoint(
            date=row["date"].isoformat(),
            cost_usd=float(row["daily_cost"]),
            tokens=int(row["daily_tokens"])
        ))

    total_cost = sum(item["total_cost_usd"] for item in by_provider_model)
    total_requests = sum(item["request_count"] for item in by_provider_model)

    return UsageStatsResponse(
        total_cost_usd=total_cost,
        total_requests=total_requests,
        by_provider_model=by_provider_model,
        daily_data=daily_data
    )


# Helper functions
async def _is_first_key_for_user_provider(
    db: AsyncSession,
    user_id: str,
    provider: str,
    project_id: str | None
) -> bool:
    """Check if this is the first key for the user/provider/project combination."""
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
    db: AsyncSession,
    user_id: str,
    provider: str,
    project_id: str | None
) -> bool:
    """Check if this is the first endpoint for the user/provider/project combination."""
    query = """
        SELECT COUNT(*) as count
        FROM api_endpoints
        WHERE user_id = $1 AND provider = $2
    """
    params = [user_id, provider]

    if project_id is not None:
        query += " AND project_id = $3"
        params.append(project_id)
    else:
        query += " AND project_id IS NULL"

    result = await db.fetchrow(query, *params)
    return result["count"] == 0


def _row_to_response(row) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=str(row["id"]),
        provider=row["provider"],
        key_preview=row["key_preview"],
        is_enabled=row["is_enabled"],
        is_default=row.get("is_default", False),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _endpoint_to_response(row) -> ApiEndpointResponse:
    return ApiEndpointResponse(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        project_id=str(row["project_id"]) if row["project_id"] else None,
        provider=row["provider"],
        name=row["name"],
        base_url=row["base_url"],
        api_key_id=str(row["api_key_id"]) if row["api_key_id"] else None,
        is_default=row["is_default"],
        headers=row["headers"] or {},
        config=row["config"] or {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# Dependency to get provider configuration for agent nodes
async def get_provider_config(
    request: Request,
    user_id: str,
    provider_type: str,
    model: str,
    project_id: str | None = None
) -> dict:
    """
    Get provider configuration (API key, endpoint, etc.) for use in agent nodes.
    Returns a dictionary with configuration needed to instantiate a provider.
    """
    enc = get_encryption(request)
    db = await get_db(request)

    # First try to get project-specific key/endpoint, then fall back to user-level
    config = None

    # Try project-specific first
    if project_id is not None:
        config = await _get_provider_config_for_project(db, enc, user_id, provider_type, model, project_id)

    # Fall back to user-level
    if config is None:
        config = await _get_provider_config_for_user(db, enc, user_id, provider_type, model)

    if config is None:
        # No configuration found - this will cause an error in the agent nodes
        # which is appropriate - they should handle missing credentials gracefully
        return {}

    return config


async def _get_provider_config_for_project(
    db: AsyncSession,
    enc: EncryptionService,
    user_id: str,
    provider_type: str,
    model: str,
    project_id: str
) -> dict | None:
    """Get provider configuration for project-level settings."""
    # Check for project-specific API key
    key_row = await db.fetchrow(
        """
        SELECT encrypted_key, provider_config
        FROM api_keys
        WHERE user_id = $1 AND provider = $2 AND project_id = $3 AND is_enabled = true
        ORDER BY is_default DESC, updated_at DESC
        LIMIT 1
        """,
        user_id, provider_type, project_id
    )

    if key_row:
        decrypted_key = enc.decrypt(key_row["encrypted_key"])
        provider_config = key_row["provider_config"] or {}

        # Check if there's a project-specific endpoint that should be used
        endpoint_row = await db.fetchrow(
            """
            SELECT base_url, api_key_id, headers, config
            FROM api_endpoints
            WHERE user_id = $1 AND provider = $2 AND project_id = $3 AND is_default = true
            LIMIT 1
            """,
            user_id, provider_type, project_id
        )

        base_url = None
        headers: dict[str, Any] = {}
        endpoint_config: dict[str, Any] = {}

        if endpoint_row:
            base_url = endpoint_row["base_url"]
            # If endpoint has its own API key, use that instead
            if endpoint_row["api_key_id"]:
                key_row = await db.fetchrow(
                    "SELECT encrypted_key FROM api_keys WHERE id = $1",
                    endpoint_row["api_key_id"]
                )
                if key_row:
                    decrypted_key = enc.decrypt(key_row["encrypted_key"])
            headers = endpoint_row["headers"] or {}
            endpoint_config = endpoint_row["config"] or {}

        # Merge configurations
        final_config = {
            "api_key": decrypted_key,
            "provider_config": {**provider_config, **endpoint_config},
        }

        if base_url:
            final_config["base_url"] = base_url
        if headers:
            final_config["headers"] = headers

        return final_config

    return None


async def _get_provider_config_for_user(
    db: AsyncSession,
    enc: EncryptionService,
    user_id: str,
    provider_type: str,
    model: str
) -> dict | None:
    """Get provider configuration for user-level settings."""
    # Check for user-specific API key
    key_row = await db.fetchrow(
        """
        SELECT encrypted_key, provider_config
        FROM api_keys
        WHERE user_id = $1 AND provider = $2 AND project_id IS NULL AND is_enabled = true
        ORDER BY is_default DESC, updated_at DESC
        LIMIT 1
        """,
        user_id, provider_type
    )

    if key_row:
        decrypted_key = enc.decrypt(key_row["encrypted_key"])
        provider_config = key_row["provider_config"] or {}

        # Check if there's a user-level endpoint that should be used
        endpoint_row = await db.fetchrow(
            """
            SELECT base_url, api_key_id, headers, config
            FROM api_endpoints
            WHERE user_id = $1 AND provider = $2 AND project_id IS NULL AND is_default = true
            LIMIT 1
            """,
            user_id, provider_type
        )

        base_url = None
        headers: dict[str, Any] = {}
        endpoint_config: dict[str, Any] = {}

        if endpoint_row:
            base_url = endpoint_row["base_url"]
            # If endpoint has its own API key, use that instead
            if endpoint_row["api_key_id"]:
                key_row = await db.fetchrow(
                    "SELECT encrypted_key FROM api_keys WHERE id = $1",
                    endpoint_row["api_key_id"]
                )
                if key_row:
                    decrypted_key = enc.decrypt(key_row["encrypted_key"])
            headers = endpoint_row["headers"] or {}
            endpoint_config = endpoint_row["config"] or {}

        # Merge configurations
        final_config = {
            "api_key": decrypted_key,
            "provider_config": {**provider_config, **endpoint_config},
        }

        if base_url:
            final_config["base_url"] = base_url
        if headers:
            final_config["headers"] = headers

        return final_config

    return None
