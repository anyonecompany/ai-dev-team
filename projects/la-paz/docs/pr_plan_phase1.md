# La Paz — Phase 1 PR 계획서

> 기준 문서: `docs/next_steps_phase1.md` (TODO-01 ~ TODO-05)
> 생성일: 2026-02-20
> 제약: 신규 B2B 엔드포인트 금지 · CLAUDE.md 수정 금지 · 커스텀 ML 금지
> 대상 브랜치: `main` (trunk-based)

---

## PR-1: DB 마이그레이션 — query_logs, demand_signals, RLS

> TODO-01 + TODO-02 통합

### 목적

팬 쿼리 구조 로깅(`query_logs`)과 수요 신호 집계(`demand_signals`) 테이블을 생성하고,
RLS 정책으로 query_logs는 service_role 전용, demand_signals는 k-anonymity(k≥5) 필터를 적용한다.

### 1) 변경 파일 목록

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `supabase/migrations/004_query_logs.sql` | **신규** | query_logs 테이블, 5개 인덱스, RLS enable + service_only 정책 |
| `supabase/migrations/005_demand_signals.sql` | **신규** | demand_signals 테이블, 2개 인덱스, RLS enable + b2b_read + k_anon 정책 |

### 2) 마이그레이션 파일명

- `supabase/migrations/004_query_logs.sql`
- `supabase/migrations/005_demand_signals.sql`

### 3) 테스트 실행 명령

마이그레이션은 Supabase Dashboard SQL Editor 또는 `psql`로 실행 후 검증:

```bash
# 마이그레이션 적용 (Supabase CLI 사용 시)
supabase db push

# 검증 1: 테이블 존재 확인
psql "$SUPABASE_DB_URL" -c "\dt query_logs"
psql "$SUPABASE_DB_URL" -c "\dt demand_signals"

# 검증 2: 인덱스 확인 (7개)
psql "$SUPABASE_DB_URL" -c "SELECT indexname FROM pg_indexes WHERE tablename IN ('query_logs','demand_signals');"

# 검증 3: INSERT 테스트
psql "$SUPABASE_DB_URL" -c "INSERT INTO query_logs (anon_id, query_text, channel) VALUES ('test_anon', 'test query', 'chat') RETURNING id;"

# 검증 4: RLS — anon role이 query_logs 접근 불가
psql "$SUPABASE_DB_URL" -c "SET ROLE anon; SELECT count(*) FROM query_logs;"
# 기대값: 0행 (RLS policy blocks)

# 검증 5: k-anonymity — unique_users < 5 필터링
psql "$SUPABASE_DB_URL" -c "INSERT INTO demand_signals (signal_date, intent, query_count, unique_users) VALUES (current_date, 'test', 10, 3);"
psql "$SUPABASE_DB_URL" -c "SET ROLE anon; SELECT count(*) FROM demand_signals;"
# 기대값: 0행 (k=3 < 5)
psql "$SUPABASE_DB_URL" -c "INSERT INTO demand_signals (signal_date, intent, query_count, unique_users) VALUES (current_date, 'test2', 10, 5);"
psql "$SUPABASE_DB_URL" -c "SET ROLE anon; SELECT count(*) FROM demand_signals WHERE intent='test2';"
# 기대값: 1행 (k=5 ≥ 5)
```

### 4) 롤백 전략

```sql
DROP POLICY IF EXISTS "query_logs_service_only" ON query_logs;
DROP POLICY IF EXISTS "demand_signals_b2b_read" ON demand_signals;
DROP POLICY IF EXISTS "demand_signals_k_anon" ON demand_signals;
DROP TABLE IF EXISTS demand_signals;
DROP TABLE IF EXISTS query_logs;
```

단일 트랜잭션으로 실행. 다른 테이블에 FK 의존성 없으므로 안전.

### 5) DoD

- [ ] `query_logs` 테이블이 Supabase에 존재하고 INSERT/SELECT 동작
- [ ] `demand_signals` 테이블이 Supabase에 존재하고 INSERT/SELECT 동작
- [ ] `pg_indexes`에서 7개 인덱스 확인 (`idx_ql_anon`, `idx_ql_intent`, `idx_ql_entity`, `idx_ql_temporal`, `idx_ds_date`, `idx_ds_entity` + PK 인덱스)
- [ ] anon role로 `query_logs` SELECT 시 0행 반환
- [ ] anon role로 `demand_signals` SELECT 시 `unique_users < 5` 행 필터링됨
- [ ] 기존 테이블(`fan_events`, `chat_messages` 등)에 영향 없음

---

## PR-2: anonymize_id + log_query 헬퍼 (테스트 포함)

> TODO-04 + TODO-08 (next_steps_phase1.md) 통합
> 선행 조건: PR-1 머지 완료

### 목적

user_id를 일일 salt 기반 SHA-256으로 익명화하는 `anonymize_id()` 함수와,
분류 결과 + 응답 메타데이터를 `query_logs`에 논블로킹 삽입하는 `_log_query()` 헬퍼를 구현한다.

### 1) 변경 파일 목록

| 파일 | 변경 유형 | 예상 변경량 | 설명 |
|------|----------|-----------|------|
| `agents/shared_config.py` | **수정** | +25줄 | `_get_daily_salt()`, `anonymize_id()` 함수 추가 (파일 하단) |
| `agents/agent_5_api.py` | **수정** | +35줄 | `_log_query()` 헬퍼 함수 추가, import 추가 |
| `tests/test_anonymize.py` | **신규** | ~40줄 | `anonymize_id()` 단위 테스트 4건 |
| `tests/test_log_query.py` | **신규** | ~50줄 | `_log_query()` 단위 테스트 2건 (정상 삽입 + 실패 시 논블로킹 확인) |

### 2) 마이그레이션 파일명

없음. DB 변경 없음 (PR-1에서 테이블 생성 완료 전제).

### 3) 테스트 실행 명령

```bash
cd /Users/danghyeonsong/ai-dev-team/projects/la-paz

# anonymize_id 단위 테스트
python3 -m pytest tests/test_anonymize.py -v

# log_query 단위 테스트 (Supabase 연결 필요 — mock 또는 실제 DB)
python3 -m pytest tests/test_log_query.py -v

# 전체
python3 -m pytest tests/ -v
```

**테스트 케이스 명세:**

`tests/test_anonymize.py`:
| # | 케이스 | 입력 | 기대 |
|---|--------|------|------|
| 1 | 동일 user+같은 날 → 같은 해시 | `anonymize_id("user1")` 2회 호출 | 두 반환값 동일 |
| 2 | 동일 user+다른 날 → 다른 해시 | salt 강제 교체 후 호출 | 두 반환값 다름 |
| 3 | None 입력 → "anonymous" 기반 해시 | `anonymize_id(None)` | 길이 16, 예외 없음 |
| 4 | 반환 길이 | 임의 입력 | `len(result) == 16` |

`tests/test_log_query.py`:
| # | 케이스 | 조건 | 기대 |
|---|--------|------|------|
| 1 | 정상 삽입 | 유효한 Supabase 연결 | `query_logs`에 행 1건 생성 |
| 2 | 연결 실패 시 논블로킹 | Supabase URL을 잘못된 값으로 | 예외 없이 `None` 반환 |

### 4) 롤백 전략

- `agents/shared_config.py`: `anonymize_id()`, `_get_daily_salt()`, `_DAILY_SALT`, `_SALT_DATE` 제거 + `import hashlib` 제거
- `agents/agent_5_api.py`: `_log_query()` 함수 제거 + `from shared_config import anonymize_id` 제거
- `tests/test_anonymize.py`, `tests/test_log_query.py`: 파일 삭제

모든 변경이 신규 함수 추가이므로 기존 동작에 영향 없음. 제거만으로 롤백 완료.

### 5) DoD

- [ ] `anonymize_id("user1")`이 16자 hex 문자열 반환
- [ ] 같은 날 동일 입력 → 동일 출력 (결정적)
- [ ] 다른 날(salt 교체) → 다른 출력 (비가역성)
- [ ] `_log_query()`가 `query_logs`에 행을 삽입
- [ ] `_log_query()`가 Supabase 실패 시 예외를 던지지 않음
- [ ] `python3 -m pytest tests/ -v` 전체 PASS (6건)
- [ ] 기존 `/chat`, `/search` 엔드포인트 동작에 변화 없음 (이 PR에서는 연결하지 않음)

---

## PR-3: intent_classifier (LLM + fallback) + 최소 /chat 연결 (테스트 포함)

> TODO-05 + TODO-06 + TODO-07 + TODO-09 (최소 연결) 통합
> 선행 조건: PR-2 머지 완료

### 목적

Gemini Flash 구조화 출력으로 intent를 분류하는 `classify_intent()`와
키워드 기반 fallback `classify_intent_fallback()`, 그리고 이 둘을 감싸는 `safe_classify()`를 구현한다.
`/chat` 엔드포인트 1개소에만 최소 연결하여, 분류 결과를 `_log_query()`에 전달한다.

### 1) 변경 파일 목록

| 파일 | 변경 유형 | 예상 변경량 | 설명 |
|------|----------|-----------|------|
| `agents/intent_classifier.py` | **신규** | ~120줄 | `classify_intent()`, `classify_intent_fallback()`, `safe_classify()`, `CLASSIFY_PROMPT`, `RULE_PATTERNS`, `VALID_INTENTS` |
| `agents/agent_5_api.py` | **수정** | ~15줄 (net) | `/chat` 핸들러에 `safe_classify()` 호출 + `_log_query()` 연결. 기존 `track_fan_event("chat", ...)` 호출은 유지 (삭제하지 않음). |
| `tests/test_intent_classifier.py` | **신규** | ~80줄 | LLM 분류 테스트 3건, fallback 테스트 3건, safe_classify 통합 테스트 3건 |
| `tests/test_chat_classification.py` | **신규** | ~45줄 | `/chat` 엔드포인트 호출 → query_logs 기록 확인 통합 테스트 2건 |

### 2) 마이그레이션 파일명

없음. DB 변경 없음.

### 3) 테스트 실행 명령

```bash
cd /Users/danghyeonsong/ai-dev-team/projects/la-paz

# intent_classifier 단위 테스트
python3 -m pytest tests/test_intent_classifier.py -v

# /chat 연결 통합 테스트 (Supabase + Gemini API key 필요)
python3 -m pytest tests/test_chat_classification.py -v

# 전체 (PR-2 테스트 포함)
python3 -m pytest tests/ -v
```

**테스트 케이스 명세:**

`tests/test_intent_classifier.py`:
| # | 함수 | 케이스 | 입력 | 기대 |
|---|------|--------|------|------|
| 1 | `classify_intent` | 한국어 stat 쿼리 | `"손흥민 이번 시즌 골 수"` | `intent=="stat_lookup"`, entities에 `"Son"` 또는 `"Heung-Min Son"` 포함 |
| 2 | `classify_intent` | 영어 transfer 쿼리 | `"Mbappe transfer rumor"` | `intent=="transfer"` |
| 3 | `classify_intent` | 잘못된 API key | `GOOGLE_API_KEY=""` 환경 | 예외 발생 (fallback 위임 위해) |
| 4 | `classify_intent_fallback` | 부상 키워드 | `"살라 부상 복귀"` | `intent=="injury"` |
| 5 | `classify_intent_fallback` | 일정 키워드 | `"다음 경기 일정"` | `intent=="schedule"` |
| 6 | `classify_intent_fallback` | 미매칭 | `"안녕하세요"` | `intent==None` |
| 7 | `safe_classify` | 정상 Gemini | 유효한 API key + 쿼리 | dict 반환, `intent`가 9개 중 하나 |
| 8 | `safe_classify` | Gemini 실패 + fallback 매칭 | `GOOGLE_API_KEY=""` + `"이적 뉴스"` | `intent=="transfer"` (fallback 경유) |
| 9 | `safe_classify` | 전부 실패 | `GOOGLE_API_KEY=""` + `"ㅎㅎ"` | `{"intent": None, ...}` 반환, 예외 없음 |

`tests/test_chat_classification.py`:
| # | 케이스 | 조건 | 기대 |
|---|--------|------|------|
| 1 | 정상 분류 + 로깅 | `/chat` POST `{"message": "손흥민 골 수"}` | 기존 응답 형식 유지 + `query_logs`에 `intent` 행 생성 |
| 2 | 분류 실패 시 응답 정상 | `GOOGLE_API_KEY=""` + fallback 미매칭 쿼리 | 채팅 응답 정상 반환 + `query_logs`에 `intent=null` 행 생성 |

### 4) 롤백 전략

- `agents/intent_classifier.py`: 파일 삭제
- `agents/agent_5_api.py`: `/chat` 핸들러에서 `safe_classify()` 호출 + `_log_query()` 호출 코드 제거 (3~5줄). `track_fan_event("chat", ...)` 호출이 유지되므로 기존 동작 완전 복원.
- `tests/test_intent_classifier.py`, `tests/test_chat_classification.py`: 파일 삭제

`/chat` 핸들러의 변경이 추가(additive) 전용이므로 제거만으로 롤백 완료. 기존 `track_fan_event`는 삭제하지 않았으므로 팬 이벤트 추적도 유지됨.

### 5) DoD

- [ ] `agents/intent_classifier.py` 파일 존재, 3개 public 함수 export (`classify_intent`, `classify_intent_fallback`, `safe_classify`)
- [ ] `safe_classify()`가 어떤 입력에서도 예외를 던지지 않고 dict 반환
- [ ] 반환 dict에 최소한 `intent`, `entities`, `is_followup` 키 존재
- [ ] `intent` 값이 `VALID_INTENTS` 9개 중 하나이거나 `None`
- [ ] `/chat` POST 호출 시 `query_logs`에 1행 기록됨 (intent 포함)
- [ ] `/chat` 기존 응답 형식 (`ChatResp`: answer, sources, model, latency_ms) 변화 없음
- [ ] 분류 실패(Gemini 타임아웃 등) 시 `/chat` 응답 정상 반환 (논블로킹)
- [ ] `python3 -m pytest tests/ -v` 전체 PASS (PR-2 6건 + PR-3 11건 = 17건)

---

## PR 간 의존성

```
PR-1 (DB 마이그레이션)
  │
  ▼
PR-2 (anonymize_id + log_query)
  │
  ▼
PR-3 (intent_classifier + /chat 연결)
```

**반드시 순차 머지.** PR-2는 PR-1의 `query_logs` 테이블에 의존하고, PR-3는 PR-2의 `_log_query()` + `anonymize_id()`에 의존한다.

---

## 범위 밖 (이 PR 계획에서 제외)

| 항목 | 사유 | 대상 PR |
|------|------|---------|
| `/chat/stream` 분류 연결 | PR-3 안정화 후 | 별도 PR (TODO-10) |
| `/search` 분류 연결 | PR-3 안정화 후 | 별도 PR (TODO-11) |
| `generate_demand_signals()` RPC | Phase 2 범위 | 별도 PR (TODO-03) |
| followup 감지 로직 | Phase 2 범위 | 별도 PR (TODO-12) |
| intent-aware 검색 라우팅 | Phase 3 범위 | 별도 PR (TODO-14) |
| 신규 B2B 엔드포인트 | **금지** | N/A |
| CLAUDE.md 수정 | **금지** | N/A |
