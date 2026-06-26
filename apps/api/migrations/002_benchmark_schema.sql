-- AgentForge Enhanced Benchmark Schema
-- PostgreSQL 16
-- Supports 4 conditions × 20 tasks = 80 experiments

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Benchmark Test Conditions
CREATE TABLE IF NOT EXISTS benchmark_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(10) NOT NULL, -- A, B, C, D
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    condition_type VARCHAR(20) NOT NULL -- single, team
);

CREATE TABLE IF NOT EXISTS benchmark_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condition_id UUID NOT NULL REFERENCES benchmark_conditions(id),
    task_type VARCHAR(50) NOT NULL, -- authentication, crud, sql, fastapi, react, typescript, testing, refactoring, documentation, bugfix
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL, -- easy, medium, hard
    ground_truth JSONB, -- objective correctness criteria
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_task_type CHECK (task_type IN ('authentication', 'crud', 'sql', 'fastapi', 'react', 'typescript', 'testing', 'refactoring', 'documentation', 'bugfix'))
);

CREATE TABLE IF NOT EXISTS benchmark_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    total_tasks INTEGER NOT NULL,
    completed_tasks INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES benchmark_runs(id),
    task_id UUID NOT NULL REFERENCES benchmark_tasks(id),
    execution_time_ms INTEGER NOT NULL,
    token_usage INTEGER NOT NULL,
    retry_count INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL, -- completed, failed, timeout
    final_output JSONB, -- code/analysis results
    metadata JSONB, -- evaluation criteria scores
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_status CHECK (status IN ('completed', 'failed', 'timeout'))
);

CREATE TABLE IF NOT EXISTS evaluation_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(50) NOT NULL,
    criteria VARCHAR(50) NOT NULL, -- correctness, code_quality, security, test_coverage, maintainability, cost, latency
    weight DECIMAL(5,4) NOT NULL, -- 0.0000 to 1.0000
    max_score INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_criteria CHECK (criteria IN ('correctness', 'code_quality', 'security', 'test_coverage', 'maintainability', 'cost', 'latency'))
);

CREATE TABLE IF NOT EXISTS benchmark_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id UUID NOT NULL REFERENCES benchmark_results(id),
    criteria VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL, -- 0 to max_score
    evaluator TEXT, -- 'human', 'llm_judge', 'auto'
    feedback TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index performance
CREATE INDEX IF NOT EXISTS idx_benchmark_tasks_condition ON benchmark_tasks(condition_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_run ON benchmark_results(run_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_task ON benchmark_results(task_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_evaluations_result ON benchmark_evaluations(result_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_status ON benchmark_runs(status);

-- Views for reporting
CREATE OR REPLACE VIEW v_benchmark_summary AS
SELECT
    bc.name AS condition,
    COUNT(br.id) AS tasks_completed,
    COUNT(CASE WHEN br.status = 'completed' THEN 1 END) AS successful_tasks,
    AVG(br.execution_time_ms) AS avg_execution_time_ms,
    AVG(br.token_usage) AS avg_tokens_used,
    AVG(br.retry_count) AS avg_retries,
    (COUNT(CASE WHEN br.status = 'completed' THEN 1 END)::DECIMAL / COUNT(br.id)) * 100 AS success_rate
FROM benchmark_conditions bc
LEFT JOIN benchmark_tasks bt ON bt.condition_id = bc.id
LEFT JOIN benchmark_results br ON br.task_id = bt.id
GROUP BY bc.name;

CREATE OR REPLACE VIEW v_criterion_breakdown AS
SELECT
    bc.name AS condition,
    bt.task_type,
    ec.criteria,
    AVG(be.score) AS avg_score,
    COUNT(be.id) AS evaluations_count,
    ec.weight AS weight
FROM benchmark_conditions bc
JOIN benchmark_tasks bt ON bt.condition_id = bc.id
JOIN benchmark_results br ON br.task_id = bt.id
JOIN benchmark_evaluations be ON be.result_id = br.id
JOIN evaluation_criteria ec ON ec.task_type = bt.task_type AND ec.criteria = be.criteria
GROUP BY bc.name, bt.task_type, ec.criteria, ec.weight;

CREATE OR REPLACE VIEW v_task_analysis AS
SELECT
    bt.task_type,
    bt.title,
    COUNT(br.id) AS total_runs,
    COUNT(CASE WHEN br.status = 'completed' THEN 1 END) AS successful_runs,
    AVG(br.execution_time_ms) AS avg_execution_time_ms,
    AVG(br.token_usage) AS avg_token_usage,
    STRING_AGG(DISTINCT be.feedback, '; ') AS all_feedback
FROM benchmark_tasks bt
LEFT JOIN benchmark_results br ON br.task_id = bt.id
LEFT JOIN benchmark_evaluations be ON be.result_id = br.id
GROUP BY bt.task_type, bt.title;

-- Database functions for automated scoring
CREATE OR REPLACE FUNCTION calculate_overall_score(result_id UUID) RETURNS DECIMAL AS $$
DECLARE
    total_score DECIMAL := 0;
    total_weight DECIMAL := 0;
    ev RECORD;
BEGIN
    FOR ev IN SELECT score, ec.weight FROM benchmark_evaluations be
                              JOIN evaluation_criteria ec ON ec.criteria = be.criteria
                            WHERE be.result_id = result_id
    LOOP
        total_score := total_score + (ev.score * ev.weight);
        total_weight := total_weight + ev.weight;
    END LOOP;
    
    IF total_weight > 0 THEN
        RETURN total_score / total_weight;
    END IF;
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION generate_benchmark_report(run_id UUID) RETURNS TABLE(
    condition VARCHAR,
    task_type VARCHAR,
    overall_score DECIMAL,
    success_rate DECIMAL,
    avg_execution_time_ms INTEGER,
    avg_token_usage INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        bc.name AS condition,
        bt.task_type,
        calculate_overall_score(br.id) AS overall_score,
        (COUNT(CASE WHEN br.status = 'completed' THEN 1 END)::DECIMAL / COUNT(br.id)) * 100 AS success_rate,
        AVG(br.execution_time_ms) AS avg_execution_time_ms,
        AVG(br.token_usage) AS avg_token_usage
    FROM benchmark_conditions bc
    JOIN benchmark_tasks bt ON bt.condition_id = bc.id
    JOIN benchmark_results br ON br.task_id = bt.id
    WHERE br.run_id = run_id
    GROUP BY bc.name, bt.task_type, br.id
    ORDER BY bc.name, bt.task_type;
END;
$$ LANGUAGE plpgsql;