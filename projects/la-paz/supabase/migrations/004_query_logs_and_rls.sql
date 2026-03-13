-- ================================================================
-- Migration: 004_query_logs_and_rls
-- Description: Fan Intelligence 쿼리 로깅 테이블 + 인덱스 + RLS
-- Date: 2026-02-20
-- PR: PR-1 (DB 마이그레이션)
-- Ref: docs/fan_intelligence_architecture.md Section 3, 6
-- ================================================================
-- NOTE: 멱등(idempotent). CREATE TABLE IF NOT EXISTS + DO $$ 사용.
--       fan_events 테이블은 삭제하지 않음 (병행 운영).
--       user_id FK 없음 — anon_id(SHA-256 해시)만 저장.
-- ================================================================

BEGIN;

-- ---------------------------------------------------------------
-- 1. query_logs 테이블
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS query_logs (
  id                uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Identity (익명화 — 평문 user_id 저장 금지)
  anon_id           text NOT NULL,              -- SHA-256(user_id + daily_salt)
  session_hash      text,                       -- SHA-256(session_id + daily_salt)

  -- Raw query
  query_text        text NOT NULL,
  ui_language       text NOT NULL DEFAULT 'ko', -- ISO 639-1: ko, en, ja, ...
  normalized_query  text,                       -- 영어 번역 (LLM 또는 rule-based)

  -- Classification (intent_classifier가 채움)
  intent_type       text,                       -- stat_lookup | comparison | news | opinion | prediction | transfer | injury | schedule | explainer
  team_tags         text[] DEFAULT '{}',        -- ["Manchester United", "Real Madrid"]
  player_tags       text[] DEFAULT '{}',        -- ["Heung-Min Son", "Mbappe"]
  league_tags       text[] DEFAULT '{}',        -- ["PL", "CL"]

  -- Context
  match_id          uuid,                       -- NULL 허용 — 특정 경기 참조 시에만
  retrieval_success boolean DEFAULT false,      -- RAG가 유용한 문서를 반환했는지
  confidence_score  real,                       -- 분류 신뢰도 (0.0 ~ 1.0)
  response_type     text,                       -- rag | web_fallback | direct_lookup | error

  -- Timestamps
  created_at        timestamptz DEFAULT now()
);

-- ---------------------------------------------------------------
-- 2. 성능 인덱스
-- ---------------------------------------------------------------

-- 시간 순 조회 (최신 로그, 날짜 범위 필터)
CREATE INDEX IF NOT EXISTS idx_ql_created
  ON query_logs (created_at DESC);

-- intent별 집계 (demand signal 생성 시 핵심)
CREATE INDEX IF NOT EXISTS idx_ql_intent_created
  ON query_logs (intent_type, created_at);

-- 태그 배열 검색 (GIN — JSONB/배열 전용)
CREATE INDEX IF NOT EXISTS idx_ql_league_tags
  ON query_logs USING GIN (league_tags);

CREATE INDEX IF NOT EXISTS idx_ql_team_tags
  ON query_logs USING GIN (team_tags);

CREATE INDEX IF NOT EXISTS idx_ql_player_tags
  ON query_logs USING GIN (player_tags);

-- anon_id별 세션 추적 (followup 감지용)
CREATE INDEX IF NOT EXISTS idx_ql_anon_created
  ON query_logs (anon_id, created_at);

-- ---------------------------------------------------------------
-- 3. RLS — service_role 전용 (외부 노출 금지)
-- ---------------------------------------------------------------
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;

-- anon/authenticated role: 모든 작업 차단
DO $$ BEGIN
  CREATE POLICY "query_logs_deny_all"
    ON query_logs
    FOR ALL
    USING (false);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- service_role은 RLS bypass이므로 별도 정책 불필요.
-- Supabase service_role key는 RLS를 무시하여 INSERT/SELECT 모두 가능.

-- ---------------------------------------------------------------
-- 4. 코멘트
-- ---------------------------------------------------------------
COMMENT ON TABLE query_logs IS
  'Fan Intelligence: 구조화된 쿼리 로그. 평문 user_id 저장 금지 — anon_id만 사용.';

COMMENT ON COLUMN query_logs.anon_id IS
  'SHA-256(user_id + daily_salt). 일일 salt 교체로 cross-day 추적 방지.';

COMMENT ON COLUMN query_logs.intent_type IS
  '9개 intent 중 하나: stat_lookup, comparison, news, opinion, prediction, transfer, injury, schedule, explainer. NULL 허용 (분류 실패 시).';

COMMENT ON COLUMN query_logs.retrieval_success IS
  'RAG 벡터 검색이 유용한 문서를 반환했는지 여부. false면 web fallback 또는 직접 조회 사용.';

COMMIT;
