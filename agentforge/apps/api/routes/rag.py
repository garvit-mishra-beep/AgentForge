from __future__ import annotations

import uuid
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.dependencies.auth import get_current_active_user, get_tenant_id
from apps.api.services.rag import rag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])


class DocumentIngest(BaseModel):
    document_id: str
    text: str
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    score_threshold: Optional[float] = 0.5
    filter_conditions: Optional[dict] = None


class AugmentRequest(BaseModel):
    query: str
    system_prompt: str
    limit: int = 3


@router.post("/ingest", status_code=201)
async def ingest_document(
    payload: DocumentIngest,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: dict = Depends(get_current_active_user),
):
    count = await rag.ingest_document(
        tenant_id=str(tenant_id),
        document_id=payload.document_id,
        text=payload.text,
        metadata=payload.metadata,
    )
    return {"document_id": payload.document_id, "chunks_created": count}


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_id: Optional[str] = Form(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: dict = Depends(get_current_active_user),
):
    if file.content_type not in settings.ALLOWED_UPLOAD_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {', '.join(settings.ALLOWED_UPLOAD_MIME_TYPES)}",
        )

    content_bytes = await file.read()
    if len(content_bytes) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
        )

    content = content_bytes.decode("utf-8", errors="replace")
    doc_id = document_id or f"{uuid.uuid4()}"
    count = await rag.ingest_document(
        tenant_id=str(tenant_id),
        document_id=doc_id,
        text=content,
        metadata={"filename": file.filename, "content_type": file.content_type},
    )
    return {"document_id": doc_id, "filename": file.filename, "chunks_created": count}


@router.post("/search")
async def search_documents(
    payload: SearchRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: dict = Depends(get_current_active_user),
):
    results = await rag.search(
        tenant_id=str(tenant_id),
        query=payload.query,
        limit=payload.limit,
        score_threshold=payload.score_threshold,
        filter_conditions=payload.filter_conditions,
    )
    return {"results": results, "total": len(results)}


@router.post("/augment")
async def augment_prompt(
    payload: AugmentRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: dict = Depends(get_current_active_user),
):
    augmented = await rag.augment_prompt(
        tenant_id=str(tenant_id),
        query=payload.query,
        system_prompt=payload.system_prompt,
        limit=payload.limit,
    )
    return {"augmented_prompt": augmented}


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: dict = Depends(get_current_active_user),
):
    await rag.delete_document(tenant_id=str(tenant_id), document_id=document_id)


@router.get("/documents/{document_id}/stats")
async def document_stats(
    document_id: str,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: dict = Depends(get_current_active_user),
):
    stats = await rag.document_stats(tenant_id=str(tenant_id), document_id=document_id)
    return stats
