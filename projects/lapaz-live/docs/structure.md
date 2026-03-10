# La Paz Live Q&A Dashboard - Project Structure

> Version: 1.0.0
> Date: 2026-03-06
> Author: Architect Agent

---

## 전체 구조

```
projects/lapaz-live/
├── docs/
│   ├── api-spec.md          # API 스펙 문서
│   ├── db-schema.sql        # DB 스키마
│   └── structure.md         # 이 문서
├── backend/
│   ├── main.py              # FastAPI 엔트리포인트, CORS, 라우터 등록
│   ├── config.py            # 환경변수 관리 (RAG 경로, DB 경로 등)
│   ├── requirements.txt     # Python 의존성
│   ├── routers/
│   │   ├── ask.py           # POST /api/ask - RAG 질문 처리
│   │   ├── questions.py     # GET /api/questions, PATCH /api/questions/{id}/status
│   │   └── match.py         # GET /api/match/live - 경기 정보
│   ├── services/
│   │   ├── rag_service.py   # RAG 파이프라인 래퍼 (기존 pipeline.py 호출)
│   │   ├── question_service.py  # questions 테이블 CRUD
│   │   └── match_service.py     # 경기 정보 관리 (환경변수 또는 JSON 기반)
│   └── models/
│       └── schemas.py       # Pydantic request/response 모델
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── postcss.config.mjs
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx       # 루트 레이아웃
    │   │   ├── page.tsx         # 메인 대시보드 페이지
    │   │   └── globals.css      # 글로벌 스타일 (Tailwind)
    │   ├── components/
    │   │   ├── QuestionInput.tsx  # 질문 입력 폼 (텍스트 입력 + 전송 버튼)
    │   │   ├── AnswerCard.tsx     # 답변 카드 (질문, 답변, 카테고리, 복사 버튼)
    │   │   ├── QuestionList.tsx   # 질문 목록 (상태 필터, 페이지네이션)
    │   │   ├── MatchInfo.tsx      # 경기 정보 헤더 (팀명, 시간, 상태)
    │   │   └── StatusBadge.tsx    # 상태 뱃지 (draft/published/archived)
    │   ├── lib/
    │   │   └── api.ts            # API 클라이언트 (fetch 래퍼)
    │   └── types/
    │       └── index.ts          # TypeScript 타입 정의
    └── public/
        └── (정적 에셋)
```

---

## 모듈 의존성

```
[Frontend]                    [Backend]                    [Existing RAG]
  page.tsx                      main.py
    ├─ QuestionInput ──POST──→  routers/ask.py
    │                             └─ services/rag_service.py ──→ pipeline.ask()
    │                                 └─ services/question_service.py (DB 저장)
    ├─ QuestionList ──GET───→  routers/questions.py
    │   └─ AnswerCard              └─ services/question_service.py
    │       └─ StatusBadge
    ├─ MatchInfo ─────GET───→  routers/match.py
    │                             └─ services/match_service.py
    └─ lib/api.ts (모든 API 호출 중앙 관리)
```

---

## 기술 선택

| 영역 | 선택 | 근거 |
|------|------|------|
| Backend | FastAPI | 비동기 지원, 자동 문서 생성, RAG 파이프라인과 동일 Python 환경 |
| DB | SQLite (aiosqlite) | MVP 단계 단순성, 별도 서버 불필요, 추후 PostgreSQL 전환 용이 |
| Frontend | Next.js 14 (App Router) | React 기반, SSR 가능, 빠른 개발 |
| Styling | Tailwind CSS | 유틸리티 퍼스트, 빠른 UI 구성 |
| State | React hooks (useState, useEffect) | MVP 규모에 충분, 추가 상태관리 라이브러리 불필요 |

---

## RAG 파이프라인 연동

기존 `projects/lapaz-live/src/rag/pipeline.py`를 `sys.path`에 추가하여 직접 import.

```python
# backend/services/rag_service.py 개요
import sys
sys.path.insert(0, "../../lapaz-live/src")
from rag.pipeline import ask

async def generate_answer(question: str, match_context: dict | None) -> dict:
    result = await ask(question, match_context)
    return result
```

---

## 파일 소유권

| 에이전트 | 담당 |
|---------|------|
| BE-Developer | `backend/` 전체 |
| FE-Developer | `frontend/` 전체 |
| Architect | `docs/` 전체, 루트 설정 |
| QA-DevOps | 테스트, 린트, 빌드 검증 |
