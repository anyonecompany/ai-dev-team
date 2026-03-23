# 기타 프로젝트 Codemap
> 최종 갱신: 2026-03-23

---

## adaptfitai
### 개요
축구 선수 적응도(Fit) 예측 플랫폼. StatsBomb/Transfermarkt/K리그/J리그 데이터를 수집하고, GNN 기반 전술 시너지 시뮬레이터와 시계열 성능 예측 모델로 외국인 선수의 리그 적응도를 스코어링한다. FastAPI 백엔드 + Next.js 대시보드.

### 디렉토리 맵
```
adaptfitai/
├── src/
│   ├── api/                    # FastAPI 서버
│   │   ├── main.py             # 앱 엔트리포인트
│   │   ├── routers/            # analysis, dashboard, health, players_v2, reports
│   │   ├── middleware.py       # API Key, 로깅 미들웨어
│   │   └── error_handlers.py
│   ├── adaptfit/               # 핵심 비즈니스 로직
│   │   ├── scoring/hsi/        # HSI (적응도) 스코어링
│   │   ├── features/           # 피처 엔지니어링
│   │   ├── core/               # 도메인 코어
│   │   ├── feedback/           # 피드백 루프
│   │   └── report/             # 리포트 생성
│   ├── ingestion/              # 데이터 수집 잡 (16+ 잡)
│   │   ├── statsbomb_job.py    # StatsBomb 이벤트 데이터
│   │   ├── transfermarkt_job.py
│   │   ├── kleague_job.py / jleague_stats_job.py
│   │   ├── weather_job.py / kma_climate_job.py
│   │   └── sns_sentiment_job.py / culture_job.py
│   ├── model/                  # ML 모델
│   │   ├── gnn/                # goalnet, graph_builder, tactical_simulator
│   │   └── temporal/           # axial_attention, performance_predictor
│   ├── processing/             # 데이터 처리 (검증, 추론, 환경 리스크)
│   ├── pipeline/               # 파이프라인 오케스트레이션
│   ├── core/                   # 공용 (storage, exceptions, base_job, data_validator)
│   ├── config/settings.py      # 설정
│   └── feature_store/          # 피처 레지스트리
├── dashboard/                  # Next.js 대시보드 (React)
│   ├── app/page.tsx            # 메인 페이지
│   └── components/             # RadarChart, PlayerTable, ComparisonTable 등 10개
├── scripts/                    # 유틸 스크립트 (크롤러, 리포트 생성, 분석)
├── tests/                      # 테스트 (20+ 파일)
├── claude_llm.py               # Gemini LLM 래퍼
└── pyproject.toml / requirements.txt
```

### 진입점
- **API 서버**: `src/api/main.py` (FastAPI)
- **대시보드**: `dashboard/app/page.tsx` (Next.js)
- **파이프라인**: `src/pipeline/`
- **소스 파일**: 144개 Python 파일

---

## foundloop-landing
### 개요
Foundloop 해커톤/프로그램 랜딩 페이지. Next.js 14 기반 정적 랜딩으로 Hero, 문제/솔루션, 일정, 심사 기준, FAQ, 지원 섹션으로 구성.

### 디렉토리 맵
```
foundloop-landing/
├── app/
│   ├── page.js                # 메인 랜딩 (15개 섹션 조합)
│   ├── layout.js
│   └── globals.css
├── components/                # 15개 섹션 컴포넌트
│   ├── Hero.js / Navbar.js / Footer.js
│   ├── ProblemSection.js / SolutionSection.js
│   ├── Schedule.js / JudgingCriteria.js
│   ├── FAQ.js / ApplySection.js
│   ├── SocialProof.js / ResultsSection.js
│   ├── PrizeAnchor.js / Countdown.js
│   └── TallyForm.js / CopyButton.js
├── lib/                       # 유틸리티
├── public/                    # 정적 에셋
└── package.json               # Next.js 14, React 18, Pretendard 폰트
```

### 진입점
- **메인 페이지**: `app/page.js`

---

## 서로연 (seroyeon) MVP Landing Page
### 개요
서로연 캠프(아동 체육 프로그램) 사전등록 MVP 랜딩 페이지. Next.js + TypeScript + Supabase. 폼 제출 → Supabase 저장 + Slack 알림. GA4/Meta Pixel 추적 포함.

### 디렉토리 맵
```
서로연-(seroyeon)-mvp-landing-page/
├── app/
│   ├── page.tsx               # 메인 랜딩 (12개 섹션 + 모달)
│   ├── layout.tsx
│   ├── api/register/route.ts  # POST /api/register → Supabase + Slack
│   ├── components/
│   │   ├── sections/          # 12개 (Hero, PainPoint, CampIntro, Pricing, FAQ 등)
│   │   ├── FormModal.tsx / SuccessModal.tsx
│   │   ├── FloatingCTA.tsx / FloatingChatButton.tsx
│   │   ├── CountDown.tsx / CountUp.tsx
│   │   └── UrgencyBar.tsx / Footer.tsx
│   └── lib/
│       ├── supabase.ts        # Supabase 클라이언트
│       ├── gtag.ts            # GA4
│       └── pixel.ts           # Meta Pixel
├── hooks/use-mobile.ts
├── supabase/migrations/       # 001_add_gender_birthdate.sql
└── package.json               # Next.js, Supabase, react-hook-form, zod
```

### 진입점
- **메인 페이지**: `app/page.tsx`
- **API**: `app/api/register/route.ts`

---

## tactical-gnn
### 개요
축구 전술 패턴 분류를 위한 GNN(Graph Neural Network) 연구 프로젝트. PyTorch Geometric 기반 GATv2Conv 모델로 14개 전술 클래스(빌드업, 세트피스, 수비 등) 분류. Jupyter 노트북 + Python 스크립트 기반 실험.

### 디렉토리 맵
```
tactical-gnn/
├── tactical_gnn_real_data_improved.py    # 메인 실행 스크립트 (GATv2Conv, 14 클래스)
├── 01_data_pipeline.ipynb                # 데이터 전처리 파이프라인
├── 02_gnn_model.ipynb                    # 모델 학습 노트북
├── tactical_gnn_colab.ipynb              # Colab 실행용
├── tactical_gnn_colab_try.ipynb
├── tactical_gnn_real_data.ipynb
├── tactical_gnn_real_v2.ipynb
└── patent_specification_v3.md            # 특허 명세서 (v3)
```

### 진입점
- **메인 스크립트**: `tactical_gnn_real_data_improved.py`
- **데이터 파이프라인**: `01_data_pipeline.ipynb`
- 의존성: PyTorch, torch_geometric, scipy, sklearn

---

## lapaz-dashboard-20260306130416
### 개요
La Paz Live Q&A 대시보드. FastAPI 백엔드(SQLite) + Next.js 프론트엔드. 축구 경기 중 팬 질문을 받아 RAG 기반 답변을 제공하고, 질문/답변 이력을 관리하는 대시보드.

### 디렉토리 맵
```
lapaz-dashboard-20260306130416/
├── backend/
│   ├── main.py                # FastAPI 엔트리 (ask, questions, match 라우터)
│   ├── config.py
│   ├── routers/
│   │   ├── ask.py             # POST /api/ask — RAG 질문
│   │   ├── questions.py       # 질문 이력 CRUD
│   │   └── match.py           # 경기 정보
│   ├── services/
│   │   ├── question_service.py
│   │   ├── rag_service.py
│   │   └── match_service.py
│   ├── models/schemas.py
│   ├── data/questions.db      # SQLite
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/page.tsx       # 메인 대시보드 UI
│       ├── components/        # AnswerCard, MatchInfo, QuestionInput, QuestionList, StatusBadge
│       ├── lib/api.ts         # 백엔드 API 호출
│       └── types/index.ts
└── docs/
```

### 진입점
- **백엔드**: `backend/main.py` (FastAPI)
- **프론트엔드**: `frontend/src/app/page.tsx` (Next.js)

---

## notion-reporter-20260306
### 개요
Notion API 기반 보고 자동화 도구 (integrations/notion의 원형 프로젝트). 에이전트 출력을 파싱하여 태스크/의사결정/기술레퍼런스/완료 보고를 Notion DB에 기록. Slack 웹훅 알림 포함.

### 디렉토리 맵
```
notion-reporter-20260306/
├── src/
│   ├── notion_client.py       # Notion API 래퍼 (rate limit, retry)
│   ├── config.py              # 환경변수 로드
│   ├── parsers/
│   │   └── agent_output_parser.py  # 에이전트 출력 파싱
│   └── reporters/
│       ├── task_reporter.py         # 태스크 상태 업데이트
│       ├── decision_reporter.py     # 의사결정 기록
│       ├── techref_reporter.py      # 기술 레퍼런스 기록
│       └── completion_reporter.py   # 통합 완료 보고 + Slack
├── scripts/
│   ├── report_task_done.py
│   ├── report_decision.py
│   ├── report_techref.py
│   ├── report_completion.py
│   └── setup_check.py        # 환경 점검
├── tests/test_reporters.py
└── requirements.txt
```

### 진입점
- **CLI**: `scripts/report_*.py`
- **라이브러리**: `src/reporters/completion_reporter.py`

---

## integrations (공용 연동)
### 개요
ai-dev-team 전체에서 사용하는 외부 서비스 연동 모듈. Notion DB 보고, Slack 웹훅 알림, Monday.com 보드 동기화, 공용 포맷팅 유틸을 제공한다.

### 디렉토리 맵
```
integrations/
├── notion/
│   ├── reporter.py            # 핵심 — 통합 보고 (report_task_done, report_decision, report_completion 등)
│   ├── client.py              # NotionClientWrapper (rate limit, retry)
│   └── config.py              # .env 로드 (NOTION_API_KEY, DB IDs, SLACK_WEBHOOK_URL)
├── slack/
│   └── slack_notifier.py      # 비동기 Slack 웹훅 (send_notification, notify_* 헬퍼)
├── monday/
│   └── monday_sync.py         # Monday.com GraphQL 보드 동기화 (프로젝트/QA/에이전트 그룹)
├── shared/
│   └── notification_format.py # QA 리포트 포맷팅 유틸 (format_qa_report)
└── test_integration.py        # 통합 테스트
```

### 주요 함수
- `integrations.notion.reporter`
  - `report_task_done(task_name, status, note)` — 태스크 상태 변경 + Slack
  - `add_task(task_name, priority, done_criteria, project_name)` — 새 태스크 생성
  - `report_decision(title, category, decision, rationale, alternatives, project_name)` — 의사결정 기록
  - `report_techref(title, category, tags, content, project_name)` — 기술 레퍼런스
  - `report_completion(task_name, status, summary, decisions, tech_refs, new_tasks, project_name)` — 통합 보고
  - `add_project(name, status, summary, icon)` — 프로젝트 등록
- `integrations.slack.slack_notifier`
  - `send_notification(channel, message, blocks)` — 비동기 Slack 전송
  - `notify_project_created / notify_task_updated / notify_qa_result / notify_error`
- `integrations.monday.monday_sync` — Monday.com GraphQL API (프로젝트/QA/에이전트 그룹)
- `integrations.shared.notification_format.format_qa_report(project_name, results)` — QA 결과 포맷

---

## design-system (디자인 시스템)
### 개요
La Paz와 Portfiq 프로젝트의 디자인 시스템 명세. 마크다운 기반으로 색상, 타이포그래피, 컴포넌트, 페이지별 레이아웃 규칙을 정의한다. 코드 없음 (문서 전용).

### 디렉토리 맵
```
design-system/
├── la-paz/
│   ├── MASTER.md              # 브랜드 DNA, 컬러, 타이포, 컴포넌트 규칙 (다크 테마, 각진 디자인)
│   ├── FE_HANDOFF.md          # 프론트엔드 핸드오프 문서
│   └── pages/                 # 페이지별 명세
│       ├── home.md / chat.md / matches.md
│       ├── standings.md / transfers.md
│       ├── profile.md / simulate.md
└── portfiq/
    ├── MASTER.md              # Flutter Dark Premium + Glassmorphism (Fintech Minimal)
    └── pages/                 # 페이지별 명세
        ├── briefing.md / feed.md
        ├── etf-detail.md / onboarding.md
        └── settings.md
```

### 참고
- La Paz: 블랙&화이트 기반 각진 디자인, 삼각형 모티프, 다크 테마
- Portfiq: 인디고 악센트(`#6366F1`), 다크 배경(`#0D0E14`), Flutter 전용

---

## seoul-safe-road
### 개요
빈 프로젝트. 디렉토리 구조만 생성됨 (backend/app에 `__init__.py` 빈 파일, routers/services/models/db 모두 빈 `__init__.py`만 존재). 코드 없음.

### 디렉토리 맵
```
seoul-safe-road/
├── apps/mobile/               # 빈 디렉토리
├── backend/
│   ├── app/
│   │   ├── __init__.py        # 빈 파일
│   │   ├── db/__init__.py     # 빈
│   │   ├── models/__init__.py # 빈
│   │   ├── routers/__init__.py# 빈
│   │   └── services/__init__.py# 빈
│   └── scripts/               # 빈 디렉토리
├── docs/                      # 빈 디렉토리
└── supabase/migrations/       # 빈 디렉토리
```

### 상태
스캐폴딩만 완료. 구현 코드 없음.
