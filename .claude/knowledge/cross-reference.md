# 프로젝트간 Cross-Reference

> 최종 갱신: 2026-03-23
> 분석 방법: 실제 코드/requirements/git log 기반. 추측 없음.

---

## 공유 패턴

### 캐시 전략

| 프로젝트 | 캐시 방식 | 구현체 | TTL | 특이사항 |
|----------|----------|--------|-----|---------|
| **portfiq** | In-memory TTLCache (thread-safe) | `cachetools.TTLCache` (`services/cache.py`) | 15분 기본, `cache_ttl.py`에 데이터별 분리 (장중 15분 ~ 메타 30일) | `clear_cache()` API 존재, thread lock 사용 |
| **lapaz-live** | In-memory OrderedDict + 수동 TTL | `_response_cache: OrderedDict` (`src/rag/pipeline.py`) | 응답 캐시 1분, 컨텍스트 캐시 2분 (`structured_context.py`) | 라이브 경기 대응으로 짧은 TTL, LRU 수동 구현 (max 100) |
| **la-paz** | Dict 기반 조회 캐시 | `team_cache`, `player_cache` (dict) (`agents/agent_3_narrative.py`) | 무한 (세션 내) | Supabase ID 조회 결과를 세션 내 캐싱 |
| **adaptfitai** | Dict 기반 banned-words 캐시 | `_BANNED_CACHE: dict[Path, set]` (`report/grounding_guard.py`) | 무한 (프로세스 내) | 금지어 파일 로드 결과 캐싱 |
| **foundloop-landing** | 없음 | - | - | 정적 랜딩 페이지, 캐시 불필요 |
| **seroyeon** | 없음 | - | - | 정적 랜딩 페이지, 캐시 불필요 |

**관찰**: portfiq의 `cachetools.TTLCache` + thread lock 패턴이 가장 성숙. lapaz-live는 OrderedDict으로 LRU를 수동 구현하고 있어 `cachetools` 통일이 가능.

---

### LLM API 사용 비교

| 프로젝트 | 주 LLM | 모델 | SDK | fallback | 정책 위반 |
|----------|--------|------|-----|----------|----------|
| **portfiq** | Gemini | 2.5 Flash Lite | `google-genai` | Flash -> Pro (Gemini 내) | 없음 |
| **lapaz-live** | Gemini | 2.5 Flash (생성), 2.5 Flash Lite (분류) | `google-genai` | `gemini-2.0-flash-lite` | ✅ 해결 (2026-03-23, requirements에서 제거) |
| **lapaz-crawl** | Gemini | 2.5 Flash (enricher, generator) | `google-genai` | 없음 | ✅ 해결 (2026-03-23, requirements에서 제거) |
| **la-paz** | Gemini | 2.0 Flash (via OpenAI SDK) | `openai` (Gemini OpenAI-compatible endpoint) | DeepSeek V3.2 | **openai 패키지 사용** (Gemini 호환 엔드포인트), **DeepSeek fallback** |
| **adaptfitai** | Claude CLI | sonnet/opus | `subprocess` (claude CLI) | opus fallback | **Claude CLI 직접 호출** (anthropic 패키지는 아님, 비공식 경로) |
| **lapaz-dashboard** | 없음 | - | - | - | ✅ FALSE POSITIVE (실제 anthropic 의존성 없음, 2026-03-23 확인) |
| **foundloop-landing** | 없음 | - | - | - | - |
| **seroyeon** | 없음 | - | - | - | - |

---

### 임베딩 전략

| 프로젝트 | 임베딩 모델 | SDK |
|----------|-----------|-----|
| **lapaz-live** | OpenAI text-embedding-3-small + Voyage-3 | `openai`, `voyageai` |
| **lapaz-crawl** | OpenAI text-embedding-3-small + Voyage-3 | `openai`, `voyageai` |
| **la-paz** | sentence-transformers (로컬) | `sentence-transformers` |
| **adaptfitai** | FAISS + sentence-transformers (문서에 기재) | `transformers`, `sentencepiece` |

---

### 인프라 패턴

| 프로젝트 | Backend Framework | DB | 배포 (BE) | 배포 (FE) | 컨테이너 |
|----------|------------------|-----|----------|----------|---------|
| **portfiq** | FastAPI | Supabase (PostgreSQL) | Fly.io (Railway.toml도 존재) | Vercel (admin) + Flutter 앱 | Docker (`docker-compose.yml`) |
| **lapaz-live** | FastAPI | Supabase + SQLite (aiosqlite) | Fly.io (`fly.toml` + `Dockerfile`) | Vercel (Next.js FE) | Docker |
| **lapaz-crawl** | FastAPI | Supabase | GitHub Actions (자동 크롤) | - | 없음 |
| **la-paz** | FastAPI | Supabase | - (로컬/미정) | - | 없음 |
| **adaptfitai** | FastAPI (optional) | DuckDB (로컬) | 없음 (배치 파이프라인) | Next.js 대시보드 (로컬) | Docker (`docker-compose.yml`: Postgres + MinIO) |
| **foundloop-landing** | 없음 | 없음 | - | Vercel (`vercel.json`, ICN1 리전) | 없음 |
| **seroyeon** | Next.js API Routes | Supabase | - | - (배포 미설정) | 없음 |

**공통**: 전 프로젝트 FastAPI 통일 (BE 있는 경우). Supabase가 5/7 프로젝트에서 사용됨.

---

## 공통 이슈 (git log 기반 반복 패턴)

### 1. 타임아웃 설정 반복 수정 (portfiq - 7회)
```
46f4cc9 fix: Portfiq 전체 진단 — API 타임아웃 수정 + Admin CORS 프록시 + Flutter 30초 타임아웃
aed4fc5 fix: Portfiq API 타임아웃 + Admin 무한 로딩 수정
f96fa3c fix: API 타임아웃 20초 확대 + 뉴스 수집 3분→10분 간격
2ca4848 fix: backendVerify 5초 타임아웃 + auth-guard localStorage 우선 체크
```
**원인**: Flutter/Admin/Backend 간 타임아웃 값이 일관되지 않음. `cache_ttl.py`처럼 타임아웃도 중앙 관리 필요.

### 2. CORS 설정 반복 수정 (portfiq - 5회+)
```
04e35a3 fix: remove credentials:include from adminFetch + add CORS regex for Vercel previews
c3f89d2 fix: 무한 렌더 루프 + CORS 장애 시 graceful 처리
697d52b fix: Google OAuth 무한 로딩 완전 해결 — 전용 콜백 페이지 분리
731432c fix: OAuth 콜백 무한 로딩 수정 — redirectTo를 /login으로 변경 + race condition 해결
```
**원인**: Vercel preview URL이 동적이라 CORS 화이트리스트가 반복 파손됨. credentials:include + CORS 조합 문제.

### 3. Event loop 블로킹 (portfiq - 3회)
```
19df3db fix: 뉴스 수집 Job을 별도 스레드+event loop에서 실행 — 서버 행 완전 해결
fe6dee1 fix: 백엔드 event loop 블로킹 해결 — 뉴스 수집 asyncio.to_thread 래핑
ccec84b fix: 백엔드 event loop 블로킹 해결 — 뉴스 수집 asyncio.to_thread 래핑
```
**원인**: APScheduler 백그라운드 Job이 메인 event loop을 블로킹. 해결 패턴: 별도 스레드+event loop.

### 4. 캐시 무효화 누락 (portfiq)
```
40c41cc fix: 뉴스 번역 후 피드 캐시 무효화 누락 수정
3453170 fix: 캐시 클리어 API + 야간 브리핑 정확성 개선
```

### 5. DB 컬럼명 불일치 (portfiq, lapaz 공통)
```
9a59533 fix: daily_metrics 컬럼명 불일치 수정 (metric_date → date)
```
**원인**: Supabase 테이블 스키마와 코드의 필드명이 다름. pydantic 모델과 DB 스키마의 동기화 부재.

---

## 재사용 가능 코드

### 1. `integrations/notion/reporter.py`
- **기능**: Notion DB 자동 보고 (태스크, 의사결정, 기술 레퍼런스, 프로젝트)
- **사용처**: ai-dev-team 전체 (모든 프로젝트 공통)
- **함수**: `report_task_done()`, `report_decision()`, `report_techref()`, `report_completion()`, `add_project()`, `add_task()`

### 2. `integrations/slack/slack_notifier.py`
- **기능**: Slack 웹훅 알림
- **사용처**: ai-dev-team 전체 + portfiq 백엔드 (`jobs/funnel_aggregation.py`, `jobs/aggregation.py`에서 직접 import)

### 3. `integrations/shared/notification_format.py`
- **기능**: 알림 포맷팅 유틸리티
- **사용처**: Notion/Slack 통합

### 4. `scripts/report.py`
- **기능**: CLI 기반 Notion 보고
- **사용처**: 전체 프로젝트 (CLI에서 사용)

### 5. `portfiq/backend/services/cache.py` (재사용 후보)
- **기능**: thread-safe TTLCache 래퍼 (get/set/clear/stats)
- **재사용 가능 대상**: lapaz-live (현재 OrderedDict 수동 LRU → cachetools 전환 가능)

### 6. `lapaz-live/src/rag/` + `lapaz-crawl/src/rag/` (코드 중복)
- `retriever.py`, `generator.py`, `classifier.py` 파일이 lapaz-live와 lapaz-crawl에 **거의 동일하게 복사**되어 있음
- 공통 RAG 라이브러리로 추출 가능

---

## 의존성 정리 필요 (정책 위반 사항)

> 정책: "모든 프로젝트의 AI API는 Google Gemini로 통일 — Anthropic/OpenAI 절대 금지"

### ~~CRITICAL (anthropic 패키지 직접 의존)~~ — 2026-03-23 FALSE POSITIVE 확인

| 프로젝트 | 상태 | 비고 |
|----------|------|------|
| **lapaz-dashboard** | ✅ 이슈 없음 | 실제 코드/requirements에 anthropic 의존성 없음. 초기 분석 오류. |

### HIGH (openai 패키지 잔존 — 임베딩용) — 2건 해결

| 프로젝트 | 파일 | 상태 | 비고 |
|----------|------|------|------|
| **lapaz-live** | `requirements.txt` | ✅ 해결 (2026-03-23) | openai 제거. 임베딩은 voyageai 사용. indexer.py는 조건부 import (openai 없어도 동작) |
| **lapaz-crawl** | `requirements.txt` | ✅ 해결 (2026-03-23) | openai 제거. 동일 구조. |
| **la-paz** | `requirements.txt` | ⚠️ 유지 | DeepSeek V3.2를 OpenAI SDK로 호출 — 의도적 사용. `google-genai` 직접 전환 검토 가능하나 현재 동작에 문제 없음 |

### MEDIUM (Claude CLI 직접 호출)

| 프로젝트 | 파일 | 내용 | 조치 |
|----------|------|------|------|
| **adaptfitai** | `src/utils/claude_llm.py` | Claude CLI를 subprocess로 호출 | Gemini API(`google-genai`)로 전환 필요. 현재 `pyproject.toml`에 LLM 관련 의존성 없음 |

### LOW (DeepSeek fallback)

| 프로젝트 | 파일 | 내용 | 조치 |
|----------|------|------|------|
| **la-paz** | `agents/agent_5_api.py` | DeepSeek V3.2를 OpenAI SDK 경유 fallback | Gemini 계열 fallback으로 전환 (Flash -> Pro) |

---

## 마이그레이션 로드맵

### Phase 1: 즉시 처리 (정책 위반 해소)

1. **lapaz-dashboard: `anthropic` -> `google-genai` 전환**
   - `backend/requirements.txt`에서 `anthropic>=0.42.0` 제거
   - `google-genai>=1.0.0` 추가
   - RAG generator 코드 Gemini API로 리라이트

2. **adaptfitai: Claude CLI -> Gemini API 전환**
   - `src/utils/claude_llm.py`를 `src/utils/gemini_llm.py`로 교체
   - `call_claude()` → `call_gemini()` 시그니처 유지
   - `pyproject.toml`에 `google-genai>=1.0.0` 추가
   - `expert_reasoning_job.py` 및 테스트 코드 업데이트

### Phase 2: 임베딩 통일 (openai 패키지 제거)

3. **lapaz-live + lapaz-crawl: OpenAI 임베딩 -> Gemini/Voyage 전환**
   - `src/embeddings/indexer.py`에서 `openai` import 제거
   - Gemini Embedding API 또는 Voyage 단일화
   - `requirements.txt`에서 `openai>=1.50.0` 제거

4. **la-paz: OpenAI SDK 경유 Gemini -> google-genai 직접 전환**
   - `agents/agent_5_api.py`에서 OpenAI SDK 제거
   - `google-genai` 직접 사용
   - DeepSeek fallback -> Gemini Flash Lite fallback
   - `requirements.txt`에서 `openai>=1.50.0` 제거, `google-genai>=1.0.0` 추가

### Phase 3: 코드 중복 해소

5. **lapaz-live / lapaz-crawl RAG 코드 통합**
   - `src/rag/` 디렉토리가 양쪽에 거의 동일하게 복사됨
   - 공통 `lapaz-rag` 패키지로 추출 또는 한쪽이 다른 쪽을 의존하도록 구조 변경

6. **캐시 유틸 통일**
   - portfiq의 `services/cache.py` 패턴을 lapaz-live에도 적용
   - lapaz-live의 OrderedDict 수동 LRU -> `cachetools.TTLCache` 전환

### Phase 4: 인프라 표준화

7. **타임아웃 중앙 관리 패턴 도입**
   - portfiq의 `cache_ttl.py` 패턴을 타임아웃에도 적용
   - `timeout_config.py` 같은 중앙 상수 파일 신설

8. **CORS 설정 템플릿화**
   - Vercel preview URL 정규식 패턴을 공통 설정으로 관리
   - portfiq에서 5회 반복 수정된 패턴을 다른 프로젝트에 선제 적용
