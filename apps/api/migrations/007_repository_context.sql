-- Migration 007: Repository Context Engine
-- Stores parsed code structure for context extraction

CREATE TABLE IF NOT EXISTS repository_contexts (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES project_files(id) ON DELETE CASCADE,
    file_path VARCHAR(2048) NOT NULL,
    language VARCHAR(50) NOT NULL DEFAULT '',
    parsed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_message TEXT,
    UNIQUE(file_id)
);

CREATE TABLE IF NOT EXISTS code_symbols (
    id UUID PRIMARY KEY,
    context_id UUID NOT NULL REFERENCES repository_contexts(id) ON DELETE CASCADE,
    symbol_type VARCHAR(50) NOT NULL,
    name VARCHAR(500) NOT NULL,
    line_start INTEGER NOT NULL DEFAULT 0,
    line_end INTEGER NOT NULL DEFAULT 0,
    signature TEXT,
    docstring TEXT,
    visibility VARCHAR(20) DEFAULT 'public',
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS code_imports (
    id UUID PRIMARY KEY,
    context_id UUID NOT NULL REFERENCES repository_contexts(id) ON DELETE CASCADE,
    source VARCHAR(500) NOT NULL,
    alias VARCHAR(255) DEFAULT '',
    is_relative BOOLEAN NOT NULL DEFAULT false,
    line_number INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS code_dependencies (
    id UUID PRIMARY KEY,
    context_id UUID NOT NULL REFERENCES repository_contexts(id) ON DELETE CASCADE,
    depends_on_file_id UUID REFERENCES project_files(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'import',
    symbol_name VARCHAR(500) NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS code_chunks (
    id UUID PRIMARY KEY,
    context_id UUID NOT NULL REFERENCES repository_contexts(id) ON DELETE CASCADE,
    chunk_type VARCHAR(50) NOT NULL DEFAULT 'function',
    name VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    line_start INTEGER NOT NULL DEFAULT 0,
    line_end INTEGER NOT NULL DEFAULT 0,
    tokens_estimate INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_repo_context_project ON repository_contexts(project_id);
CREATE INDEX IF NOT EXISTS idx_code_symbols_context ON code_symbols(context_id);
CREATE INDEX IF NOT EXISTS idx_code_symbols_type ON code_symbols(symbol_type);
CREATE INDEX IF NOT EXISTS idx_code_imports_context ON code_imports(context_id);
CREATE INDEX IF NOT EXISTS idx_code_dependencies_context ON code_dependencies(context_id);
CREATE INDEX IF NOT EXISTS idx_code_dependencies_target ON code_dependencies(depends_on_file_id);
CREATE INDEX IF NOT EXISTS idx_code_chunks_context ON code_chunks(context_id);
CREATE INDEX IF NOT EXISTS idx_code_chunks_type ON code_chunks(chunk_type);
