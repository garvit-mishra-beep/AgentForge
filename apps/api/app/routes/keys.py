import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_user, DEMO_USER_ID
from core.encryption import EncryptionService
from core.validation import (
    get_provider_info,
    validate_key_format,
    validate_key_live,
)
from models.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyUpdate,
    ApiKeyValidateRequest,
    ApiKeyValidateResponse,
    ProviderInfoResponse,
)

router = APIRouter(prefix="/keys", tags=["keys"])

_encryption: EncryptionService | None = None


def _enc(request: Request) -> EncryptionService:
    global _encryption
    if _encryption is None:
        _encryption = EncryptionService()
    return _encryption


def _db(request: Request):
    return request.app.state.db


@router.get("/providers")
async def list_providers() -> ProviderInfoResponse:
    return ProviderInfoResponse(providers=get_provider_info())


@router.post("/validate")
async def validate_key(body: ApiKeyValidateRequest) -> ApiKeyValidateResponse:
    provider = body.provider.value
    fmt_valid, fmt_msg = validate_key_format(provider, body.key)
    if not fmt_valid:
        return ApiKeyValidateResponse(
            valid=False, provider=body.provider,
            message=fmt_msg, format_valid=False, live_valid=None,
        )

    live_valid, live_msg = await validate_key_live(provider, body.key)
    return ApiKeyValidateResponse(
        valid=live_valid, provider=body.provider,
        message=live_msg, format_valid=True, live_valid=live_valid,
    )


@router.post("", status_code=201)
async def create_api_key(
    body: ApiKeyCreate,
    request: Request,
    user_id: str = Depends(require_user),
) -> ApiKeyResponse:
    db = _db(request)
    enc = _enc(request)
    provider = body.provider.value
    raw_key = body.key

    fmt_valid, fmt_msg = validate_key_format(provider, raw_key)
    if not fmt_valid:
        raise HTTPException(status_code=400, detail=fmt_msg)

    existing = await db.fetchrow(
        "SELECT id FROM api_keys WHERE user_id = $1 AND provider = $2",
        user_id, provider,
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"API key for '{provider}' already exists. Use PUT to update.",
        )

    encrypted = enc.encrypt(raw_key)
    preview = enc.mask_key(raw_key)
    key_id = str(uuid.uuid4())

    await db.execute(
        "INSERT INTO api_keys (id, user_id, provider, encrypted_key, key_preview, is_enabled) VALUES ($1, $2, $3, $4, $5, true)",
        key_id, user_id, provider, encrypted, preview,
    )

    row = await db.fetchrow(
        "SELECT id, provider, key_preview, is_enabled, created_at, updated_at FROM api_keys WHERE id = $1",
        key_id,
    )
    return _row_to_response(row)


@router.get("")
async def list_api_keys(
    request: Request,
    user_id: str = Depends(require_user),
) -> list[ApiKeyResponse]:
    db = _db(request)
    rows = await db.fetch(
        "SELECT id, provider, key_preview, is_enabled, created_at, updated_at FROM api_keys WHERE user_id = $1 ORDER BY provider",
        user_id,
    )
    return [_row_to_response(r) for r in rows]


@router.get("/{key_id}")
async def get_api_key(
    key_id: str,
    request: Request,
    user_id: str = Depends(require_user),
) -> ApiKeyResponse:
    db = _db(request)
    row = await db.fetchrow(
        "SELECT id, provider, key_preview, is_enabled, created_at, updated_at FROM api_keys WHERE id = $1 AND user_id = $2",
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
) -> ApiKeyResponse:
    db = _db(request)
    enc = _enc(request)

    existing = await db.fetchrow(
        "SELECT id, provider, encrypted_key FROM api_keys WHERE id = $1 AND user_id = $2",
        key_id, user_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="API key not found")

    provider = existing["provider"]
    encrypted = existing["encrypted_key"]
    preview = None

    if body.key is not None:
        fmt_valid, fmt_msg = validate_key_format(provider, body.key)
        if not fmt_valid:
            raise HTTPException(status_code=400, detail=fmt_msg)
        encrypted = enc.encrypt(body.key)
        preview = enc.mask_key(body.key)

    is_enabled = body.is_enabled if body.is_enabled is not None else None

    if preview and is_enabled is not None:
        await db.execute(
            "UPDATE api_keys SET encrypted_key = $1, key_preview = $2, is_enabled = $3, updated_at = NOW() WHERE id = $4",
            encrypted, preview, is_enabled, key_id,
        )
    elif preview:
        await db.execute(
            "UPDATE api_keys SET encrypted_key = $1, key_preview = $2, updated_at = NOW() WHERE id = $3",
            encrypted, preview, key_id,
        )
    elif is_enabled is not None:
        await db.execute(
            "UPDATE api_keys SET is_enabled = $1, updated_at = NOW() WHERE id = $2",
            is_enabled, key_id,
        )

    row = await db.fetchrow(
        "SELECT id, provider, key_preview, is_enabled, created_at, updated_at FROM api_keys WHERE id = $1",
        key_id,
    )
    return _row_to_response(row)


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: str,
    request: Request,
    user_id: str = Depends(require_user),
) -> None:
    db = _db(request)
    result = await db.execute(
        "DELETE FROM api_keys WHERE id = $1 AND user_id = $2",
        key_id, user_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="API key not found")


def _row_to_response(row) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=str(row["id"]), provider=row["provider"],
        key_preview=row["key_preview"], is_enabled=row["is_enabled"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )
