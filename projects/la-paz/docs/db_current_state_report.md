# DB Current State Report

> 분석 방법: 코드/마이그레이션 기반 정적 분석 (실제 DB 연결 없음)
> 분석일: 2026-02-20
> 대상: `supabase/schema.sql` + `supabase/migrations/001~003` + `agents/*.py`
> 작성 목적: PR-1 (DB 마이그레이션) 실행 전 현재 상태 기록

---

## 1. Migration Status

### 마이그레이션 파일 목록

| 파일명 | 날짜 | 내용 |
|--------|------|------|
| `001_enable_rls_all_tables.sql` | 2026-02-18 | public 테이블 27개에 RLS 활성화 + 정책 적용 |
| `002_enable_rls_remaining_tables.sql` | 2026-02-19 | 001과 동일 대상 재적용 (멱등) + `team_stats`/`player_stats` 추가 시도 |
| `003_fix_search_path_warnings.sql` | 2026-02-19 | `match_documents()`, `generate_trend_snapshot()` 함수 `search_path` 설정 |

### Phase 1 관련 마이그레이션 존재 여부

| 항목 | 파일 존재 | 상태 |
|------|----------|------|
| `004_query_logs.sql` | **없음** | 미생성 |
| `005_demand_signals.sql` (또는 RPC) | **없음** | 미생성 |
| `query_logs` 관련 DDL | **어디에도 없음** | docs에만 설계 존재 |
| `demand_signals` 관련 DDL | **어디에도 없음** | docs에만 설계 존재 |
| `anonymize_id()` Python 함수 | **없음** | agents/ 코드에 미존재 |
| `intent_classifier.py` | **없음** | agents/ 디렉토리에 미존재 |

**결론:** Phase 1 TODO-01 ~ TODO-05에 해당하는 코드/스키마는 아직 아무것도 구현되지 않았다.

---

## 2. Table Existence

### 전체 테이블 (schema.sql 기준, 31개)

| 도메인 | 테이블명 | schema.sql | 비고 |
|--------|---------|:----------:|------|
| **Structure** | competitions | O | FK 기준점 (competition_id) |
| | seasons | O | |
| | teams | O | `canonical`, `aliases jsonb` 포함 |
| | players | O | |
| | managers | O | |
| | team_seasons | O | |
| | player_contracts | O | |
| | manager_tenures | O | |
| **Match** | matches | O | `source_id` unique |
| | lineups | O | `ON DELETE CASCADE` |
| | match_events | O | x/y 좌표 포함 |
| **Performance** | player_match_stats | O | xG/xA 포함 |
| | player_season_stats | O | |
| | team_match_stats | O | |
| | team_season_stats | O | **0행 이슈 (이전 분석에서 확인)** |
| **Narrative** | transfers | O | |
| | injuries | O | |
| | articles | O | |
| **Tactics** | formations | O | |
| **RAG** | documents | O | pgvector 384차원 |
| **Fan** | users | O | |
| | chat_sessions | O | |
| | chat_messages | O | |
| | fan_events | O | **Phase 1에서 query_logs로 역할 분리 예정** |
| | fan_predictions | O | |
| **B2B** | trend_snapshots | O | **Phase 1에서 demand_signals로 대체 예정** |
| | fan_segments | O | `criteria jsonb` 미사용 |
| | b2b_clients | O | `api_key` 보호 대상 |
| | b2b_api_logs | O | |
| **Pipeline** | agent_status | O | PK = `agent_name` |
| | pipeline_runs | O | |

### Phase 1 신규 테이블 (미존재)

| 테이블명 | schema.sql | migrations | agents 코드 | 상태 |
|----------|:----------:|:----------:|:-----------:|------|
| **query_logs** | X | X | X | **설계만 완료 (docs)** |
| **demand_signals** | X | X | X | **설계만 완료 (docs)** |

---

## 3. Column Audit

### fan_events (현재 쿼리 로깅 담당)

| 컬럼 | 타입 | 설명 | Phase 1 대응 |
|------|------|------|-------------|
| id | uuid PK | - | query_logs.id |
| user_id | uuid FK → users(id) | **PII — 평문 저장** | → `anon_id` (SHA-256 해시) |
| session_id | uuid | 세션 ID (평문) | → `session_hash` (해시) |
| event_type | text | chat/search/page_view/prediction/share | → `channel` (chat/search/stream) |
| entity_type | text | team/player/match/competition | → `entities_json` (배열 + confidence) |
| entity_id | text | 단일 엔티티 | → `entities_json` (복수 엔티티) |
| payload | jsonb | **비구조화** — 이벤트마다 스키마 다름 | → 개별 컬럼으로 분해 |
| created_at | timestamptz | - | query_logs.created_at |

**fan_events.payload 내부 (chat 이벤트 기준):**

```json
{"query": "...(200자)", "model": "gemini-2.0-flash", "source_count": 3}
```

Phase 1 query_logs에서 추가되는 컬럼 (fan_events에 없는 것):

| 신규 컬럼 | 용도 | fan_events 대응 |
|----------|------|----------------|
| `intent` | 9개 intent 분류 | 없음 |
| `sub_intent` | 세부 분류 | 없음 |
| `temporal_frame` | 시간 맥락 | 없음 |
| `rag_hit` | RAG 성공 여부 | 없음 |
| `latency_ms` | 응답 시간 | 없음 |
| `is_followup` | 재질문 여부 | 없음 |
| `query_position` | 세션 내 순서 | 없음 |
| `query_lang` | 감지 언어 | 없음 |

### trend_snapshots (현재 수요 집계 담당)

| 컬럼 | 타입 | 설명 | Phase 1 대응 |
|------|------|------|-------------|
| id | uuid PK | - | demand_signals.id |
| snapshot_date | date | - | → `signal_date` |
| metric_type | text | entity_buzz/topic_trend/query_volume | → `intent` (9개 분류) |
| entity_type | text | - | demand_signals.entity_type |
| entity_id | text | - | 제거 (demand_signals는 이름 기반) |
| entity_name | text | - | demand_signals.entity_name |
| value | real | 단순 카운트 | → `query_count` + `intensity_score` |
| sample_size | int | distinct user_id 수 | → `unique_users` |
| breakdown | jsonb | 시간대별 분포 | → `signal_hour` 컬럼으로 분해 |
| created_at | timestamptz | - | demand_signals.created_at |

Phase 1 demand_signals에서 추가되는 컬럼 (trend_snapshots에 없는 것):

| 신규 컬럼 | 용도 |
|----------|------|
| `signal_hour` | 시간별 세분화 (0-23) |
| `intent` | intent 분류별 집계 |
| `sub_intent` | 세부 분류별 집계 |
| `temporal_frame` | 시간 맥락별 집계 |
| `avg_latency_ms` | 평균 응답 시간 |
| `rag_hit_rate` | RAG 성공률 |
| `followup_rate` | 재질문 비율 (불만족 신호) |
| `intensity_score` | 수요 강도 점수 |

---

## 4. Index Audit

### 현재 인덱스 (schema.sql 기준)

| 테이블 | 인덱스명 | 유형 | 컬럼 |
|--------|---------|------|------|
| documents | `idx_documents_embedding` | IVFFlat (vector_cosine_ops, lists=50) | embedding |
| documents | `idx_documents_type` | B-tree | doc_type |
| articles | `idx_articles_published` | B-tree | published_at DESC |
| fan_events | `idx_fan_events_type` | B-tree | event_type |
| fan_events | `idx_fan_events_created` | B-tree | created_at |
| trend_snapshots | `idx_trend_date` | B-tree | snapshot_date |
| b2b_api_logs | `idx_b2b_logs_client` | B-tree | client_id, created_at |

**GIN 인덱스: 없음** (schema.sql에 GIN 인덱스 정의 없음)

### Phase 1에서 필요한 인덱스 (미존재)

| 테이블 | 인덱스명 | 유형 | 컬럼 | 용도 |
|--------|---------|------|------|------|
| query_logs | `idx_ql_anon` | B-tree | anon_id, created_at | 사용자별 쿼리 조회 |
| query_logs | `idx_ql_intent` | B-tree | intent, created_at | intent별 집계 |
| query_logs | `idx_ql_entity` | **GIN** | entities_json | 엔티티 검색 (JSONB) |
| query_logs | `idx_ql_temporal` | B-tree | temporal_frame, created_at | 시간 맥락별 집계 |
| demand_signals | `idx_ds_date` | B-tree | signal_date, intent | 날짜+intent 집계 |
| demand_signals | `idx_ds_entity` | B-tree | entity_name, signal_date | 엔티티별 추이 |

**주목:** `idx_ql_entity`는 이 프로젝트 최초의 GIN 인덱스가 된다.

---

## 5. RLS & Policy Audit

### RLS 활성화 상태 (schema.sql Section J + migrations 001/002)

| 테이블 | RLS 활성화 | 정책 | 접근 수준 |
|--------|:---------:|------|----------|
| competitions | O | `competitions_public_read` | anon/authenticated SELECT |
| seasons | O | `seasons_public_read` | anon/authenticated SELECT |
| teams | O | `teams_public_read` | anon/authenticated SELECT |
| players | O | `players_public_read` | anon/authenticated SELECT |
| managers | O | `managers_public_read` | anon/authenticated SELECT |
| team_seasons | O | `team_seasons_public_read` | anon/authenticated SELECT |
| player_contracts | O | `player_contracts_public_read` | anon/authenticated SELECT |
| manager_tenures | O | `manager_tenures_public_read` | anon/authenticated SELECT |
| matches | O | `matches_public_read` | anon/authenticated SELECT |
| lineups | O | `lineups_public_read` | anon/authenticated SELECT |
| match_events | O | `match_events_public_read` | anon/authenticated SELECT |
| player_match_stats | O | `player_match_stats_public_read` | anon/authenticated SELECT |
| player_season_stats | O | `player_season_stats_public_read` | anon/authenticated SELECT |
| team_match_stats | O | `team_match_stats_public_read` | anon/authenticated SELECT |
| team_season_stats | O | `team_season_stats_public_read` | anon/authenticated SELECT |
| transfers | O | `transfers_public_read` | anon/authenticated SELECT |
| injuries | O | `injuries_public_read` | anon/authenticated SELECT |
| articles | O | `articles_public_read` | anon/authenticated SELECT |
| formations | O | `formations_public_read` | anon/authenticated SELECT |
| documents | O | `documents_public_read` | anon/authenticated SELECT |
| users | O | `users_self_read`, `users_self_update` | `auth.uid() = id` |
| chat_sessions | O | `sessions_self` | `auth.uid() = user_id` |
| chat_messages | O | `messages_self` | session 소유자만 |
| fan_events | O | `fan_events_self_read`, `fan_events_self_insert` | `auth.uid() = user_id` |
| fan_predictions | O | `fan_predictions_self` | `auth.uid() = user_id` |
| b2b_clients | O | `b2b_clients_service_only` | **service_role 전용** (`USING (false)`) |
| b2b_api_logs | O | `b2b_logs_service_only` | **service_role 전용** |
| trend_snapshots | O | `trend_snapshots_public_read` | anon/authenticated SELECT |
| fan_segments | O | `fan_segments_public_read` | anon/authenticated SELECT |
| agent_status | O | `agent_status_service_only` | **service_role 전용** |
| pipeline_runs | O | `pipeline_runs_service_only` | **service_role 전용** |

### RLS 패턴 요약

| 패턴 | 테이블 수 | USING 조건 |
|------|----------|------------|
| 공개 읽기 전용 | 22개 | `USING (true)` |
| 사용자 자기 데이터만 | 5개 | `auth.uid() = user_id` |
| service_role 전용 | 4개 | `USING (false)` |
| **k-anonymity 필터** | **0개** | 미존재 |

### Phase 1에서 필요한 RLS 정책 (미존재)

| 테이블 | 정책명 | USING 조건 | 용도 |
|--------|-------|------------|------|
| query_logs | `query_logs_service_only` | `USING (false)` | 민감 데이터 — service_role만 접근 |
| demand_signals | `demand_signals_b2b_read` | `USING (true)` | 집계 데이터 공개 읽기 |
| demand_signals | `demand_signals_k_anon` | `USING (unique_users >= 5)` | **k-anonymity 최초 적용** |

**주목:** `demand_signals_k_anon`은 이 프로젝트 최초의 조건부 RLS 정책이 된다. 기존 정책은 모두 `true` 또는 `false`로 이진 제어만 하고 있다.

---

## 6. Gap Analysis (Phase 1 TODO 대비 부족한 부분)

### 전체 요약

| TODO | 항목 | 현재 상태 | 필요한 작업 |
|------|------|----------|-----------|
| **01** | `query_logs` 테이블 | **미존재** | DDL + 5 인덱스 생성 |
| **01** | `demand_signals` 테이블 | **미존재** | DDL + 2 인덱스 생성 |
| **02** | `query_logs` RLS | **미존재** | `USING (false)` service_role 전용 |
| **02** | `demand_signals` RLS + k-anonymity | **미존재** | `USING (true)` + `USING (unique_users >= 5)` |
| **03** | `generate_demand_signals()` RPC | **미존재** | PL/pgSQL 함수 생성 (hourly + daily rollup) |
| **04** | `anonymize_id()` | **미존재** | `shared_config.py`에 추가 (~25줄) |
| **05** | `classify_intent()` | **미존재** | `intent_classifier.py` 신규 파일 (~120줄) |

### 상세 Gap

#### Gap 1: 쿼리 데이터가 비구조화 상태

- **현재:** `fan_events.payload`에 `{"query": "...", "model": "...", "source_count": N}` 형태로 저장
- **문제:** intent, entity, temporal_frame, rag_hit, latency 등 핵심 분류 정보 없음
- **해소:** `query_logs` 테이블로 구조화 (TODO-01)

#### Gap 2: 사용자 ID가 평문 저장

- **현재:** `fan_events.user_id`가 `users.id` FK로 평문 UUID 저장
- **문제:** B2B 집계 시 개인정보 역추적 가능
- **해소:** `anonymize_id()` 함수로 일일 salt 기반 해시 (TODO-04)

#### Gap 3: 수요 신호 집계가 단순 카운트

- **현재:** `generate_trend_snapshot()` RPC는 `fan_events`에서 entity별 mention count + 시간대별 쿼리 수만 집계
- **문제:** intent 분류 없음, followup_rate 없음, intensity_score 없음
- **해소:** `generate_demand_signals()` RPC로 intent/entity/temporal 다차원 집계 (TODO-03)

#### Gap 4: intent 분류 기능 자체가 없음

- **현재:** 모든 쿼리가 동일 경로로 처리 (entity extraction → vector search → LLM generation)
- **문제:** "부상 질문"과 "순위 질문"이 같은 검색 전략 사용
- **해소:** `intent_classifier.py` 신규 생성 (TODO-05)

#### Gap 5: 조건부 RLS 부재

- **현재:** RLS 정책이 `USING (true)` 또는 `USING (false)`만 사용
- **문제:** `demand_signals`에 k-anonymity 필터(`unique_users >= 5`) 적용 불가
- **해소:** `demand_signals_k_anon` 정책 추가 (TODO-02)

#### Gap 6: GIN 인덱스 부재

- **현재:** 프로젝트 전체에 GIN 인덱스 0개
- **문제:** `query_logs.entities_json` (JSONB 배열) 검색 시 full scan
- **해소:** `idx_ql_entity` GIN 인덱스 추가 (TODO-01)

#### Gap 7: tests/ 디렉토리 부재

- **현재:** `la-paz/tests/` 디렉토리 자체가 없음
- **문제:** PR-2, PR-3의 pytest 테스트 실행 불가
- **해소:** `tests/` 디렉토리 생성 + `conftest.py` + 테스트 파일 (PR-2 범위)

### fan_events / trend_snapshots와의 관계

| 테이블 | Phase 1 이후 | 사유 |
|--------|-------------|------|
| `fan_events` | **유지** | 비쿼리 이벤트(page_view, prediction, share)에 계속 사용. 쿼리 이벤트(chat, search)는 `query_logs`로 이동. |
| `trend_snapshots` | **유지** | 기존 B2B 엔드포인트(`/b2b/trends`, `/b2b/entity-buzz`)가 참조 중. 즉시 삭제하면 엔드포인트 장애. |
| `generate_trend_snapshot()` RPC | **유지** | 기존 daily_crawl.py 또는 수동 호출에서 사용 중. 새 RPC와 병행. |
| `fan_segments` | **유지** | 미사용이지만 B2B 엔드포인트(`/b2b/fan-segments`)가 참조. |

**전환 전략:** `query_logs` + `demand_signals`가 안정화되면, `track_fan_event("chat", ...)` 호출을 `_log_query()`로 점진 교체. `trend_snapshots`는 `demand_signals`로 데이터 충분히 축적된 후 deprecated.

---

## Appendix: RPC 함수 현황

| 함수명 | 파라미터 | 정의 위치 | Phase 1 관련 |
|--------|---------|----------|:------------:|
| `match_documents(vector, int, text)` | query_embedding, match_count, filter_type | schema.sql:338 | X |
| `generate_trend_snapshot(date)` | target_date | schema.sql:492 | 간접 — demand_signals가 대체 예정 |
| `generate_demand_signals(date)` | target_date | **미존재** | O — TODO-03 |
