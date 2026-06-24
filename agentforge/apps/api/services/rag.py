from __future__ import annotations

import re
import uuid
import logging
from typing import List, Optional, AsyncIterator

from apps.api.services.vector_store import vector_store, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


class TextChunker:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ".", " ", ""]

    def chunk_text(self, text: str) -> list[str]:
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            if end < text_len:
                best_pos = -1
                for sep in self.separators:
                    pos = text.rfind(sep, start, end)
                    if pos > start:
                        best_pos = pos + len(sep)
                        break
                if best_pos > 0 and best_pos < end:
                    end = best_pos
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.chunk_overlap if end < text_len else text_len

        return chunks if chunks else [text.strip()]


class RAGPipeline:
    def __init__(self, collection_prefix: str = "rag"):
        self.prefix = collection_prefix
        self.chunker = TextChunker()

    def _collection_name(self, tenant_id: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", tenant_id)
        return f"{self.prefix}_{safe}"

    async def ensure_collection(self, tenant_id: str) -> bool:
        return await vector_store.ensure_collection(
            collection_name=self._collection_name(tenant_id),
            dimension=EMBEDDING_DIMENSION,
        )

    async def ingest_document(
        self,
        tenant_id: str,
        document_id: str,
        text: str,
        metadata: Optional[dict] = None,
    ) -> int:
        coll = self._collection_name(tenant_id)
        await self.ensure_collection(tenant_id)

        chunks = self.chunker.chunk_text(text)
        points = []
        for i, chunk_text in enumerate(chunks):
            points.append({
                "id": f"{document_id}_{i}",
                "text": chunk_text,
                "document_id": document_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                **(metadata or {}),
            })

        count = await vector_store.upsert_points(coll, points)
        logger.info(f"Ingested {len(points)} chunks for document {document_id}")
        return len(points)

    async def search(
        self,
        tenant_id: str,
        query: str,
        limit: int = 5,
        score_threshold: Optional[float] = 0.5,
        filter_conditions: Optional[dict] = None,
    ) -> list[dict]:
        coll = self._collection_name(tenant_id)
        exists = await vector_store.client.collection_exists(coll)
        if not exists:
            return []

        results = await vector_store.search(
            collection_name=coll,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions=filter_conditions,
        )
        return [
            {
                "text": r.payload.get("text", ""),
                "score": r.score,
                "document_id": r.payload.get("document_id"),
                "chunk_index": r.payload.get("chunk_index"),
                **(r.payload or {}),
            }
            for r in results
        ]

    async def augment_prompt(
        self,
        tenant_id: str,
        query: str,
        system_prompt: str,
        limit: int = 3,
    ) -> str:
        contexts = await self.search(tenant_id, query, limit=limit)
        if not contexts:
            return system_prompt

        context_str = "\n\n".join(
            f"[Context {i+1}] (relevance: {c['score']:.2f})\n{c['text']}"
            for i, c in enumerate(contexts)
        )
        return f"{system_prompt}\n\nRelevant context:\n{context_str}"

    async def delete_document(self, tenant_id: str, document_id: str) -> int:
        coll = self._collection_name(tenant_id)
        return await vector_store.delete_points(
            collection_name=coll,
            filter_conditions={"document_id": document_id},
        )

    async def document_stats(self, tenant_id: str, document_id: str) -> dict:
        coll = self._collection_name(tenant_id)
        results, _ = await vector_store.scroll(
            collection_name=coll,
            limit=1000,
        )
        doc_chunks = [r for r in results if r.payload.get("document_id") == document_id]
        return {
            "document_id": document_id,
            "chunks": len(doc_chunks),
            "total_chunks": doc_chunks[0].payload.get("total_chunks", 0) if doc_chunks else 0,
        }


rag = RAGPipeline()
