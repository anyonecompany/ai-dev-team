# PR-1 DB Verification Guide

> 대상 마이그레이션: `004_query_logs_and_rls.sql`, `005_demand_signals_and_rpc.sql`
> 작성일: 2026-02-20
> 검증 방법: Supabase SQL Editor 또는 `psql "$SUPABASE_DB_URL"`

---

## (a) 마이그레이션 적용 후 확인 SQL (8개)

### 1. 테이블 존재 확인

```sql
-- 기대: query_logs, demand_signals 두 행 반환
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('query_logs', 'demand_signals')
ORDER BY tablename;
```

**기대 결과:**
| tablename |
|-----------|
| demand_signals |
| query_logs |

---

### 2. query_logs 주요 컬럼 존재 확인

```sql
-- 기대: 15개 컬럼 반환
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'query_logs'
ORDER BY ordinal_position;
```

**기대 컬럼:**
| column_name | data_type | is_nullable |
|-------------|-----------|:-----------:|
| id | uuid | NO |
| anon_id | text | NO |
| session_hash | text | YES |
| query_text | text | NO |
| ui_language | text | NO |
| normalized_query | text | YES |
| intent_type | text | YES |
| team_tags | ARRAY | YES |
| player_tags | ARRAY | YES |
| league_tags | ARRAY | YES |
| match_id | uuid | YES |
| retrieval_success | boolean | YES |
| confidence_score | real | YES |
| response_type | text | YES |
| created_at | timestamp with time zone | YES |

---

### 3. demand_signals 주요 컬럼 존재 확인

```sql
-- 기대: 15개 컬럼 반환
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'demand_signals'
ORDER BY ordinal_position;
```

**기대 컬럼:**
| column_name | data_type | is_nullable |
|-------------|-----------|:-----------:|
| id | uuid | NO |
| signal_date | date | NO |
| entity_name | text | YES |
| entity_type | text | YES |
| intent_type | text | YES |
| league_code | text | YES |
| country_code | text | YES |
| ui_language | text | YES |
| query_count | integer | NO |
| unique_users | integer | NO |
| followup_rate | real | YES |
| rag_hit_rate | real | YES |
| intensity_score | real | YES |
| created_at | timestamp with time zone | YES |

---

### 4. 인덱스 존재 확인

```sql
-- 기대: query_logs 6개 + demand_signals 4개 + PK 2개 = 12개
SELECT
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('query_logs', 'demand_signals')
ORDER BY tablename, indexname;
```

**기대 인덱스:**
| tablename | indexname | 유형 |
|-----------|----------|------|
| demand_signals | demand_signals_pkey | PK |
| demand_signals | idx_ds_date_entity_type | B-tree (signal_date, entity_type) |
| demand_signals | idx_ds_entity_name | B-tree text_pattern_ops |
| demand_signals | idx_ds_intent_date | B-tree (intent_type, signal_date) |
| demand_signals | idx_ds_league_date | B-tree (league_code, signal_date) |
| query_logs | idx_ql_anon_created | B-tree (anon_id, created_at) |
| query_logs | idx_ql_created | B-tree (created_at DESC) |
| query_logs | idx_ql_intent_created | B-tree (intent_type, created_at) |
| query_logs | idx_ql_league_tags | **GIN** (league_tags) |
| query_logs | idx_ql_player_tags | **GIN** (player_tags) |
| query_logs | idx_ql_team_tags | **GIN** (team_tags) |
| query_logs | query_logs_pkey | PK |

---

### 5. RLS 활성화 확인

```sql
-- 기대: 두 테이블 모두 rowsecurity = true
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('query_logs', 'demand_signals')
ORDER BY tablename;
```

**기대 결과:**
| tablename | rowsecurity |
|-----------|:-----------:|
| demand_signals | true |
| query_logs | true |

---

### 6. anon role에서 query_logs SELECT 차단 확인

```sql
-- anon role로 전환 후 실행
SET ROLE anon;

-- 사전 조건: service_role로 테스트 행 삽입
-- INSERT INTO query_logs (anon_id, query_text) VALUES ('test', 'test query');

-- 기대: 0행 반환 (RLS policy "query_logs_deny_all" USING (false)로 차단)
SELECT count(*) FROM query_logs;

-- role 복원
RESET ROLE;
```

**기대 결과:** `count = 0` (행이 존재해도 anon에서 보이지 않음)

---

### 7. demand_signals k-anonymity 차단 확인

```sql
-- service_role로 테스트 데이터 삽입
INSERT INTO demand_signals (signal_date, entity_name, entity_type, intent_type, query_count, unique_users)
VALUES
  (current_date, 'Test Player A', 'player', 'stat_lookup', 10, 3),   -- k=3 < 5 → 차단 대상
  (current_date, 'Test Player B', 'player', 'stat_lookup', 20, 7);   -- k=7 >= 5 → 통과

-- anon role로 전환
SET ROLE anon;

-- 기대: 1행만 반환 (Test Player B만, unique_users >= 5)
SELECT entity_name, unique_users FROM demand_signals;

-- role 복원
RESET ROLE;

-- 정리
DELETE FROM demand_signals WHERE entity_name LIKE 'Test Player%';
```

**기대 결과:**
| entity_name | unique_users |
|-------------|:------------:|
| Test Player B | 7 |

(Test Player A는 `unique_users = 3 < 5`이므로 RLS에 의해 차단)

---

### 8. RPC 존재 확인

```sql
-- 기대: generate_demand_signals 함수 1행 반환
SELECT
  routine_name,
  routine_type,
  data_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'generate_demand_signals';
```

**기대 결과:**
| routine_name | routine_type | data_type |
|-------------|-------------|-----------|
| generate_demand_signals | FUNCTION | void |

추가 확인 (파라미터):

```sql
SELECT
  parameter_name,
  data_type,
  parameter_mode
FROM information_schema.parameters
WHERE specific_schema = 'public'
  AND specific_name LIKE 'generate_demand_signals%'
ORDER BY ordinal_position;
```

**기대 결과:**
| parameter_name | data_type | parameter_mode |
|----------------|-----------|:-----------:|
| start_date | date | IN |
| end_date | date | IN |

---

## (b) 롤백 전략

마이그레이션 004/005를 되돌리려면 아래 SQL을 **역순으로** 실행한다.

```sql
-- ================================================================
-- ROLLBACK: 005 먼저, 004 다음 (의존성 순서)
-- ================================================================

BEGIN;

-- 1. RPC 삭제 (005)
DROP FUNCTION IF EXISTS generate_demand_signals(date, date);

-- 2. demand_signals 정책 삭제 (005)
DROP POLICY IF EXISTS "demand_signals_k_anon_read" ON demand_signals;
DROP POLICY IF EXISTS "demand_signals_deny_write" ON demand_signals;
DROP POLICY IF EXISTS "demand_signals_deny_update" ON demand_signals;
DROP POLICY IF EXISTS "demand_signals_deny_delete" ON demand_signals;

-- 3. demand_signals 테이블 삭제 (005)
DROP TABLE IF EXISTS demand_signals;

-- 4. query_logs 정책 삭제 (004)
DROP POLICY IF EXISTS "query_logs_deny_all" ON query_logs;

-- 5. query_logs 테이블 삭제 (004) — 인덱스는 테이블과 함께 삭제됨
DROP TABLE IF EXISTS query_logs;

COMMIT;
```

**롤백 안전성:**
- `query_logs`와 `demand_signals`는 다른 테이블에 FK로 참조되지 않음
- `fan_events`, `trend_snapshots`는 삭제하지 않으므로 기존 기능 영향 없음
- `generate_trend_snapshot()` RPC는 유지됨
- 롤백 후 기존 B2B 엔드포인트 (`/b2b/trends`, `/b2b/fan-segments`, `/b2b/entity-buzz`) 정상 동작

---

## 체크리스트

| # | 확인 항목 | SQL | 기대 |
|---|----------|-----|------|
| 1 | 테이블 존재 | `pg_tables` 조회 | 2개 테이블 |
| 2 | query_logs 컬럼 | `information_schema.columns` | 15개 |
| 3 | demand_signals 컬럼 | `information_schema.columns` | 14개 |
| 4 | 인덱스 | `pg_indexes` | 12개 (GIN 3개 포함) |
| 5 | RLS 활성화 | `pg_tables.rowsecurity` | 두 테이블 모두 true |
| 6 | query_logs anon 차단 | `SET ROLE anon; SELECT` | 0행 |
| 7 | demand_signals k-anonymity | anon으로 k<5/k≥5 행 비교 | k<5 차단, k≥5 통과 |
| 8 | RPC 존재 | `information_schema.routines` | generate_demand_signals(date, date) → void |
