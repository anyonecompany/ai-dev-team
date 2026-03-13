# DB 마이그레이션 적용 로그 — 2026-02-20

> 대상: Supabase SQL Editor
> 마이그레이션: `004_query_logs_and_rls.sql`, `005_demand_signals_and_rpc.sql`
> 작업자: Human Lead
> 상태: [ ] 미적용 / [ ] 적용 완료 / [ ] 롤백 완료

---

## STEP 1: 004_query_logs_and_rls.sql 적용

Supabase Dashboard → SQL Editor → New Query에 아래 전체를 붙여넣고 **Run** 클릭.

```sql
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
```

- [ ] **004 적용 완료** — "Success. No rows returned" 메시지 확인
- [ ] 에러 발생 시 메시지 기록: ___________________________________________

---

## STEP 2: 005_demand_signals_and_rpc.sql 적용

Supabase Dashboard → SQL Editor → New Query에 아래 전체를 붙여넣고 **Run** 클릭.

```sql
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
    ql.league_tags[1]                            AS league_code,
    NULL                                         AS country_code,
    ql.ui_language,
    count(*)                                     AS query_count,
    count(DISTINCT ql.anon_id)                   AS unique_users,
    0                                            AS followup_rate,
    avg(CASE WHEN ql.retrieval_success THEN 1.0 ELSE 0.0 END)
                                                 AS rag_hit_rate,
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
```

- [ ] **005 적용 완료** — "Success. No rows returned" 메시지 확인
- [ ] 에러 발생 시 메시지 기록: ___________________________________________

---

## STEP 3: 검증 쿼리 실행 (6개)

각 쿼리를 SQL Editor에서 개별 실행하고, 결과를 기대값과 대조한다.

### 검증 1: 테이블 존재 확인 (`to_regclass`)

```sql
SELECT
  to_regclass('public.query_logs')    AS query_logs_exists,
  to_regclass('public.demand_signals') AS demand_signals_exists;
```

**기대 결과:**

| query_logs_exists | demand_signals_exists |
|-------------------|----------------------|
| query_logs | demand_signals |

(NULL이면 테이블이 생성되지 않은 것)

- [ ] **검증 1 통과** — 두 컬럼 모두 NULL이 아님
- [ ] 실패 시 메모: ___________________________________________

---

### 검증 2: query_logs 컬럼 확인

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'query_logs'
ORDER BY ordinal_position;
```

**기대 결과 (15행):**

| column_name | data_type | is_nullable | column_default |
|-------------|-----------|:-----------:|----------------|
| id | uuid | NO | uuid_generate_v4() |
| anon_id | text | NO | |
| session_hash | text | YES | |
| query_text | text | NO | |
| ui_language | text | NO | 'ko'::text |
| normalized_query | text | YES | |
| intent_type | text | YES | |
| team_tags | ARRAY | YES | '{}'::text[] |
| player_tags | ARRAY | YES | '{}'::text[] |
| league_tags | ARRAY | YES | '{}'::text[] |
| match_id | uuid | YES | |
| retrieval_success | boolean | YES | false |
| confidence_score | real | YES | |
| response_type | text | YES | |
| created_at | timestamp with time zone | YES | now() |

- [ ] **검증 2 통과** — 15개 컬럼 확인
- [ ] 실패 시 메모: ___________________________________________

---

### 검증 3: demand_signals 컬럼 확인

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'demand_signals'
ORDER BY ordinal_position;
```

**기대 결과 (14행):**

| column_name | data_type | is_nullable | column_default |
|-------------|-----------|:-----------:|----------------|
| id | uuid | NO | uuid_generate_v4() |
| signal_date | date | NO | |
| entity_name | text | YES | |
| entity_type | text | YES | |
| intent_type | text | YES | |
| league_code | text | YES | |
| country_code | text | YES | |
| ui_language | text | YES | |
| query_count | integer | NO | 0 |
| unique_users | integer | NO | 0 |
| followup_rate | real | YES | 0 |
| rag_hit_rate | real | YES | 0 |
| intensity_score | real | YES | 0 |
| created_at | timestamp with time zone | YES | now() |

- [ ] **검증 3 통과** — 14개 컬럼 확인
- [ ] 실패 시 메모: ___________________________________________

---

### 검증 4: RLS 활성화 확인 (`pg_class.relrowsecurity`)

```sql
SELECT relname, relrowsecurity
FROM pg_class
WHERE relname IN ('query_logs', 'demand_signals')
  AND relkind = 'r'
ORDER BY relname;
```

**기대 결과:**

| relname | relrowsecurity |
|---------|:--------------:|
| demand_signals | true |
| query_logs | true |

- [ ] **검증 4 통과** — 두 테이블 모두 `true`
- [ ] 실패 시 메모: ___________________________________________

---

### 검증 5: 인덱스 확인 (`pg_indexes`)

```sql
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('query_logs', 'demand_signals')
ORDER BY tablename, indexname;
```

**기대 결과 (12행):**

| tablename | indexname |
|-----------|----------|
| demand_signals | demand_signals_pkey |
| demand_signals | idx_ds_date_entity_type |
| demand_signals | idx_ds_entity_name |
| demand_signals | idx_ds_intent_date |
| demand_signals | idx_ds_league_date |
| query_logs | idx_ql_anon_created |
| query_logs | idx_ql_created |
| query_logs | idx_ql_intent_created |
| query_logs | idx_ql_league_tags |
| query_logs | idx_ql_player_tags |
| query_logs | idx_ql_team_tags |
| query_logs | query_logs_pkey |

GIN 인덱스 확인 (3개):

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexdef LIKE '%USING gin%';
```

**기대:** `idx_ql_league_tags`, `idx_ql_team_tags`, `idx_ql_player_tags` 3행.

- [ ] **검증 5 통과** — B-tree 9개 + GIN 3개 = 12개
- [ ] 실패 시 메모: ___________________________________________

---

### 검증 6: RPC 존재 확인 (`information_schema.routines`)

```sql
SELECT routine_name, data_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'generate_demand_signals';
```

**기대 결과:**

| routine_name | data_type |
|-------------|-----------|
| generate_demand_signals | void |

- [ ] **검증 6 통과** — 1행, data_type = void
- [ ] 실패 시 메모: ___________________________________________

---

## STEP 4: 스모크 테스트 (INSERT + SELECT)

### 4-1. query_logs 테스트 INSERT (service_role로 실행)

```sql
INSERT INTO query_logs (anon_id, query_text, intent_type, team_tags, league_tags, retrieval_success)
VALUES (
  'abc123def456',
  '손흥민 이번 시즌 골 수',
  'stat_lookup',
  ARRAY['Tottenham Hotspur'],
  ARRAY['PL'],
  true
)
RETURNING id, anon_id, intent_type, created_at;
```

**기대:** 1행 반환, `id`는 UUID, `intent_type`은 `stat_lookup`.

- [ ] **4-1 통과** — INSERT RETURNING 성공
- [ ] 실패 시 메모: ___________________________________________

### 4-2. query_logs SELECT 확인

```sql
SELECT id, anon_id, query_text, intent_type, team_tags, league_tags, retrieval_success
FROM query_logs
ORDER BY created_at DESC
LIMIT 5;
```

**기대:** 방금 삽입한 행이 보임.

- [ ] **4-2 통과** — 삽입한 테스트 행 확인
- [ ] 실패 시 메모: ___________________________________________

### 4-3. 테스트 데이터 정리

```sql
DELETE FROM query_logs WHERE anon_id = 'abc123def456';
```

- [ ] **4-3 완료** — 테스트 행 삭제

---

## STEP 5: 최종 확인 체크리스트

| # | 항목 | 상태 |
|---|------|:----:|
| 1 | 004 마이그레이션 적용 | [ ] |
| 2 | 005 마이그레이션 적용 | [ ] |
| 3 | query_logs 테이블 존재 | [ ] |
| 4 | demand_signals 테이블 존재 | [ ] |
| 5 | query_logs 컬럼 15개 | [ ] |
| 6 | demand_signals 컬럼 14개 | [ ] |
| 7 | RLS 활성화 (두 테이블) | [ ] |
| 8 | 인덱스 12개 (GIN 3개 포함) | [ ] |
| 9 | generate_demand_signals RPC 존재 | [ ] |
| 10 | query_logs INSERT/SELECT 정상 | [ ] |
| 11 | 테스트 데이터 정리 완료 | [ ] |
| 12 | fan_events 테이블 영향 없음 | [ ] |
| 13 | trend_snapshots 테이블 영향 없음 | [ ] |
| 14 | 기존 B2B 엔드포인트 영향 없음 | [ ] |

---

## 롤백 (문제 발생 시)

```sql
BEGIN;
DROP FUNCTION IF EXISTS generate_demand_signals(date, date);
DROP POLICY IF EXISTS "demand_signals_k_anon_read" ON demand_signals;
DROP POLICY IF EXISTS "demand_signals_deny_write" ON demand_signals;
DROP POLICY IF EXISTS "demand_signals_deny_update" ON demand_signals;
DROP POLICY IF EXISTS "demand_signals_deny_delete" ON demand_signals;
DROP TABLE IF EXISTS demand_signals;
DROP POLICY IF EXISTS "query_logs_deny_all" ON query_logs;
DROP TABLE IF EXISTS query_logs;
COMMIT;
```

- [ ] 롤백 실행 여부: ___________________________________________

---

## 적용 기록

| 항목 | 값 |
|------|---|
| 적용 일시 | 2026-02-20 __:__ KST |
| 004 결과 | |
| 005 결과 | |
| 검증 1~6 | 모두 PASS / 실패 항목: |
| 스모크 테스트 | PASS / FAIL |
| 비고 | |
