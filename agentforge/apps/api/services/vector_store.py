from __future__ import annotations

import uuid
import hashlib
import logging
from typing import Any, List, Optional, Dict

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    VectorParams,
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    ScoredPoint,
    HnswConfigDiff,
    OptimizersConfigDiff,
)

from apps.api.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 1536  # OpenAI text-embedding-3-small


class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            return self._mock_embed(texts)
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.embeddings.create(model=self.model, input=texts)
        return [r.embedding for r in response.data]

    def _mock_embed(self, texts: list[str]) -> list[list[float]]:
        import hashlib
        dim = EMBEDDING_DIMENSION
        results = []
        for text in texts:
            h = hashlib.sha256(text.encode()).digest()
            vec = [((h[i % len(h)] + ord(c)) / 512.0 - 1.0) for i, c in enumerate(text.ljust(dim, " ")[:dim])]
            vec = vec + [0.0] * (dim - len(vec))
            results.append(vec[:dim])
        return results


class VectorStoreService:
    def __init__(self):
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30,
        )
        self.embedder = EmbeddingService()

    async def ensure_collection(
        self,
        collection_name: str,
        dimension: int = EMBEDDING_DIMENSION,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        exists = await self.client.collection_exists(collection_name)
        if not exists:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=distance),
                hnsw_config=HnswConfigDiff(m=16, ef_construct=200),
                optimizers_config=OptimizersConfigDiff(default_segment_number=2),
            )
            logger.info(f"Created Qdrant collection '{collection_name}'")
            return True
        return False

    async def upsert_points(
        self,
        collection_name: str,
        points: list[dict],
        payload_fields: Optional[list[str]] = None,
    ) -> int:
        texts = [p.get("text", "") for p in points]
        vectors = await self.embedder.embed(texts)
        point_structs = []
        for i, p in enumerate(points):
            point_id = str(p.get("id", uuid.uuid4()))
            payload = {k: v for k, v in p.items() if k != "text"}
            if payload_fields:
                payload = {k: payload.get(k) for k in payload_fields if k in payload}
            point_structs.append(
                PointStruct(
                    id=point_id,
                    vector=vectors[i],
                    payload={"text": p.get("text", ""), **payload},
                )
            )
        op_info = await self.client.upsert(
            collection_name=collection_name,
            points=point_structs,
            wait=True,
        )
        return len(points)

    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> list[ScoredPoint]:
        query_vector = (await self.embedder.embed([query]))[0]
        qdrant_filter = None
        if filter_conditions:
            conditions = []
            for key, value in filter_conditions.items():
                if isinstance(value, dict):
                    if "gte" in value or "lte" in value:
                        conditions.append(FieldCondition(key=key, range=Range(**value)))
                else:
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            qdrant_filter = Filter(must=conditions)

        results = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
        )
        return results

    async def delete_points(
        self,
        collection_name: str,
        point_ids: Optional[list[str]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> int:
        if point_ids:
            result = await self.client.delete(
                collection_name=collection_name,
                points_selector=point_ids,
                wait=True,
            )
        elif filter_conditions:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_conditions.items()
            ]
            result = await self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(must=conditions),
                wait=True,
            )
        else:
            raise ValueError("Either point_ids or filter_conditions required")
        return result.status

    async def scroll(
        self,
        collection_name: str,
        limit: int = 100,
        offset: Optional[str] = None,
    ) -> tuple[list[ScoredPoint], Optional[str]]:
        results, next_offset = await self.client.scroll(
            collection_name=collection_name,
            limit=limit,
            offset=offset,
        )
        return results, next_offset

    async def count(self, collection_name: str) -> int:
        count_result = await self.client.count(collection_name=collection_name)
        return count_result.count

    async def delete_collection(self, collection_name: str) -> bool:
        await self.client.delete_collection(collection_name)
        return True

    async def list_collections(self) -> list[str]:
        response = await self.client.get_collections()
        return [c.name for c in response.collections]

    async def health(self) -> dict:
        try:
            collections = await self.list_collections()
            return {"connected": True, "collections": len(collections), "names": collections}
        except Exception as e:
            logger.warning(f"Qdrant health check failed: {e}")
            return {"connected": False, "error": str(e)}


_vector_store_instance: VectorStoreService | None = None


def get_vector_store() -> VectorStoreService:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService()
    return _vector_store_instance


class _LazyVectorStore:
    def __getattr__(self, name):
        return getattr(get_vector_store(), name)


vector_store = _LazyVectorStore()
