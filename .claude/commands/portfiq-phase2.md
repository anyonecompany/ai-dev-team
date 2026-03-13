# Portfiq(포트픽) — Phase 2 실제 데이터 연동

> Mock → 실제 데이터로 전환. Supabase DB + Claude API + 뉴스 수집 파이프라인 연동.
> Phase 1 코드 기반 위에 서비스 레이어만 교체하는 방식.

## 프로젝트 경로
- 모노레포: `projects/portfiq/`
- Flutter 앱: `projects/portfiq/apps/mobile/`
- FastAPI 백엔드: `projects/portfiq/backend/`
- 마이그레이션: `projects/portfiq/backend/migrations/001_initial_schema.sql`

## 환경변수 (.env 필요)
```
SUPABASE_URL=
SUPABASE_KEY=
ANTHROPIC_API_KEY=
```

---

## 에이전트 팀 구성 (4인)

### 1. DB-Engineer
**담당**: Supabase 연동 + DB 클라이언트 + ETF 마스터 데이터

**작업 내용**:

1. `backend/services/supabase_client.py` — Supabase 클라이언트 초기화
   - `supabase` 패키지 사용 (requirements.txt에 이미 있음)
   - `config.py`에서 SUPABASE_URL, SUPABASE_KEY 읽기
   - 싱글톤 클라이언트 + async 래퍼

2. `backend/services/etf_service.py` — Mock → Supabase 전환
   - `etf_master` 테이블에서 검색/조회
   - `device_etfs` 테이블에 등록/삭제
   - `devices` 테이블에 디바이스 등록 (upsert)
   - 인기 ETF: `device_etfs` 집계 쿼리

3. ETF 마스터 시드 데이터 생성
   - `backend/seeds/etf_master.json` — 인기 서학 ETF 30종
   - QQQ, VOO, SPY, SCHD, TQQQ, SOXL, JEPI, ARKK, TLT, GLD, XLE, VTI, IVV, SOXX, SMH, EEM, KWEB, VIG, DIVO, QYLD, VNQ, DIA, IWM, XLK, XLF, IBIT, BITO, MSTR, PLTR, NVDA
   - 각 ETF: ticker, name(한국어), category, expense_ratio, top_holdings(상위 10종목)
   - `backend/seeds/seed_etf_master.py` — 시드 데이터 Supabase 업로드 스크립트

4. `backend/services/analytics_service.py` — Mock → Supabase 전환
   - `events` 테이블에 배치 insert
   - `daily_metrics` 집계 쿼리

**파일 소유권**: `backend/services/supabase_client.py`, `backend/services/etf_service.py`, `backend/services/analytics_service.py`, `backend/seeds/`

---

### 2. AI-Engineer
**담당**: Claude API 연동 (브리핑 생성 + 영향도 분류 + 뉴스 번역)

**작업 내용**:

1. `backend/services/briefing_service.py` — Mock → Claude API 전환
   - `anthropic` 패키지 사용 (requirements.txt에 이미 있음)
   - 프롬프트: 사용자 ETF 포트폴리오 + 최신 뉴스 → 구조화된 브리핑
   - 모델: `claude-sonnet-4-5-20250929` (비용 효율)
   - 응답 파싱: JSON 모드로 BriefingResponse 구조 강제
   - Supabase `briefings` 테이블에 결과 저장
   - 토큰 사용량 기록 (prompt_tokens, completion_tokens)

2. `backend/services/impact_service.py` — Mock → Claude API 전환
   - 프롬프트: "이 뉴스가 {ETF 구성종목 Top 10}에 미치는 영향도는?" → High/Medium/Low
   - 배치 처리: 뉴스 10개씩 한 번에 분류 (API 비용 최적화)
   - 결과를 `news_impacts` 테이블에 저장
   - 한국어 impact_reason 생성

3. `backend/services/news_service.py` — 뉴스 번역 헤드라인 추가
   - Claude API로 영문 헤드라인 → 한국어 번역
   - 배치 처리: 헤드라인 10개씩

4. 프롬프트 관리
   - `backend/prompts/briefing.py` — 브리핑 생성 프롬프트
   - `backend/prompts/impact.py` — 영향도 분류 프롬프트
   - `backend/prompts/translate.py` — 번역 프롬프트

**파일 소유권**: `backend/services/briefing_service.py`, `backend/services/impact_service.py`, `backend/prompts/`

---

### 3. Data-Engineer
**담당**: 실시간 뉴스 수집 파이프라인 + 스케줄러

**작업 내용**:

1. `backend/services/news_service.py` — Mock → 실제 뉴스 수집 전환
   - Yahoo Finance RSS 파싱 (httpx + feedparser)
   - 15분 간격 갱신 (APScheduler)
   - 중복 제거: source_url 기준 upsert
   - Supabase `news` 테이블에 저장
   - `requirements.txt`에 `feedparser` 추가

2. `backend/jobs/briefing_scheduler.py` — 실제 스케줄러 구현
   - 아침 브리핑: 매일 08:35 KST (전날 밤 미장 마감 후)
   - 밤 체크포인트: 매일 22:00 KST (미장 개장 전)
   - 모든 등록 디바이스에 대해 배치 브리핑 생성
   - APScheduler CronTrigger 사용

3. `backend/jobs/aggregation.py` — daily_metrics 집계 실제 구현
   - 매일 자정 실행
   - events, devices, briefings 테이블에서 집계

4. `backend/jobs/news_collector.py` — 뉴스 수집 Job (신규)
   - APScheduler IntervalTrigger (15분)
   - Yahoo Finance RSS → 파싱 → 영향도 분류 → DB 저장

**파일 소유권**: `backend/services/news_service.py`, `backend/jobs/`

---

### 4. QA-DevOps
**담당**: 통합 검증

**작업 내용**:
1. Supabase 연결 테스트 (실제 DB)
2. ETF 시드 데이터 업로드 확인
3. Claude API 호출 테스트 (브리핑 1건 생성)
4. 뉴스 수집 1회 실행 + DB 저장 확인
5. Flutter → Backend API 연동 확인 (Chrome에서)
6. `flutter analyze` 에러 0
7. Backend import 검증

**파일 소유권**: `tests/`

---

## 실행 순서

```
Phase 1 (병렬): DB-Engineer + AI-Engineer + Data-Engineer
  ↓
Phase 2: QA-DevOps (통합 검증)
```

## 규칙
- Phase 1의 기존 코드 구조 유지, 서비스 내부만 교체
- 라우터/스키마 변경 최소화
- Mock 데이터는 fallback으로 유지 (DB 연결 실패 시)
- 환경변수 하드코딩 절대 금지
- 모든 함수에 type hints + docstring
- 작업 완료 후 Notion 보고 (project_name="Portfiq (포트픽)")
