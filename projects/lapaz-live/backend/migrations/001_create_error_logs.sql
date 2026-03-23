-- error_logs 테이블: RAG 파이프라인 에러를 추적하기 위한 로그 테이블
-- Supabase (PostgreSQL) 에서 실행

CREATE TABLE IF NOT EXISTS error_logs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id    TEXT NOT NULL,
    match_id      TEXT,
    question      TEXT NOT NULL,
    error_type    TEXT NOT NULL,          -- rate_limit / timeout / data_source / generation / unknown
    pipeline_stage TEXT NOT NULL,         -- classification / retrieval / structured_context / generation / router
    error_message TEXT NOT NULL,
    latency_ms    INTEGER,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 에러 유형별 집계를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_error_logs_error_type ON error_logs (error_type);

-- 시간 범위 조회를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs (created_at DESC);

-- request_id로 특정 요청의 에러 추적
CREATE INDEX IF NOT EXISTS idx_error_logs_request_id ON error_logs (request_id);

-- RLS 비활성화 (서비스 키로만 접근)
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service key full access on error_logs"
    ON error_logs
    FOR ALL
    USING (true)
    WITH CHECK (true);
