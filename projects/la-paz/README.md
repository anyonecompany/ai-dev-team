# La Paz — B2C2C 축구 AI 서비스

> Smart Wrapper + RAG 아키텍처 | 5대 리그 데이터 파이프라인

## 아키텍처

```
Fan (B2C)                      B2B Client
   │                              │
   ▼                              ▼
┌──────────────────────────────────────┐
│         FastAPI (Agent 5)            │
│  /chat  /matches  /teams  /players   │
│  /search  /predictions  /b2b/*       │
└─────────────┬────────────────────────┘
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
Supabase   DeepSeek   SentenceTransformer
(pgvector)  V3.2       (all-MiniLM-L6-v2)
```

## 5-Domain 데이터 파이프라인

| Agent | 역할 | 소스 | 의존성 |
|-------|------|------|--------|
| 1. Structure | 대회/팀/선수 구조 데이터 | soccerdata (FBref, Transfermarkt) | - |
| 2. Match+Perf | 경기/통계 수집 | soccerdata, statsbombpy, understatapi | Agent 1 |
| 3. Narrative | 이적/부상/뉴스 수집 | soccerdata (Transfermarkt), RSS | Agent 1 |
| 4. Document | 문서 생성 + 임베딩 | SentenceTransformer | Agent 2, 3 |
| 5. API Server | REST + RAG + B2B | FastAPI + DeepSeek V3.2 | Agent 4 |

### 파이프라인 흐름

```
[1] Structure ──┬──→ [2] Match+Perf ──┬──→ [4] Document+Embed ──→ [5] API
                └──→ [3] Narrative  ──┘
```

## 5대 리그

- EPL (England Premier League)
- La Liga (Spain)
- Serie A (Italy)
- Bundesliga (Germany)
- Ligue 1 (France)

## 빠른 시작

```bash
# 1. 환경 설정
cp .env.example .env
# .env 에 Supabase, DeepSeek 키 입력

# 2. Supabase 스키마 적용
# Supabase Dashboard → SQL Editor → supabase/schema.sql 실행

# 3. 의존성 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. 전체 파이프라인 실행 (tmux 5분할)
bash agents/launch_all.sh

# 또는 개별 에이전트 실행
bash agents/run_single.sh 1
```

## tmux 레이아웃

```
┌──────────────────────┬──────────────────────┐
│ [1] Structure        │ [2] Match+Perf       │
├──────────────────────┼──────────────────────┤
│ [3] Narrative        │ [4] Document+Embed   │
├──────────────────────┴──────────────────────┤
│ [5] API Server                              │
└─────────────────────────────────────────────┘
```

## API 엔드포인트

### Fan (B2C)

| Method | Path | 설명 |
|--------|------|------|
| POST | /chat | RAG 채팅 (DeepSeek V3.2) |
| GET | /matches | 경기 목록 |
| GET | /teams | 팀 목록 |
| GET | /teams/{id} | 팀 상세 + 통계 |
| GET | /players/{id} | 선수 상세 + 통계 |
| GET | /search?q= | 시맨틱 검색 |
| POST | /predictions | 팬 경기 예측 |
| GET | /health | 서버 상태 |

### B2B (API Key 인증)

| Method | Path | 설명 |
|--------|------|------|
| GET | /b2b/trends | 트렌드 스냅샷 |
| GET | /b2b/fan-segments | 팬 세그먼트 |
| GET | /b2b/entity-buzz | 엔티티 버즈 랭킹 |

B2B 요청 시 `X-API-Key` 헤더에 API 키를 포함해야 합니다.

## DB 스키마 (31 tables)

| 도메인 | 테이블 수 | 테이블 |
|--------|----------|--------|
| Structure | 8 | competitions, seasons, teams, players, managers, team_seasons, player_contracts, manager_tenures |
| Match | 3 | matches, lineups, match_events |
| Performance | 4 | player_match_stats, player_season_stats, team_match_stats, team_season_stats |
| Narrative | 3 | transfers, injuries, articles |
| Tactics | 1 | formations |
| RAG | 1 | documents (+match_documents RPC) |
| Fan Engagement | 5 | users, chat_sessions, chat_messages, fan_events, fan_predictions |
| B2B | 4 | trend_snapshots, fan_segments, b2b_clients, b2b_api_logs (+generate_trend_snapshot RPC) |
| Pipeline | 2 | agent_status, pipeline_runs |

## 기술 스택

- **LLM**: DeepSeek V3.2 (primary), Gemini 2.0 Flash (fallback)
- **DB**: Supabase (PostgreSQL + pgvector + Auth + RLS)
- **Embedding**: all-MiniLM-L6-v2 (384차원)
- **API**: FastAPI + Uvicorn
- **데이터 소스**: soccerdata (FBref, Transfermarkt), StatsBomb, Understat, RSS

## 디렉토리 구조

```
la-paz/
├── agents/
│   ├── shared_config.py       공유 설정, Supabase 클라이언트
│   ├── agent_1_structure.py   Structure Collector
│   ├── agent_2_match.py       Match & Performance Collector
│   ├── agent_3_narrative.py   Narrative Collector
│   ├── agent_4_document.py    Document Generator & Embedder
│   ├── agent_5_api.py         FastAPI REST + RAG
│   ├── launch_all.sh          tmux 5분할 실행
│   └── run_single.sh          개별 에이전트 실행
├── supabase/
│   └── schema.sql             전체 DB 스키마 (31 tables + 2 RPC)
├── data/                      로컬 데이터 백업
├── ai/vectorstore/            ChromaDB 백업
├── evaluation/                평가 리포트
├── logs/                      에이전트 로그
├── requirements.txt
├── .env.example
└── README.md
```
