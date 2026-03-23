# La Paz 계열 Codemap
> 최종 갱신: 2026-03-23

## 프로젝트 관계도

```
la-paz (메인 플랫폼)          lapaz-crawl (데이터 수집)         lapaz-live (실시간 Q&A)
━━━━━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━━━━━━━
B2C2C 축구 AI 플랫폼           선수 프로필 크롤러               경기 당일 팬 Q&A 대시보드
5대 리그 전체 커버              MUN/AVL 선수 나무위키 크롤링     맨유 vs 빌라 특화
Supabase + Edge Functions      Supabase documents 테이블에 저장  Fly.io + Vercel 배포

                    ┌─────────────────────┐
                    │   Supabase (공유)    │
                    │   - documents 테이블  │
                    │   - pgvector 임베딩   │
                    └──────┬──────┬────────┘
                           │      │
              크롤링 데이터 적재  │  하이브리드 검색 (RAG)
                           │      │
                    ┌──────┘      └──────┐
                    ▼                    ▼
              lapaz-crawl          lapaz-live (src/rag/)
              lapaz-live (scripts/)
```

- **la-paz**: 원본 풀스택 플랫폼. 5-Domain 에이전트 파이프라인 (Agent 1~5), Supabase Edge Functions, Next.js 프론트엔드, DeepSeek/Gemini LLM. 5대 리그 전체를 다루는 장기 비전.
- **lapaz-crawl-20260305170615**: 선수 프로필 크롤러. 나무위키/위키피디아에서 MUN/AVL 선수 데이터를 수집하여 Supabase `documents` 테이블에 저장. GitHub Actions `daily_crawl.yml`로 매일 자동 업데이트.
- **lapaz-live**: 경기 당일 실시간 팬 Q&A 서비스. la-paz의 RAG 코어를 추출/경량화한 파생 프로젝트. lapaz-crawl이 적재한 데이터 + 별도 크롤링 데이터를 Supabase에서 검색하여 Gemini Flash로 답변 생성.
- **lapaz-crawl과 lapaz-live의 src/ 구조가 거의 동일** (crawlers, processors, embeddings, rag, validators). lapaz-live가 crawl 코드를 복사한 뒤 RAG 파이프라인(pipeline.py, structured_context.py, exceptions.py, logging_utils.py)과 백엔드(backend/)를 추가한 형태.

---

## la-paz (메인)

### 아키텍처 개요
- **5-Domain Agent Pipeline**: Structure(1) -> Match+Perf(2) + Narrative(3) -> Document+Embed(4) -> API(5)
- **Backend**: FastAPI (Agent 5), DeepSeek V3.2 + Gemini via OpenAI SDK
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind + Zustand + Supabase Auth + Radix UI
- **DB**: Supabase (PostgreSQL + pgvector). 8 Structure 테이블 (competitions, seasons, teams, players, managers 등) + documents + fan_events + agent_status
- **Edge Functions**: chat, search, simulate-match, simulate-transfer, parse-rumors (Deno)
- **LLM**: Gemini 2.0 Flash (primary), DeepSeek V3.2 (fallback)
- **Embedding**: SentenceTransformer (all-MiniLM-L6-v2, 로컬)

### 디렉토리 맵
```
projects/la-paz/
├── agents/                    # 5-Domain 에이전트 파이프라인
│   ├── shared_config.py       # Supabase 클라이언트, IPC, 로깅, 환경변수 (핵심 공유 모듈)
│   ├── agent_1_structure.py   # 대회/팀/선수 구조 데이터 수집 (soccerdata)
│   ├── agent_2_match.py       # 경기/통계 수집 (statsbombpy, understatapi)
│   ├── agent_3_narrative.py   # 이적/부상/뉴스 수집 (Transfermarkt, RSS)
│   ├── agent_4_document.py    # 문서 생성 + 임베딩 (SentenceTransformer)
│   ├── agent_5_api.py         # FastAPI REST + RAG + B2B API 서버
│   ├── collectors/            # 데이터 소스별 수집기 (footballdata, statsbomb, understat)
│   ├── kleague_collectors.py  # K리그 데이터 수집
│   ├── pilot_match_prep.py    # 파일럿 경기 데이터 준비
│   ├── launch_all.sh          # 전체 에이전트 실행 스크립트
│   └── run_single.sh          # 단일 에이전트 실행
├── frontend/                  # Next.js 16 프론트엔드
│   ├── app/                   # App Router (auth, main 라우트 그룹)
│   │   ├── (auth)/            # 로그인/콜백
│   │   └── (main)/            # 홈, 채팅, 경기, 선수, 팀, 순위, 이적, 시뮬레이션
│   ├── components/            # chat, matches, simulate, standings, transfers, shared, ui
│   ├── lib/                   # hooks, supabase, types, utils
│   └── e2e/                   # Playwright E2E 테스트
├── supabase/
│   ├── schema.sql             # 전체 DB 스키마 (pgvector)
│   ├── migrations/            # RLS, 쿼리 로그, demand signals 등
│   └── functions/             # Edge Functions (chat, search, simulate 등)
├── scripts/
│   ├── daily_crawl.py         # 일간 크롤링 (football-data.org)
│   └── generate_transfer_rumors.py
├── data/                      # raw/ (StatsBomb 이벤트 등), processed/ (documents.json)
├── docs/                      # MVP spec, API contract, 보안 감사 등
├── evaluation/                # 평가 리포트
├── CLAUDE.md                  # 프로젝트 정체성 + 아키텍처 원칙
└── requirements.txt           # openai, soccerdata, statsbombpy, sentence-transformers 등
```

### 핵심 진입점
| 파일 | 역할 |
|------|------|
| `agents/agent_5_api.py` | FastAPI 서버 (B2C chat, matches, teams, players, search, predictions; B2B trends, fan-segments) |
| `agents/shared_config.py` | 전체 에이전트 공유 설정: Supabase 클라이언트, IPC (publish_status/wait_for_agent), 팬 이벤트 트래킹 |
| `agents/launch_all.sh` | 에이전트 1~5 순차/병렬 실행 |
| `supabase/schema.sql` | DB 스키마 정의 (competitions, seasons, teams, players, managers, matches, documents 등) |
| `frontend/app/(main)/page.tsx` | 프론트엔드 메인 페이지 |
| `scripts/daily_crawl.py` | GitHub Actions 매일 실행 |

---

## lapaz-live (실시간 Q&A)

### 아키텍처 개요
- **Backend**: FastAPI (Python 3.11), SQLite (질문 저장), Supabase (RAG 검색)
- **RAG Pipeline**: Classify (Gemini Flash Lite) -> Retrieve (Voyage AI 임베딩 + Supabase pgvector 하이브리드 검색) -> Generate (Gemini 2.5 Flash, fallback: 2.0 Flash Lite)
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind (la-paz보다 경량)
- **Data Sources**: football-data.org (순위/스쿼드/스코어), API-Football (라이브 이벤트)
- **배포**: Fly.io (백엔드, ams 리전, 512MB), Vercel (프론트엔드)
- **LLM**: Gemini 2.5 Flash (generator), Gemini Flash Lite (classifier). OpenAI/Anthropic 사용 안 함.
- **Embedding**: Voyage AI (검색용 쿼리 임베딩)

### 디렉토리 맵
```
projects/lapaz-live/
├── backend/                   # FastAPI 백엔드 (Fly.io 배포)
│   ├── main.py                # FastAPI 앱 엔트리포인트 (lifespan: DB 초기화 + 캐시 워밍업)
│   ├── config.py              # 환경변수, DB 경로, CORS, football-data.org/API-Football 설정
│   ├── models/schemas.py      # Pydantic 스키마 (AskRequest, AskResponse 등)
│   ├── routers/
│   │   ├── ask.py             # POST /api/ask (일반), POST /api/ask/stream (SSE 스트리밍)
│   │   ├── match.py           # GET /api/match/preview, /api/match/live
│   │   ├── questions.py       # GET /api/questions (질문 히스토리)
│   │   ├── errors.py          # GET /api/errors (에러 로그)
│   │   └── health.py          # GET /health/data-sources
│   ├── services/
│   │   ├── rag_service.py     # RAG 파이프라인 래퍼 (src/rag/pipeline.py 호출)
│   │   ├── question_service.py # SQLite 질문 CRUD
│   │   ├── live_service.py    # API-Football 라이브 이벤트
│   │   ├── match_service.py   # football-data.org 경기 데이터
│   │   ├── football_data_service.py # football-data.org API 클라이언트 (TTL 캐시)
│   │   └── error_log_service.py # 에러 로그 SQLite 저장
│   ├── data/questions.db      # SQLite DB (질문/답변 저장)
│   ├── migrations/            # 에러 로그 테이블
│   └── requirements.txt       # fastapi, google-genai, voyageai, supabase 등
├── src/                       # 크롤링 + RAG 코어 (lapaz-crawl과 구조 공유)
│   ├── config.py              # 크롤링 설정 (Supabase, 선수 목록, 크롤링 딜레이)
│   ├── crawlers/              # 나무위키 (v1, v2, deep, selenium), 위키피디아 fallback
│   ├── processors/            # play_style_enricher, profile_builder
│   ├── embeddings/indexer.py  # Supabase 임베딩 인덱서
│   ├── validators/            # data_checker, enrichment_checker
│   └── rag/                   # RAG 파이프라인
│       ├── pipeline.py        # 메인 파이프라인 (ask, ask_stream) — classify->retrieve->generate
│       ├── classifier.py      # Gemini Flash Lite 의도 분류 (7 카테고리)
│       ├── retriever.py       # 하이브리드 검색 (pgvector + ILIKE + RRF)
│       ├── generator.py       # Gemini 2.5 Flash 답변 생성 (스트리밍 지원)
│       ├── structured_context.py # 구조화 컨텍스트 빌더
│       ├── exceptions.py      # RateLimitError, PipelineTimeoutError 등
│       ├── logging_utils.py   # JSON 구조화 로깅
│       ├── prompts/           # system_prompt.txt, classifier_prompt.txt, few_shot_examples.json
│       └── data/player_names.json # 선수명 사전
├── frontend/                  # Next.js 프론트엔드 (Vercel 배포)
│   └── src/
│       ├── app/page.tsx       # 메인 페이지 (질문 입력 + 답변 + 경기 프리뷰)
│       ├── components/        # AnswerCard, MatchInfo, MatchPreview, QuestionInput/List, StatusBadge 등
│       ├── lib/api.ts         # 백엔드 API 클라이언트
│       └── types/index.ts     # TypeScript 타입
├── data/                      # 크롤링 원본 + 컨텍스트 (JSON, markdown)
│   ├── context/               # 팀/시즌/감독/라이벌리/규칙 JSON + 나무위키 markdown (30+ 문서)
│   ├── players_*.json         # MUN/AVL 선수 프로필
│   └── updates/               # 자동 업데이트 결과
├── scripts/                   # 크롤링/임베딩/검증 스크립트
│   ├── auto_update.py         # 자동 업데이트 (크롤링 + DB 교체 + 임베딩)
│   ├── crawl_all.py           # 전체 크롤링
│   ├── deep_crawl.py          # 딥 크롤링
│   └── generate_embeddings.py # 임베딩 생성
├── tests/                     # dryrun_test, test_generator, test_pipeline_degradation 등
├── api/index.py               # Vercel serverless 엔트리포인트 (backend/main.py import)
├── Dockerfile                 # Fly.io 배포용 (backend + src + data 복사)
├── fly.toml                   # Fly.io 설정 (lapaz-live, ams, 512MB, 1 vCPU)
└── requirements.txt           # 통합 의존성 (크롤링 + RAG + 백엔드)
```

### 핵심 진입점
| 파일 | 역할 |
|------|------|
| `backend/main.py` | FastAPI 앱 (uvicorn으로 실행). Fly.io/Docker 엔트리포인트 |
| `api/index.py` | Vercel serverless 엔트리포인트 (backend/main.py를 import) |
| `src/rag/pipeline.py` | RAG 핵심: `ask()` (일반), `ask_stream()` (SSE). classify -> retrieve -> generate |
| `backend/routers/ask.py` | POST `/api/ask` (질문 -> RAG -> 답변 + DB 저장) |
| `backend/config.py` | sys.path에 `src/` 추가하여 RAG 파이프라인 연결 |
| `scripts/auto_update.py` | 데이터 자동 업데이트 (cron/GitHub Actions) |
| `frontend/src/app/page.tsx` | 프론트엔드 메인 (질문 입력 + 실시간 답변) |

### RAG 파이프라인 흐름
```
사용자 질문
  → classifier.py (Gemini Flash Lite): 7개 카테고리 분류 + 키워드 추출
  → retriever.py: Voyage AI 임베딩 → Supabase pgvector 유사도 + ILIKE 키워드 → RRF 병합
  → structured_context.py: 검색 결과를 구조화된 프롬프트 컨텍스트로 변환
  → generator.py (Gemini 2.5 Flash): 한국어 3~4문장 답변 생성 (스트리밍 지원)
  → pipeline.py: 타임아웃 45초, 컨텍스트 품질 평가, 캐시, 에러 로깅
```

### 질문 분류 카테고리 (7개)
`player_info`, `tactical_intent`, `match_flow`, `player_form`, `fan_simulation`, `season_narrative`, `rules_judgment` + `out_of_scope`

---

## lapaz-crawl (데이터 수집)

### 아키텍처 개요
- **목적**: 맨체스터 유나이티드/아스톤 빌라 선수 프로필을 나무위키/위키피디아에서 크롤링하여 Supabase `documents` 테이블에 저장
- **크롤링 소스**: 나무위키 (1차, BeautifulSoup), 위키피디아 REST API (fallback)
- **임베딩 전략**: `deferred` (텍스트만 저장, 임베딩은 Voyage AI로 별도 배치 생성)
- **자동 업데이트**: `scripts/auto_update.py`로 시즌/팀/감독 페이지 매일 재크롤링 → Supabase 교체

### 디렉토리 맵
```
projects/lapaz-crawl-20260305170615/
├── src/
│   ├── config.py              # Supabase, 크롤링 설정, MUN/AVL 선수 목록 (한/영)
│   ├── crawlers/              # namuwiki (v1, v2, deep, selenium), wikipedia_fallback
│   ├── processors/            # play_style_enricher, profile_builder
│   ├── embeddings/indexer.py  # Supabase 임베딩 인덱서
│   ├── validators/            # data_checker, enrichment_checker
│   ├── rag/                   # classifier, generator, retriever, pipeline (lapaz-live보다 이전 버전)
│   └── api/server.py          # (미사용 또는 테스트용)
├── scripts/
│   ├── auto_update.py         # 자동 업데이트 메인 스크립트 (FRESH_SEEDS 7개 페이지)
│   ├── crawl_all.py           # 전체 크롤링
│   ├── deep_crawl.py          # 딥 크롤링
│   ├── generate_embeddings.py # Voyage AI 임베딩 생성
│   ├── index_to_supabase.py   # Supabase 인덱싱
│   └── verify_seeds.py        # 시드 URL 검증
├── data/
│   ├── context/               # 크롤링된 컨텍스트 (JSON + markdown, lapaz-live와 동일한 데이터)
│   ├── players_*.json         # MUN/AVL 선수 프로필
│   └── updates/               # 자동 업데이트 결과 (update_YYYYMMDD_HHMMSS.json)
├── output/                    # 크롤링 로그 + 결과 아카이브
├── logs/                      # auto_update.log
├── tests/                     # test_crawler, test_data_checker, test_indexer, test_processor
└── requirements.txt           # requests, beautifulsoup4, selenium, supabase, google-genai
```

### 핵심 진입점
| 파일 | 역할 |
|------|------|
| `scripts/auto_update.py` | 매일 실행되는 자동 업데이트 (7개 FRESH_SEEDS: 시즌/팀/감독 페이지) |
| `scripts/crawl_all.py` | 전체 선수 프로필 크롤링 |
| `src/config.py` | MUN 20명 + AVL 선수 목록, Supabase 설정 |
| `src/crawlers/namuwiki_deep_crawler.py` | 나무위키 딥 크롤러 (auto_update.py에서 사용) |

---

## 최근 변경 이력

```
87ee399 feat: Portfiq 출시 준비 — UI/UX 디자인 고도화 + 백엔드 버그 수정 + Admin 개선
a026b0d feat(lapaz-live): 듀얼 데이터 아키텍처 구축 (football-data.org + API-Football)
```

주요 미커밋 변경 (git status 기준):
- `lapaz-live`: backend/ 전면 수정 (config, main, schemas, routers/ask, routers/match, services/), src/rag/ 전면 수정 (classifier, generator, pipeline, retriever, structured_context, prompts), frontend/ 수정, Dockerfile/fly.toml 추가, 에러 로깅 시스템 추가
- `lapaz-crawl`: requirements.txt, src/api/server.py, src/processors/play_style_enricher.py, src/rag/ 수정, 자동 업데이트 데이터 다수 추가
- `la-paz-ci.yml`, `daily_crawl.yml` 워크플로우 수정

---

## 주의사항/Gotchas

1. **lapaz-crawl과 lapaz-live의 src/ 코드 중복**: 두 프로젝트의 `src/` 디렉토리가 거의 동일한 구조이지만 lapaz-live가 더 발전된 버전. 변경 시 양쪽 동기화 필요 여부 확인할 것.

2. **config.py 충돌**: lapaz-live에는 `backend/config.py`와 `src/config.py` 두 개가 존재. `api/index.py`에서 sys.path 순서로 우선순위 제어 (backend > src). `backend/config.py`가 `sys.path.insert(0, src/)`를 수행하여 RAG 모듈 접근.

3. **SQLite 다중 인스턴스 문제**: lapaz-live가 Fly.io에서 SQLite(`/tmp/questions.db`)를 사용하므로 스케일 아웃 시 질문 데이터가 인스턴스별로 분산됨. Supabase 마이그레이션 필요 (미완료).

4. **LLM 정책**: la-paz 원본은 DeepSeek + OpenAI SDK를 사용하지만, lapaz-live/crawl은 Gemini 전용으로 전환 완료 (`google-genai`). 팀 정책상 Anthropic/OpenAI 사용 금지.

5. **la-paz 원본의 데이터 수집 의존성**: `soccerdata`, `statsbombpy`, `understatapi` 등 축구 데이터 라이브러리에 의존. lapaz-live는 이들을 사용하지 않고 `football-data.org` REST API + 나무위키 크롤링으로 대체.

6. **Voyage AI 임베딩**: lapaz-live/crawl 모두 검색 쿼리 임베딩에 Voyage AI 사용 (`voyageai` 패키지). la-paz 원본은 SentenceTransformer (로컬) 사용. 임베딩 차원이 다를 수 있으므로 혼용 주의.

7. **GitHub Actions**: `daily_crawl.yml`은 `projects/la-paz` 경로에서 실행 (lapaz-crawl이 아님). `la-paz-ci.yml`은 la-paz 프론트엔드 린트/타입체크만 실행.

8. **Fly.io 배포**: lapaz-live 전용. `fly.toml`에서 `auto_stop_machines = false`, `min_machines_running = 1`로 상시 가동. 리전은 ams (암스테르담).
