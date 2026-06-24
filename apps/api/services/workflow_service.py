"""
Workflow service.

Handles workflow lifecycle, execution, and state management.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.core.config import settings
from apps.api.core.database import async_session
from apps.api.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowStatus,
    ExecutionCreate,
    ExecutionResponse,
)

import hashlib
import numpy as np

logger = logging.getLogger(__name__)

async def get_embedding(text: str) -> List[float]:
    """
    Generate text embeddings using OpenAI/Gemini providers or numpy fallback.
    """
    from apps.api.core.config import settings
    
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
            return await embeddings.aembed_query(text)
        except Exception as e:
            logger.warning(f"Failed to fetch OpenAI embeddings: {e}. Falling back.")
            
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import GoogleGenAIEmbeddings
            embeddings = GoogleGenAIEmbeddings(google_api_key=settings.GEMINI_API_KEY, model="models/text-embedding-004")
            return await embeddings.aembed_query(text)
        except Exception as e:
            logger.warning(f"Failed to fetch Gemini embeddings: {e}. Falling back.")
            
    # NumPy/Hashing deterministic semantic-like vectorizer fallback
    try:
        vector = np.zeros(768, dtype=np.float32)
        words = [w.lower().strip() for w in text.split() if len(w.lower().strip()) > 2]
        if not words:
            words = [text[i:i+3] for i in range(len(text)-2)]
            
        for word in words:
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx = h % 768
            val = 1.0 + (h % 100) / 100.0
            vector[idx] += val
            
            for j in range(len(word) - 1):
                pair = word[j:j+2]
                h_pair = int(hashlib.md5(pair.encode('utf-8')).hexdigest(), 16)
                vector[h_pair % 768] += 0.3
                
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()
    except Exception as e:
        logger.error(f"Error in numpy fallback vectorizer: {e}")
        return [0.0] * 768

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    try:
        return float(np.dot(v1, v2))
    except Exception:
        return 0.0


# ===============================
# REAL DATABASE MODELS & PERSISTENCE
# ===============================

import json
from packages.state.models.workflow import (
    Workflow as DBWorkflow,
    Execution as DBExecution,
    Task as DBTask,
    EventLog as DBEventLog,
)
from packages.state.models.workflow_execution import (
    ProjectMemory,
    Message,
)

class WorkflowService:
    """
    Workflow service for CRUD operations in PostgreSQL.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize workflow service.

        Args:
            db: Database session
        """
        self.db = db

    def _to_workflow_response(self, db_workflow: DBWorkflow) -> WorkflowResponse:
        inputs_val = {}
        if db_workflow.inputs:
            try:
                inputs_val = json.loads(db_workflow.inputs)
            except Exception:
                inputs_val = {}

        output_schema_val = {}
        if db_workflow.output_schema:
            try:
                output_schema_val = json.loads(db_workflow.output_schema)
            except Exception:
                output_schema_val = {}

        return WorkflowResponse(
            id=db_workflow.id,
            workflow_id=db_workflow.workflow_id,
            name=db_workflow.name,
            description=db_workflow.description,
            status=WorkflowStatus(db_workflow.status),
            agent_type=db_workflow.agent_type,
            inputs=inputs_val,
            output_schema=output_schema_val,
            created_at=db_workflow.created_at,
            updated_at=db_workflow.updated_at,
            creator_id=db_workflow.creator_id,
        )

    async def create(
        self,
        workflow: WorkflowCreate,
        creator_id: Optional[str] = None,
    ) -> WorkflowResponse:
        """
        Create workflow in Postgres.
        """
        # Delete existing workflow if workflow_id already exists to prevent duplicate key errors
        existing_query = select(DBWorkflow).where(DBWorkflow.workflow_id == workflow.workflow_id)
        result = await self.db.execute(existing_query)
        existing = result.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.commit()

        db_workflow = DBWorkflow(
            workflow_id=workflow.workflow_id,
            name=workflow.name,
            description=workflow.description,
            agent_type=workflow.agent_type or "planner",
            inputs=json.dumps(workflow.inputs or {}),
            output_schema=json.dumps(workflow.output_schema or {}),
            timeout_seconds=workflow.timeout_seconds or 3600,
            max_retries=workflow.max_retries or 3,
            status=WorkflowStatus.CREATED.value,
            creator_id=creator_id,
        )
        self.db.add(db_workflow)
        await self.db.commit()
        await self.db.refresh(db_workflow)
        return self._to_workflow_response(db_workflow)

    async def list_workflows(
        self,
        offset: int = 0,
        limit: int = 20,
        status: Optional[WorkflowStatus] = None,
    ) -> List[WorkflowResponse]:
        """
        List workflows from Postgres.
        """
        query = select(DBWorkflow)
        if status:
            query = query.where(DBWorkflow.status == status.value)
        query = query.offset(offset).limit(limit).order_by(DBWorkflow.created_at.desc())

        result = await self.db.execute(query)
        db_workflows = result.scalars().all()
        return [self._to_workflow_response(w) for w in db_workflows]

    async def get(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """
        Get workflow by ID.
        """
        query = select(DBWorkflow).where(DBWorkflow.workflow_id == workflow_id)
        result = await self.db.execute(query)
        db_workflow = result.scalar_one_or_none()
        if not db_workflow:
            return None
        return self._to_workflow_response(db_workflow)

    async def search_memory(self, prompt: str) -> Optional[ProjectMemory]:
        """
        Search project_memories for similar prompt using semantic similarity.
        """
        results = await self.search_memories(prompt, limit=1)
        return results[0] if results else None

    async def save_memory(self, project_key: str, description: str, architecture: dict, code_artifacts: list) -> ProjectMemory:
        """
        Save project plan & artifacts to project_memories for future reuse.
        """
        # Delete if already exists
        existing_query = select(ProjectMemory).where(ProjectMemory.project_key == project_key)
        res = await self.db.execute(existing_query)
        existing = res.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.commit()
            
        embedding = await get_embedding(description)
        memory = ProjectMemory(
            project_key=project_key,
            description=description,
            architecture=json.dumps(architecture),
            code_artifacts=json.dumps(code_artifacts),
            embedding_data=json.dumps(embedding),
            embedding=embedding,
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    def _to_memory_response(self, memory: ProjectMemory) -> Any:
        """
        Convert ProjectMemory DB model to MemoryResponse schema.
        """
        from apps.api.schemas.memory import MemoryResponse
        
        arch_val = {}
        if memory.architecture:
            try:
                arch_val = json.loads(memory.architecture) if isinstance(memory.architecture, str) else memory.architecture
            except Exception:
                arch_val = {}

        artifacts_val = []
        if memory.code_artifacts:
            try:
                artifacts_val = json.loads(memory.code_artifacts) if isinstance(memory.code_artifacts, str) else memory.code_artifacts
            except Exception:
                artifacts_val = []

        return MemoryResponse(
            id=memory.id,
            project_key=memory.project_key,
            description=memory.description,
            architecture=arch_val,
            code_artifacts=artifacts_val,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
        )

    async def get_memory_by_id_or_key(self, id_or_key: str) -> Optional[ProjectMemory]:
        """
        Retrieve a single memory by either its unique project_key or UUID id.
        """
        query = select(ProjectMemory).where(
            (ProjectMemory.id == id_or_key) | (ProjectMemory.project_key == id_or_key)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_memories(self, offset: int = 0, limit: int = 20) -> List[ProjectMemory]:
        """
        Retrieve list of project memories.
        """
        query = select(ProjectMemory).offset(offset).limit(limit).order_by(ProjectMemory.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_memory(self, project_key: str, description: str, architecture: dict, code_artifacts: list) -> ProjectMemory:
        """
        Manually create a new project memory.
        """
        existing = await self.get_memory_by_id_or_key(project_key)
        if existing:
            raise ValueError(f"ProjectMemory with key '{project_key}' already exists.")

        embedding = await get_embedding(description)
        memory = ProjectMemory(
            project_key=project_key,
            description=description,
            architecture=json.dumps(architecture),
            code_artifacts=json.dumps(code_artifacts),
            embedding_data=json.dumps(embedding),
            embedding=embedding,
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def update_memory(
        self,
        id_or_key: str,
        description: Optional[str] = None,
        architecture: Optional[dict] = None,
        code_artifacts: Optional[list] = None
    ) -> Optional[ProjectMemory]:
        """
        Update memory fields.
        """
        memory = await self.get_memory_by_id_or_key(id_or_key)
        if not memory:
            return None

        if description is not None:
            memory.description = description
            embedding = await get_embedding(description)
            memory.embedding_data = json.dumps(embedding)
            memory.embedding = embedding
        if architecture is not None:
            memory.architecture = json.dumps(architecture)
        if code_artifacts is not None:
            memory.code_artifacts = json.dumps(code_artifacts)

        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def delete_memory(self, id_or_key: str) -> bool:
        """
        Delete project memory.
        """
        memory = await self.get_memory_by_id_or_key(id_or_key)
        if not memory:
            return False
        await self.db.delete(memory)
        await self.db.commit()
        return True

    async def search_memories(self, prompt: str, limit: int = 5) -> List[ProjectMemory]:
        """
        Search project_memories using semantic similarity and return top matches.
        """
        prompt_emb = await get_embedding(prompt)

        from apps.api.core.database import has_vector_extension
        if has_vector_extension():
            try:
                # Cosine distance operator <=> in pgvector. Cosine Distance = 1 - Cosine Similarity.
                # A cosine similarity >= 0.35 translates to cosine distance <= 0.65.
                # Order by distance ascending (closest match first).
                distance_expr = ProjectMemory.embedding.op('<=>')(prompt_emb)
                query = select(ProjectMemory).where(distance_expr <= 0.65).order_by(distance_expr).limit(limit)
                result = await self.db.execute(query)
                return list(result.scalars().all())
            except Exception as e:
                logger.error(f"Failed to search memories using pgvector query: {e}. Falling back to Python similarity search.")

        # Fallback Python-based similarity search
        query = select(ProjectMemory)
        result = await self.db.execute(query)
        memories = result.scalars().all()
        if not memories:
            return []

        matches = []
        for mem in memories:
            emb_source = mem.embedding if mem.embedding is not None else mem.embedding_data
            if not emb_source:
                try:
                    emb = await get_embedding(mem.description)
                    mem.embedding = emb
                    mem.embedding_data = json.dumps(emb)
                    self.db.add(mem)
                    await self.db.commit()
                except Exception as e:
                    logger.error(f"Failed to generate embedding for memory {mem.project_key}: {e}")
                    continue
            
            try:
                emb = emb_source if isinstance(emb_source, list) else json.loads(emb_source)
                sim = cosine_similarity(prompt_emb, emb)
                if sim >= 0.35:
                    matches.append((sim, mem))
            except Exception:
                continue

        # Sort matches by similarity score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:limit]]



class ExecutionService:
    """
    Execution service for workflow execution management in PostgreSQL.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize execution service.

        Args:
            db: Database session
        """
        self.db = db

    def generate_execution_id(self) -> str:
        """
        Generate execution ID.
        """
        return f"ex-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"

    def _to_execution_response(self, db_execution: DBExecution) -> ExecutionResponse:
        return ExecutionResponse(
            id=db_execution.execution_id,
            workflow_id=db_execution.workflow_id,
            status=db_execution.status,
            priority=db_execution.priority,
            cancel_on_timeout=db_execution.cancel_on_timeout,
            webhook_url=db_execution.webhook_url,
            created_at=db_execution.created_at,
            started_at=db_execution.started_at,
            completed_at=db_execution.completed_at,
            error=db_execution.error,
            result=db_execution.result,
            checkpoint=db_execution.checkpoint,
        )

    async def create_execution(
        self,
        workflow_id: str,
        execution_data: ExecutionCreate = None,
    ) -> ExecutionResponse:
        """
        Create execution.
        """
        execution_id = self.generate_execution_id()

        db_execution = DBExecution(
            workflow_id=workflow_id,
            execution_id=execution_id,
            status="pending",
            priority=execution_data.priority if execution_data else 5,
            cancel_on_timeout=execution_data.cancel_on_timeout if (execution_data and execution_data.cancel_on_timeout is not None) else True,
            webhook_url=execution_data.webhook_url if execution_data else None,
            result="{}",
            checkpoint="{}",
        )

        self.db.add(db_execution)
        
        # Also update workflow status to running
        workflow_query = select(DBWorkflow).where(DBWorkflow.workflow_id == workflow_id)
        wf_res = await self.db.execute(workflow_query)
        db_workflow = wf_res.scalar_one_or_none()
        if db_workflow:
            db_workflow.status = WorkflowStatus.RUNNING.value

        await self.db.commit()
        await self.db.refresh(db_execution)
        return self._to_execution_response(db_execution)

    async def list_executions(
        self,
        workflow_id: str,
        limit: int = 20,
    ) -> List[ExecutionResponse]:
        """
        List executions for a workflow.
        """
        query = select(DBExecution).where(DBExecution.workflow_id == workflow_id).limit(limit).order_by(DBExecution.created_at.desc())
        result = await self.db.execute(query)
        db_executions = result.scalars().all()
        return [self._to_execution_response(e) for e in db_executions]

    async def get_execution(
        self,
        workflow_id: str,
        execution_id: str,
    ) -> Optional[ExecutionResponse]:
        """
        Get specific execution.
        """
        query = select(DBExecution).where(
            DBExecution.workflow_id == workflow_id,
            DBExecution.execution_id == execution_id,
        )
        result = await self.db.execute(query)
        db_execution = result.scalar_one_or_none()
        if not db_execution:
            return None
        return self._to_execution_response(db_execution)

    async def update_execution_status(
        self,
        execution_id: str,
        status: str,
        error: Optional[str] = None,
    ) -> ExecutionResponse:
        """
        Update execution status.
        """
        query = select(DBExecution).where(DBExecution.execution_id == execution_id)
        result = await self.db.execute(query)
        db_execution = result.scalar_one_or_none()
        if not db_execution:
            raise ValueError(f"Execution not found: {execution_id}")

        db_execution.status = status
        db_execution.error = error
        if status in ("running", "resuming"):
            if not db_execution.started_at:
                db_execution.started_at = datetime.utcnow()
        elif status in ("completed", "failed", "cancelled"):
            db_execution.completed_at = datetime.utcnow()
            
            # Update workflow status as well
            workflow_query = select(DBWorkflow).where(DBWorkflow.workflow_id == db_execution.workflow_id)
            wf_res = await self.db.execute(workflow_query)
            db_workflow = wf_res.scalar_one_or_none()
            if db_workflow:
                if status == "completed":
                    db_workflow.status = WorkflowStatus.COMPLETED.value
                elif status == "failed":
                    db_workflow.status = WorkflowStatus.FAILED.value
                elif status == "cancelled":
                    db_workflow.status = WorkflowStatus.CANCELLED.value

        await self.db.commit()
        await self.db.refresh(db_execution)
        return self._to_execution_response(db_execution)

    async def update_execution_result(
        self,
        execution_id: str,
        result_data: dict,
        checkpoint_data: dict = None,
    ):
        """
        Save final execution results and state to PostgreSQL.
        """
        query = select(DBExecution).where(DBExecution.execution_id == execution_id)
        result = await self.db.execute(query)
        db_execution = result.scalar_one_or_none()
        if db_execution:
            db_execution.result = json.dumps(result_data)
            if checkpoint_data:
                db_execution.checkpoint = json.dumps(checkpoint_data)
            await self.db.commit()


    async def add_event(
        self,
        execution_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> ExecutionResponse:
        """
        Add event log entry.
        """
        event_id = f"ev-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        db_event = DBEventLog(
            workflow_id=execution_id,  # foreign key points to executions.execution_id
            event_id=event_id,
            event_type=event_type,
            status=data.get("status", "info"),
            data=json.dumps(data),
            related_id=data.get("related_id"),
            related_type=data.get("related_type"),
            checkpoint=json.dumps(data.get("checkpoint", {})),
        )
        self.db.add(db_event)
        await self.db.commit()

        query = select(DBExecution).where(DBExecution.execution_id == execution_id)
        result = await self.db.execute(query)
        db_execution = result.scalar_one_or_none()
        return self._to_execution_response(db_execution)

    async def start_execution(
        self,
        execution_id: str,
    ) -> ExecutionResponse:
        """
        Start execution.
        """
        return await self.update_execution_status(execution_id, "running")

    async def execute_workflow(
        self,
        execution_id: str,
        workflow_id: str,
    ) -> ExecutionResponse:
        """
        Execute workflow. Note: Real LangGraph execution will be done from workflows route.
        """
        # Complete execution immediately for default sync/mock behaviors
        execution = await self.start_execution(execution_id)
        
        await self.add_event(
            execution_id,
            "execution.started",
            {"workflow_id": workflow_id},
        )
        
        # In-memory mock complete
        await self.update_execution_status(execution_id, "completed")
        
        await self.add_event(
            execution_id,
            "execution.completed",
            {"workflow_id": workflow_id},
        )
        
        # Query again to get updated object
        query = select(DBExecution).where(DBExecution.execution_id == execution_id)
        result = await self.db.execute(query)
        db_execution = result.scalar_one_or_none()
        return self._to_execution_response(db_execution)

    async def get_execution_messages(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve messages for a given execution.
        """
        from packages.state.models.workflow_execution import Message
        query = select(Message).where(Message.execution_id == execution_id).order_by(Message.timestamp.asc())
        result = await self.db.execute(query)
        db_messages = result.scalars().all()
        return [
            {
                "id": m.message_id,
                "role": m.role,
                "content": m.content,
                "timestamp": float(m.timestamp)
            } for m in db_messages
        ]

    def package_project_zip(self, execution_id: str, artifacts: List[Dict[str, Any]]) -> bytes:
        """
        Package code artifacts into a deployable zip file structure.
        """
        import io
        import zipfile
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for art in artifacts:
                name = art.get("name")
                content = art.get("content", "")
                if not name:
                    continue
                zip_file.writestr(name, content)
                
            if not artifacts:
                zip_file.writestr("README.md", "# Default Project\nGenerated by AgentOS.")
                
        return zip_buffer.getvalue()

    def write_project_files_to_disk(self, execution_id: str, artifacts: List[Dict[str, Any]]):
        """
        Write generated code files to a folder hierarchy under projects/{execution_id}.
        """
        import os
        base_dir = os.path.join("projects", execution_id)
        os.makedirs(base_dir, exist_ok=True)
        
        for art in artifacts:
            name = art.get("name")
            content = art.get("content", "")
            if not name:
                continue
            file_path = os.path.join(base_dir, name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)



# ===============================
# FACTORY
# ===============================


def create_workflow_service(db: AsyncSession) -> WorkflowService:
    """
    Create workflow service.
    """
    return WorkflowService(db)


def create_execution_service(db: AsyncSession) -> ExecutionService:
    """
    Create execution service.
    """
    return ExecutionService(db)
