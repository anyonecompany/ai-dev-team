# La Paz Live — 구조화 + 실시간 데이터 통합

> 3/12 Dryrun · 3/15 Pilot (Man Utd vs Aston Villa)

## 프로젝트 경로
- 프로젝트: `projects/lapaz-live/`
- 백엔드: `projects/lapaz-live/backend/`
- 프론트엔드: `projects/lapaz-live/frontend/`
- RAG 파이프라인: `projects/lapaz-live/src/rag/`

---

## 데이터 소스 (듀얼 아키텍처)

### 1. FotMob API — 정적 데이터 (인증 불필요)

| 엔드포인트 | 용도 | 캐시 TTL |
|-----------|------|---------|
| `GET https://www.fotmob.com/api/leagues?id=47` | EPL 순위표, 일정, 통계, 이적 | 10분 |
| `GET https://www.fotmob.com/api/teams?id=10260` | 맨유 스쿼드, 통계, 일정, 역사 | 30분 |
| `GET https://www.fotmob.com/api/teams?id=10252` | 아스톤빌라 스쿼드, 통계, 일정 | 30분 |

**주의**: `matchDetails` API는 403 차단 → 사용 불가

### 2. API-Football (api-sports.io) — 실시간 데이터

| 엔드포인트 | 용도 | 폴링 주기 |
|-----------|------|----------|
| `GET /fixtures?id={fixtureId}` | 라이브 스코어, 경기 상태 | 60초 |
| `GET /fixtures/events?fixture={id}` | 골, 카드, 교체 이벤트 | 60초 |
| `GET /fixtures/lineups?fixture={id}` | 선발 라인업 | 경기 시작 시 1회 |
| `GET /fixtures/statistics?fixture={id}` | 점유율, 슈팅, 패스 등 | 60초 |
| `GET /fixtures?league=39&season=2025&from=2026-03-15&to=2026-03-15` | 당일 EPL 경기 목록 | 경기 전 1회 |

**Base URL**: `https://v3.football.api-sports.io`
**인증**: `x-apisports-key: {API_FOOTBALL_KEY}` 헤더
**무료 티어**: 100 req/일 (60초 폴링 = 90분 경기 → 90회, 충분)
**업데이트 주기**: 15초마다 데이터 갱신 (API 측)
**환경변수**: `API_FOOTBALL_KEY` (.env에 저장)

### API-Football 팀/리그 ID
- EPL league id: `39` (season: `2025`)
- Man Utd: 팀 검색 필요 (`/teams?league=39&season=2025&search=Manchester United`)
- Aston Villa: 팀 검색 필요

### 주요 ID 매핑 (FotMob ↔ API-Football)
| 팀 | FotMob ID | API-Football ID |
|---|-----------|----------------|
| Man Utd | 10260 | (첫 호출 시 조회 후 config에 저장) |
| Aston Villa | 10252 | (첫 호출 시 조회 후 config에 저장) |
| 3/15 경기 | 4813671 | (당일 fixtures 조회) |

---

## 아키텍처

```
FotMob (정적)              API-Football (실시간)
순위표/스쿼드/통계          라이브 스코어/이벤트/라인업/통계
     ↘                        ↙
       Backend Cache Layer
  (정적: TTL 10-30분 / 라이브: TTL 30초)
            ↓
    ┌───────┴───────┐
    ↓               ↓
RAG Pipeline    REST API → Frontend
(structured      (SSE or polling)
 context 주입)
```

---

## 에이전트 팀 구성 (5인)

### 1. Data-Engineer (BE 영역)
**담당**: FotMob + API-Football 듀얼 서비스 + 캐시 레이어

**작업 내용**:

1. `backend/services/fotmob_service.py` 생성
   - `httpx.AsyncClient` 싱글턴으로 FotMob API 호출
   - 3개 함수: `get_epl_standings()`, `get_team_data(team_id)`, `get_match_preview(home_id, away_id)`
   - 인메모리 TTL 캐시 (순위: 10분, 팀: 30분)
   - 에러 시 빈 dict 반환 (RAG 답변 차단 금지)

2. `backend/services/live_service.py` 생성 — **실시간 데이터 핵심**
   - `httpx.AsyncClient` 싱글턴, `x-apisports-key` 헤더 인증
   - API 키: `os.getenv("API_FOOTBALL_KEY")`
   - 함수:
     ```python
     async def get_live_score(fixture_id: int) -> LiveScore | None
     async def get_match_events(fixture_id: int) -> list[MatchEvent]
     async def get_match_lineups(fixture_id: int) -> MatchLineups | None
     async def get_match_statistics(fixture_id: int) -> list[TeamStatistics]
     async def find_fixture(league_id: int, date: str, home: str, away: str) -> int | None
     ```
   - 인메모리 TTL 캐시 (라이브: 30초, 라인업: 5분)
   - API 키 없을 시 graceful degradation (None 반환, 로그 경고)
   - 무료 쿼터 보호: 요청 카운터 + 일일 100회 제한 로깅

3. `backend/models/schemas.py`에 모델 추가
   ```python
   # 정적 데이터 (FotMob)
   class StandingEntry(BaseModel):
       rank: int
       team_name: str
       team_id: int
       played: int
       wins: int
       draws: int
       losses: int
       goals_for: int
       goals_against: int
       goal_diff: int
       points: int
       form: list[str]  # ["W","W","D","L","W"]

   class PlayerInfo(BaseModel):
       name: str
       position: str
       country: str
       number: int | None = None

   class TeamStats(BaseModel):
       team_name: str
       team_id: int
       standings: StandingEntry | None = None
       squad: list[PlayerInfo] = []
       recent_form: list[str] = []
       top_scorers: list[dict] = []

   class MatchPreview(BaseModel):
       home: TeamStats
       away: TeamStats
       standings: list[StandingEntry] = []
       match_date: str
       match_id: int | None = None

   # 실시간 데이터 (API-Football)
   class LiveScore(BaseModel):
       fixture_id: int
       home_team: str
       away_team: str
       home_goals: int | None = None
       away_goals: int | None = None
       status: str  # "NS" | "1H" | "HT" | "2H" | "FT" | "ET" | "PEN"
       elapsed: int | None = None  # 경기 분
       venue: str | None = None

   class MatchEvent(BaseModel):
       time_elapsed: int
       time_extra: int | None = None
       team: str
       player: str
       assist: str | None = None
       event_type: str  # "Goal" | "Card" | "subst" | "Var"
       detail: str  # "Normal Goal" | "Yellow Card" | "Red Card" | "Substitution 1"

   class LineupPlayer(BaseModel):
       name: str
       number: int
       position: str
       grid: str | None = None  # "1:1", "2:1" etc

   class TeamLineup(BaseModel):
       team: str
       formation: str
       start_xi: list[LineupPlayer]
       substitutes: list[LineupPlayer]

   class MatchLineups(BaseModel):
       home: TeamLineup
       away: TeamLineup

   class TeamStatistics(BaseModel):
       team: str
       possession: str | None = None  # "55%"
       total_shots: int | None = None
       shots_on_target: int | None = None
       corners: int | None = None
       fouls: int | None = None
       offsides: int | None = None
       passes_total: int | None = None
       passes_accurate: int | None = None

   # 통합 라이브 상태
   class LiveMatchState(BaseModel):
       score: LiveScore | None = None
       events: list[MatchEvent] = []
       lineups: MatchLineups | None = None
       statistics: list[TeamStatistics] = []
       updated_at: str  # ISO timestamp
   ```

4. `backend/routers/match.py`에 엔드포인트 추가
   ```
   GET /api/match/preview            → MatchPreview (정적 데이터)
   GET /api/match/live-state         → LiveMatchState (실시간 통합)
   GET /api/match/events             → list[MatchEvent]
   GET /api/standings                → list[StandingEntry]
   GET /api/teams/{team_id}/stats    → TeamStats
   ```

5. `backend/config.py`에 상수 추가
   ```python
   API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
   API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
   FOTMOB_BASE = "https://www.fotmob.com/api"
   EPL_LEAGUE_ID = 39
   EPL_SEASON = 2025
   FOTMOB_EPL_ID = 47
   ```

**파일 소유권**: `backend/` 전체

---

### 2. RAG-Engineer (src/rag 영역)
**담당**: 정적 + 실시간 데이터를 RAG 컨텍스트에 주입

**작업 내용**:
1. `src/rag/structured_context.py` 생성
   - `build_structured_context(match_context)` 함수
   - 백엔드 `/api/match/preview` + `/api/match/live-state` 호출
   - 경기 전: 정적 데이터만 (순위, 스쿼드, 폼)
   - 경기 중: 정적 + 실시간 (스코어, 이벤트, 통계) 결합
   - 예시 출력 (경기 중):
     ```
     === 현재 스코어 ===
     Man Utd 2 - 1 Aston Villa (67')

     === 주요 이벤트 ===
     23' ⚽ Man Utd — Bruno Fernandes (Rashford 어시스트)
     41' ⚽ Aston Villa — Ollie Watkins
     55' ⚽ Man Utd — Rasmus Højlund

     === 경기 통계 ===
     점유율: Man Utd 58% - Aston Villa 42%
     슈팅: 12(5 유효) - 8(3 유효)

     === 현재 EPL 순위 ===
     3위: 맨체스터 유나이티드 (51pts, 최근 5경기: W-W-D-L-W)
     4위: 아스톤 빌라 (51pts, 최근 5경기: W-D-W-W-L)
     ```

2. `src/rag/pipeline.py` 수정
   - `ask()`, `ask_stream()`에서 generate 전 structured_context 빌드
   - `generate()` 호출 시 `structured_data` 파라미터 추가
   - 실시간 데이터는 캐시 키에 포함하지 않음 (30초마다 변동)

3. `src/rag/generator.py` 수정
   - 시스템 프롬프트에 structured_data 섹션 추가
   - 우선순위: 실시간 데이터 > 구조화 정적 데이터 > RAG 문서
   - "현재 스코어" 류 질문은 structured_data에서 즉답 유도

**파일 소유권**: `src/rag/` 전체

---

### 3. FE-Developer (frontend 영역)
**담당**: 대시보드 실시간 UI

**작업 내용**:

1. `frontend/src/lib/api.ts`에 API 함수 추가
   ```typescript
   export async function getMatchPreview(): Promise<MatchPreview> { ... }
   export async function getLiveMatchState(): Promise<LiveMatchState> { ... }
   export async function getMatchEvents(): Promise<MatchEvent[]> { ... }
   export async function getStandings(): Promise<StandingEntry[]> { ... }
   ```

2. `frontend/src/types/index.ts`에 타입 추가 (정적 + 실시간 전부)

3. 신규 컴포넌트:
   - `MatchPreview.tsx` — 양팀 순위/폼/스쿼드 비교 카드
   - `StandingsTable.tsx` — 상위 6팀 미니 순위표 (맨유/빌라 하이라이트)
   - `LiveScoreBoard.tsx` — **실시간 스코어보드** (경기 중 표시)
     - 스코어 + 경과 시간 + 상태 (1H/HT/2H/FT)
     - 경기 중일 때만 표시, upcoming이면 숨김
   - `MatchEvents.tsx` — **실시간 이벤트 타임라인**
     - 골(⚽)/카드(🟨🟥)/교체(🔄) 아이콘
     - 시간순 세로 타임라인
     - 새 이벤트 발생 시 하이라이트 애니메이션
   - `MatchStats.tsx` — **실시간 경기 통계 바**
     - 점유율, 슈팅, 코너 등 양팀 비교 바 차트
     - 수치 좌우 대칭 표시

4. `frontend/src/app/page.tsx` 수정
   - 경기 상태에 따른 조건부 렌더링:
     - **upcoming**: MatchPreview + StandingsTable
     - **live**: LiveScoreBoard + MatchEvents + MatchStats + QuestionInput
     - **finished**: LiveScoreBoard(최종) + MatchEvents + MatchStats
   - 폴링 주기:
     - 정적 데이터: 5분
     - 실시간 데이터: 60초 (경기 중만)

5. 기존 `MatchInfo.tsx` 수정
   - LiveScore 데이터가 있으면 실시간 스코어 표시
   - 없으면 기존 vs 표시 유지

**디자인 규칙** (필수 준수):
- 다크 테마: bg #0A0A0A, surface #141414, border #2A2A2A
- 텍스트: primary #F5F5F5, secondary #A0A0A0, muted #6B6B6B
- 액센트: #00E5A0 (민트), 라이브: #EF4444 (레드)
- 폰트: heading=Bebas Neue, body=Outfit, stat=Work Sans
- 라운딩: rounded-[2px] (모든 곳)
- 카드: card-surface 클래스 (bg-[#141414] border border-[#2A2A2A] rounded-[2px])
- 골 이벤트: #00E5A0 하이라이트
- 카드 이벤트: Yellow #F59E0B, Red #EF4444
- 통계 바: home #00E5A0, away #3B82F6

**파일 소유권**: `frontend/` 전체

---

### 4. Infra-Engineer (설정/환경 영역)
**담당**: API-Football 키 설정 + 환경 구성

**작업 내용**:
1. `.env`에 `API_FOOTBALL_KEY` 추가 (사용자가 키 발급 후 입력)
2. `.env.example` 업데이트
3. `backend/config.py`에 API-Football 관련 상수 추가
4. API-Football 키 유효성 검증 스크립트 작성
   ```python
   # scripts/verify_api_football.py
   # API 키로 /status 호출 → 남은 쿼터 확인 → 결과 출력
   ```
5. FotMob + API-Football 통합 헬스체크 엔드포인트
   ```
   GET /api/health/data-sources → { fotmob: "ok", api_football: "ok"|"no_key"|"error" }
   ```

**파일 소유권**: 루트 설정 파일, `scripts/`

---

### 5. QA-DevOps (검증)
**담당**: 전체 통합 테스트

**작업 내용**:
1. 외부 API 연결 테스트
   - FotMob leagues/teams → 200 확인
   - API-Football /status → 키 유효성 + 남은 쿼터 확인

2. 백엔드 스모크 테스트
   - `GET /api/match/preview` → 200 + 데이터 확인
   - `GET /api/match/live-state` → 200 (경기 없으면 빈 상태)
   - `GET /api/standings` → 200 + 20팀 확인
   - `GET /api/health/data-sources` → 200
   - 기존 회귀: `/api/ask`, `/api/questions`, `/api/match/live`

3. 프론트엔드 빌드
   - `npm run build` → 에러 0
   - `npx tsc --noEmit` → 에러 0

4. 실시간 시뮬레이션 (선택)
   - mock 데이터로 LiveScoreBoard, MatchEvents 렌더링 확인

**파일 소유권**: `tests/`, QA 리포트

---

## 실행 순서

```
Phase 0: Infra-Engineer (API 키 설정, config)
  ↓
Phase 1 (병렬): Data-Engineer + RAG-Engineer
  ↓
Phase 2 (병렬): FE-Developer + QA-DevOps (백엔드 검증)
  ↓
Phase 3: QA-DevOps (전체 통합 검증)
```

## 규칙
- 각 에이전트는 자기 파일 소유권 내에서만 작업
- API 호출 시 에러 핸들링 필수 (timeout 10초, 재시도 1회)
- API-Football 키 없으면 graceful degradation (실시간 비활성, 정적만)
- 모든 새 함수에 type hints + docstring (Google 스타일)
- 환경변수 하드코딩 금지
- 작업 완료 후 Notion 보고 (project_name="La Paz Live")

## 사용자 액션 필요
1. API-Football 무료 가입: https://dashboard.api-football.com/register
2. 발급받은 API 키를 `.env`에 추가: `API_FOOTBALL_KEY=your_key_here`
