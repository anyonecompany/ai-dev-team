# La Paz — Phase 1~3 구현 TODO

> 기준 문서: `docs/fan_intelligence_architecture.md` Section 10 (Phase 1~3)
> 생성일: 2026-02-20
> 범위: Foundation → Aggregation → Internal Feedback & RAG Quality
> 제약: 신규 B2B 엔드포인트 금지. CLAUDE.md 수정 금지.

---

## TODO-01: query_logs + demand_signals 테이블 생성

- **목적:** 팬 쿼리를 구조화된 스키마로 저장하고, 수요 신호 집계 테이블을 준비한다.
- **변경 파일:** `supabase/migrations/004_query_logs.sql` (신규)
- **DB 변경:** Yes — `query_logs` 테이블 + 5개 인덱스, `demand_signals` 테이블 + 2개 인덱스 생성
- **테스트:** Supabase Dashboard 또는 `psql`에서 `INSERT INTO query_logs (anon_id, query_text, channel) VALUES ('test', 'test query', 'chat')` 성공 확인 + `SELECT * FROM query_logs` 반환 확인
- **완료 조건(DoD):** 두 테이블 모두 Supabase에 생성되고, 인덱스가 `pg_indexes`에서 확인된다.

---

## TODO-02: query_logs / demand_signals RLS 정책 생성

- **목적:** query_logs는 service_role만 접근, demand_signals는 k-anonymity(unique_users≥5) 필터를 적용한다.
- **변경 파일:** `supabase/migrations/004_query_logs.sql` (TODO-01과 동일 파일 하단에 추가)
- **DB 변경:** Yes — RLS enable + 3개 policy (`query_logs_service_only`, `demand_signals_b2b_read`, `demand_signals_k_anon`)
- **테스트:** anon role로 `SELECT * FROM query_logs` → 0행 반환 확인. `demand_signals`에 `unique_users=3` 행 INSERT 후 anon role SELECT → 0행 반환. `unique_users=5` 행은 반환됨 확인.
- **완료 조건(DoD):** anon/authenticated role이 query_logs에 접근 불가하고, demand_signals에서 k<5 행이 필터링된다.

---

## TODO-03: generate_demand_signals() RPC 생성

- **목적:** query_logs를 entity+intent별로 시간/일 단위 집계하여 demand_signals에 저장하는 서버사이드 함수를 만든다.
- **변경 파일:** `supabase/migrations/005_demand_signals_rpc.sql` (신규)
- **DB 변경:** Yes — PL/pgSQL 함수 `generate_demand_signals(target_date date)` 생성
- **테스트:** query_logs에 10건 이상 테스트 데이터 삽입 후 `SELECT generate_demand_signals(current_date)` 호출 → demand_signals에 집계 행 생성 확인. `intensity_score` 값이 `query_count * (1 + followup_rate) / unique_users`와 일치하는지 검증.
- **완료 조건(DoD):** RPC가 hourly + daily rollup을 모두 생성하고, 반환값(삽입 행 수)이 0보다 크다.

---

## TODO-04: anonymize_id() 함수 구현

- **목적:** user_id를 일일 salt 기반 SHA-256 해시로 익명화하는 함수를 shared_config에 추가한다.
- **변경 파일:** `agents/shared_config.py`
- **DB 변경:** 없음
- **테스트:** (1) 동일 user_id + 같은 날짜 → 동일 anon_id 반환. (2) 동일 user_id + 다른 날짜(salt 강제 교체) → 다른 anon_id 반환. (3) `None` 입력 → "anonymous" 기반 해시 반환. (4) 반환 길이 = 16자.
- **완료 조건(DoD):** `anonymize_id()`가 shared_config.py에 존재하고, 4개 단위 테스트 통과.

---

## TODO-05: classify_intent() — Gemini 구조화 출력

- **목적:** 사용자 쿼리의 intent/sub_intent/temporal_frame/entities를 Gemini Flash JSON 출력으로 분류한다.
- **변경 파일:** `agents/intent_classifier.py` (신규, ~80줄)
- **DB 변경:** 없음
- **테스트:** (1) `"손흥민 이번 시즌 골 수"` → `intent="stat_lookup"`, entities에 `"Heung-Min Son"` 포함. (2) `"음바페 이적 루머"` → `intent="transfer"`. (3) 잘못된 API key 시 예외 발생 확인 (fallback 위임용).
- **완료 조건(DoD):** `classify_intent(query, entities)` 호출 시 9개 intent 중 하나를 포함하는 dict 반환. GOOGLE_API_KEY 환경변수로 Gemini 호출 성공.

---

## TODO-06: rule-based fallback 분류기 구현

- **목적:** Gemini 호출 실패(타임아웃, rate limit) 시 키워드 매칭으로 intent를 결정하는 폴백을 제공한다.
- **변경 파일:** `agents/intent_classifier.py` (TODO-05와 동일 파일)
- **DB 변경:** 없음
- **테스트:** (1) `"살라 부상 복귀"` → `intent="injury"`. (2) `"다음 경기 일정"` → `intent="schedule"`. (3) 어떤 패턴에도 안 걸리는 쿼리 → `intent=None` 반환 (분류 불가 허용).
- **완료 조건(DoD):** `classify_intent_fallback(query)` 함수가 존재하고, 7개 패턴 카테고리에 대해 정확히 매칭.

---

## TODO-07: safe_classify() 통합 래퍼 구현

- **목적:** Gemini 분류 → 실패 시 rule-based fallback → 전부 실패 시 `{intent: None}`을 반환하는 단일 진입점을 만든다.
- **변경 파일:** `agents/intent_classifier.py` (TODO-05/06과 동일 파일)
- **DB 변경:** 없음
- **테스트:** (1) 정상 Gemini → Gemini 결과 반환. (2) GOOGLE_API_KEY를 빈값으로 → fallback 결과 반환. (3) 패턴 미매칭 쿼리 + Gemini 실패 → `{"intent": None, ...}` 반환 (에러 아님).
- **완료 조건(DoD):** `safe_classify()`가 어떤 상황에서도 예외를 던지지 않고 dict를 반환한다.

---

## TODO-08: log_query() 비동기 헬퍼 구현

- **목적:** 분류 결과 + 응답 메타데이터를 query_logs에 비동기/논블로킹으로 삽입하는 헬퍼를 만든다.
- **변경 파일:** `agents/agent_5_api.py` (기존 파일 수정, ~30줄 추가)
- **DB 변경:** 없음 (TODO-01에서 테이블 생성 완료 전제)
- **테스트:** (1) 정상 삽입 → query_logs에 행 생성. (2) Supabase 연결 실패 시 → 예외 무시, API 응답 정상 반환 (논블로킹 보장).
- **완료 조건(DoD):** `_log_query()` 함수가 agent_5_api.py에 존재하고, 호출 실패가 서비스 중단으로 이어지지 않는다.

---

## TODO-09: /chat 엔드포인트에 분류 + 로깅 연결

- **목적:** `/chat` 핸들러에서 `_retrieve()` 호출 전에 intent 분류를 실행하고, 응답 후 query_logs에 기록한다.
- **변경 파일:** `agents/agent_5_api.py` (기존 `chat()` 함수 수정, 약 723-757줄 영역)
- **DB 변경:** 없음
- **테스트:** `/chat`에 `{"message": "손흥민 골 수"}` POST → (1) 기존 응답이 정상 반환됨 (회귀 없음). (2) query_logs에 `intent="stat_lookup"` 행 1건 생성됨. (3) 분류 실패 시에도 채팅 응답은 정상.
- **완료 조건(DoD):** `/chat` 호출마다 query_logs에 1행이 기록되고, 기존 응답 형식/내용에 변화 없음.

---

## TODO-10: /chat/stream 엔드포인트에 분류 + 로깅 연결

- **목적:** `/chat/stream` 핸들러에서 동일하게 intent 분류 + query_logs 기록을 수행한다.
- **변경 파일:** `agents/agent_5_api.py` (기존 `chat_stream()` 함수 수정, 약 760-851줄 영역)
- **DB 변경:** 없음
- **테스트:** `/chat/stream`에 `{"message": "프리미어리그 순위"}` POST → (1) SSE 스트림 정상 수신. (2) query_logs에 행 생성됨. (3) `model_used`, `latency_ms`, `source_count` 필드가 채워짐.
- **완료 조건(DoD):** `/chat/stream` 호출마다 query_logs에 1행이 기록되고, SSE 스트림 동작에 변화 없음.

---

## TODO-11: /search 엔드포인트에 분류 + 로깅 연결

- **목적:** `/search` 핸들러에서 intent 분류 + query_logs 기록을 수행한다.
- **변경 파일:** `agents/agent_5_api.py` (기존 `search()` 함수 수정, 약 894-902줄 영역)
- **DB 변경:** 없음
- **테스트:** `/search?q=메시 vs 호날두` GET → (1) 검색 결과 정상 반환. (2) query_logs에 `channel="search"`, `intent="comparison"` 행 생성됨.
- **완료 조건(DoD):** `/search` 호출마다 query_logs에 1행이 기록되고, 기존 검색 동작에 변화 없음.

---

## TODO-12: followup 감지 로직 구현

- **목적:** 동일 세션 내에서 이전 쿼리와 비교하여 `is_followup` 및 `query_position`을 결정한다.
- **변경 파일:** `agents/agent_5_api.py` (~20줄 추가, `_log_query()` 내부 또는 별도 헬퍼)
- **DB 변경:** 없음
- **테스트:** (1) 같은 session_id로 2번 연속 호출 → 두 번째 행의 `query_position=2`, `is_followup` 판정. (2) 새 session_id → `query_position=1`, `is_followup=false`.
- **완료 조건(DoD):** query_logs에 `query_position`이 세션 내 순서대로 증가하고, 유사 쿼리 재질문 시 `is_followup=true`.

---

## TODO-13: daily_crawl.py에 demand signal 집계 추가

- **목적:** 일일 크롤링 완료 후 `generate_demand_signals()` RPC를 호출하여 전날 query_logs를 집계한다.
- **변경 파일:** `scripts/daily_crawl.py` (기존 `main()` 함수 끝에 ~10줄 추가)
- **DB 변경:** 없음 (TODO-03에서 RPC 생성 완료 전제)
- **테스트:** `python3 scripts/daily_crawl.py` 실행 → 로그에 `"demand signals 집계: N건"` 출력. demand_signals 테이블에 행 존재 확인 (query_logs가 비어 있으면 0건 허용).
- **완료 조건(DoD):** daily_crawl.py 실행 시 수집+문서 생성+demand 집계가 순차 수행된다.

---

## TODO-14: intent-aware 검색 라우팅 구현

- **목적:** `_retrieve()` 함수에서 intent에 따라 검색 전략을 분기한다 (예: `schedule` → matches 테이블 직접 쿼리, `injury` → articles 우선).
- **변경 파일:** `agents/agent_5_api.py` (기존 `_retrieve()` 함수 수정, 약 555-601줄 영역)
- **DB 변경:** 없음
- **테스트:** (1) `intent="schedule"` + `"맨유 다음 경기"` → 응답에 matches 테이블 데이터 포함. (2) `intent="injury"` + `"살라 부상"` → articles 테이블에서 injury 관련 문서 우선 반환. (3) `intent=None` → 기존 동작 유지 (벡터 검색 + 키워드).
- **완료 조건(DoD):** intent가 `schedule`/`injury`/`transfer` 중 하나일 때 해당 테이블 직접 쿼리가 벡터 검색보다 우선 적용된다.

---

## TODO-15: 주간 수요 리포트 스크립트 생성

- **목적:** demand_signals에서 지난 7일간 top entities, intent 분포, RAG gap(높은 followup_rate)을 요약하는 내부용 리포트를 생성한다.
- **변경 파일:** `scripts/weekly_demand_report.py` (신규, ~80줄)
- **DB 변경:** 없음
- **테스트:** `python3 scripts/weekly_demand_report.py` 실행 → `logs/weekly_demand_report_YYYY-MM-DD.txt` 파일 생성 확인. demand_signals가 비어 있으면 "데이터 부족" 메시지 출력.
- **완료 조건(DoD):** 스크립트가 에러 없이 실행되고, top-10 entity + top-5 RAG gap이 리포트에 포함된다.

---

## 의존성 그래프

```
TODO-01 (테이블) ──┬──→ TODO-02 (RLS)
                   ├──→ TODO-03 (RPC) ──→ TODO-13 (daily_crawl 연동)
                   └──→ TODO-08 (log_query)
                              │
TODO-04 (anonymize_id) ──────┤
                              │
TODO-05 (classify) ──┐       │
TODO-06 (fallback) ──┤       │
TODO-07 (safe_classify)──────┤
                              │
                   ┌──────────┘
                   ├──→ TODO-09 (/chat 연결)
                   ├──→ TODO-10 (/chat/stream 연결)
                   ├──→ TODO-11 (/search 연결)
                   └──→ TODO-12 (followup 감지)
                              │
                   ┌──────────┘
                   ├──→ TODO-14 (intent-aware 검색)
                   └──→ TODO-15 (주간 리포트)
```

## 구현 순서 (권장)

| 순서 | TODO | Phase | 선행 조건 |
|------|------|-------|----------|
| 1 | TODO-01 | Phase 1 | — |
| 2 | TODO-02 | Phase 1 | TODO-01 |
| 3 | TODO-04 | Phase 1 | — (병렬 가능) |
| 4 | TODO-05 | Phase 1 | — (병렬 가능) |
| 5 | TODO-06 | Phase 1 | — (병렬 가능) |
| 6 | TODO-07 | Phase 1 | TODO-05, 06 |
| 7 | TODO-08 | Phase 1 | TODO-01, 04, 07 |
| 8 | TODO-09 | Phase 1 | TODO-08 |
| 9 | TODO-10 | Phase 1 | TODO-08 |
| 10 | TODO-11 | Phase 1 | TODO-08 |
| 11 | TODO-12 | Phase 2 | TODO-09/10/11 |
| 12 | TODO-03 | Phase 2 | TODO-01 |
| 13 | TODO-13 | Phase 2 | TODO-03 |
| 14 | TODO-14 | Phase 3 | TODO-07 |
| 15 | TODO-15 | Phase 3 | TODO-03, 13 |

## 제약 사항

- **신규 B2B 엔드포인트 금지.** 기존 `/b2b/trends`, `/b2b/fan-segments`, `/b2b/entity-buzz`는 변경하지 않음.
- **CLAUDE.md 수정 금지.** 변경 필요 시 별도 제안 문서 작성.
- **신규 LLM 프로바이더 추가 금지.** 기존 Gemini 2.0 Flash + DeepSeek V3.2만 사용.
- **커스텀 ML 학습 금지.** 분류는 LLM 구조화 출력 + 규칙 기반 폴백만.
- **기존 API 응답 형식 변경 금지.** 분류/로깅은 부작용 없이 추가.
- **fan_events 테이블 삭제 금지.** 비쿼리 행동 신호(page_view, prediction)에 계속 사용.
