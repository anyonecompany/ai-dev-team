-- ================================================================
-- Migration: 005_demand_signals_and_rpc
-- Description: 수요 신호 집계 테이블 + k-anonymity RLS + 집계 RPC
-- Date: 2026-02-20
-- PR: PR-1 (DB 마이그레이션)
-- Ref: docs/fan_intelligence_architecture.md Section 5, 6
-- ================================================================
-- NOTE: 멱등(idempotent). CREATE TABLE IF NOT EXISTS 사용.
--       trend_snapshots 테이블은 삭제하지 않음 (병행 운영).
--       generate_trend_snapshot() RPC도 유지 — 기존 B2B 엔드포인트가 참조.
-- ================================================================

BEGIN;

-- ---------------------------------------------------------------
-- 1. demand_signals 테이블
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS demand_signals (
  id                uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- 시간 차원
  signal_date       date NOT NULL,

  -- 엔티티 차원
  entity_name       text,                       -- 정규화된 엔티티명 (영어)
  entity_type       text,                       -- player | team | competition

  -- 분류 차원
  intent_type       text,                       -- stat_lookup | comparison | ... (query_logs.intent_type과 동일)

  -- 지역/언어 차원
  league_code       text,                       -- PL, PD, BL1, ... (league_registry 코드)
  country_code      text,                       -- ISO 3166-1 alpha-2: GB, ES, DE, ...
  ui_language       text,                       -- ISO 639-1: ko, en, ja, ...

  -- 핵심 지표
  query_count       int NOT NULL DEFAULT 0,
  unique_users      int NOT NULL DEFAULT 0,     -- count(distinct anon_id) — k-anonymity 기준

  -- 품질/만족도 지표
  followup_rate     real DEFAULT 0,             -- 재질문 비율 (0.0 ~ 1.0). 높을수록 불만족.
  rag_hit_rate      real DEFAULT 0,             -- RAG 성공률 (0.0 ~ 1.0). 낮을수록 콘텐츠 부족.
  intensity_score   real DEFAULT 0,             -- query_count * (1 + followup_rate) / max(unique_users, 1)

  -- Meta
  created_at        timestamptz DEFAULT now()
);

-- ---------------------------------------------------------------
-- 2. 인덱스
-- ---------------------------------------------------------------

-- 날짜 + 엔티티 유형별 집계 (B2B 대시보드 패턴)
CREATE INDEX IF NOT EXISTS idx_ds_date_entity_type
  ON demand_signals (signal_date, entity_type);

-- 리그 + 날짜별 집계 (리그별 수요 분석)
CREATE INDEX IF NOT EXISTS idx_ds_league_date
  ON demand_signals (league_code, signal_date);

-- 엔티티명 검색 (prefix/pattern 검색 대비)
CREATE INDEX IF NOT EXISTS idx_ds_entity_name
  ON demand_signals (entity_name text_pattern_ops);

-- intent별 날짜 집계
CREATE INDEX IF NOT EXISTS idx_ds_intent_date
  ON demand_signals (intent_type, signal_date);

-- ---------------------------------------------------------------
-- 3. RLS — k-anonymity 필터
-- ---------------------------------------------------------------
ALTER TABLE demand_signals ENABLE ROW LEVEL SECURITY;

-- anon/authenticated role: unique_users >= 5인 행만 SELECT 허용
DO $$ BEGIN
  CREATE POLICY "demand_signals_k_anon_read"
    ON demand_signals
    FOR SELECT
    USING (unique_users >= 5);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- anon/authenticated role: INSERT/UPDATE/DELETE 차단
DO $$ BEGIN
  CREATE POLICY "demand_signals_deny_write"
    ON demand_signals
    FOR INSERT
    WITH CHECK (false);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "demand_signals_deny_update"
    ON demand_signals
    FOR UPDATE
    USING (false);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE POLICY "demand_signals_deny_delete"
    ON demand_signals
    FOR DELETE
    USING (false);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- service_role은 RLS bypass이므로 전체 행 접근 + 쓰기 가능.

-- ---------------------------------------------------------------
-- 4. generate_demand_signals() RPC
-- ---------------------------------------------------------------
-- query_logs에서 날짜 구간을 집계하여 demand_signals에 UPSERT.
-- followup_rate, rag_hit_rate, intensity_score는 최소 계산으로 구현.
-- 핵심 목적: 스키마 + 집계 경로를 열어두는 것.
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_demand_signals(
  start_date date,
  end_date   date
)
RETURNS void
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  -- 기존 구간 데이터 삭제 후 재삽입 (idempotent)
  DELETE FROM demand_signals
  WHERE signal_date >= start_date
    AND signal_date <= end_date;

  -- query_logs에서 날짜별 + entity + intent + league 단위 집계
  INSERT INTO demand_signals (
    signal_date,
    entity_name,
    entity_type,
    intent_type,
    league_code,
    country_code,
    ui_language,
    query_count,
    unique_users,
    followup_rate,
    rag_hit_rate,
    intensity_score
  )
  SELECT
    ql.created_at::date                          AS signal_date,
    unnest_tag                                   AS entity_name,
    'team'                                       AS entity_type,
    ql.intent_type,
    ql.league_tags[1]                            AS league_code,   -- 첫 번째 리그 태그 (단순화)
    NULL                                         AS country_code,  -- 추후 league_registry에서 조인
    ql.ui_language,
    count(*)                                     AS query_count,
    count(DISTINCT ql.anon_id)                   AS unique_users,
    -- followup_rate: 추후 is_followup 컬럼 추가 시 정교화 (현재 기본값 0)
    0                                            AS followup_rate,
    -- rag_hit_rate: retrieval_success 기반 비율
    avg(CASE WHEN ql.retrieval_success THEN 1.0 ELSE 0.0 END)
                                                 AS rag_hit_rate,
    -- intensity_score: query_count / max(unique_users, 1)
    -- (followup_rate가 0이므로 단순 계산)
    count(*)::real / greatest(count(DISTINCT ql.anon_id), 1)
                                                 AS intensity_score
  FROM query_logs ql,
       LATERAL unnest(ql.team_tags) AS unnest_tag
  WHERE ql.created_at >= start_date::timestamptz
    AND ql.created_at <  (end_date + interval '1 day')::timestamptz
    AND ql.intent_type IS NOT NULL
  GROUP BY 1, 2, 3, 4, 5, 6, 7

  UNION ALL

  -- player_tags 집계 (동일 구조, entity_type = 'player')
  SELECT
    ql.created_at::date,
    unnest_tag,
    'player',
    ql.intent_type,
    ql.league_tags[1],
    NULL,
    ql.ui_language,
    count(*),
    count(DISTINCT ql.anon_id),
    0,
    avg(CASE WHEN ql.retrieval_success THEN 1.0 ELSE 0.0 END),
    count(*)::real / greatest(count(DISTINCT ql.anon_id), 1)
  FROM query_logs ql,
       LATERAL unnest(ql.player_tags) AS unnest_tag
  WHERE ql.created_at >= start_date::timestamptz
    AND ql.created_at <  (end_date + interval '1 day')::timestamptz
    AND ql.intent_type IS NOT NULL
  GROUP BY 1, 2, 3, 4, 5, 6, 7;

END;
$$;

-- ---------------------------------------------------------------
-- 5. 코멘트
-- ---------------------------------------------------------------
COMMENT ON TABLE demand_signals IS
  'Fan Intelligence: 집계된 수요 신호. k-anonymity(unique_users>=5) RLS 적용. trend_snapshots과 병행 운영.';

COMMENT ON COLUMN demand_signals.unique_users IS
  'distinct anon_id 수. RLS 정책으로 5 미만인 행은 non-service role에서 조회 불가.';

COMMENT ON COLUMN demand_signals.intensity_score IS
  'query_count * (1 + followup_rate) / max(unique_users, 1). 높을수록 강한 수요 신호.';

COMMENT ON FUNCTION generate_demand_signals(date, date) IS
  'query_logs에서 날짜 구간을 집계하여 demand_signals에 UPSERT. 기존 구간 데이터를 삭제 후 재삽입.';

COMMIT;
