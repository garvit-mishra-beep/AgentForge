-- Migration 022: Add pgvector support for agent memories
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE agent_memories ADD COLUMN IF NOT EXISTS embedding vector(1536);
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON agent_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
