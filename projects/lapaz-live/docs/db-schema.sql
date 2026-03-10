-- La Paz Live Q&A Dashboard - Database Schema
-- Version: 1.0.0
-- Date: 2026-03-06
-- Database: SQLite (개발/MVP) → PostgreSQL (프로덕션 전환 가능)

-- 질문/답변 테이블
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,                          -- UUID v4
    question TEXT NOT NULL,                        -- 팬 질문 원문
    answer TEXT NOT NULL,                          -- RAG 생성 답변
    category TEXT NOT NULL,                        -- 질문 카테고리 (선수정보/전술/역사/규칙/이적/부상/기타)
    confidence REAL NOT NULL DEFAULT 0.0,          -- 답변 신뢰도 (0.0 ~ 1.0)
    source_count INTEGER NOT NULL DEFAULT 0,       -- 참조 소스 문서 수
    generation_time_ms INTEGER NOT NULL DEFAULT 0, -- 답변 생성 소요시간 (ms)
    status TEXT NOT NULL DEFAULT 'draft',          -- draft | published | archived
    match_context TEXT,                            -- JSON: {home_team, away_team, match_date, current_minute}
    created_at TEXT NOT NULL,                      -- ISO 8601 (UTC)
    updated_at TEXT NOT NULL                       -- ISO 8601 (UTC)
);

-- 인덱스: 상태별 조회 최적화
CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status);

-- 인덱스: 생성일 정렬
CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at DESC);
