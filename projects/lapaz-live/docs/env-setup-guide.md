# Environment Variables Setup Guide

> La Paz 대시보드 프로젝트 환경변수 설정 가이드

## 1. 기존 .env 파일 위치

RAG 파이프라인이 참조하는 .env 파일:
```
projects/lapaz-live/.env
```

RAG 모듈 내부에서 `load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))` 로 로드하므로, 이 위치에 환경변수가 설정되어 있어야 한다.

## 2. 필수 환경변수

### AI / 검색 서비스

```bash
# Claude API (분류 + 답변 생성) - 필수
ANTHROPIC_API_KEY=sk-ant-...

# Voyage AI (벡터 임베딩) - 선택 (없으면 키워드 검색만 사용)
VOYAGE_API_KEY=pa-...

# Supabase (문서 저장소) - 필수
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

> 주의: RAG retriever.py에서 사용하는 키 이름은 `SUPABASE_SERVICE_KEY`이다 (`SUPABASE_KEY` 아님).

### 경기 정보 (선택, 기본값 있음)

```bash
# 홈팀 (기본: Man Utd)
MATCH_HOME_TEAM=Man Utd

# 원정팀 (기본: Aston Villa)
MATCH_AWAY_TEAM=Aston Villa

# 경기 날짜 YYYY-MM-DD (기본: 2026-03-15)
MATCH_DATE=2026-03-15

# 킥오프 시간 HH:MM KST (기본: 23:00)
MATCH_KICKOFF_TIME=23:00
```

### 배포용 API / CORS

백엔드를 `fly.io`, 프론트를 별도 도메인에 둘 경우 아래 값을 명시한다.

```bash
# 백엔드가 자기 자신을 호출할 때 사용할 공개 URL
LAPAZ_API_BASE_URL=https://your-backend.fly.dev

# 백엔드 CORS 허용 목록 (쉼표 구분)
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app,https://your-domain.com

# 프리뷰 도메인을 넓게 허용해야 하면 정규식 사용 가능
CORS_ORIGIN_REGEX=https://.*\.vercel\.app

# 질문 DB 경로 (serverless에서는 /tmp 권장)
QUESTIONS_DB_PATH=/tmp/questions.db
```

## 3. 대시보드 백엔드용 .env

대시보드 프로젝트 루트에 `.env` 파일을 생성하되, RAG 파이프라인은 별도 경로의 `.env`를 자체 로드한다:

```bash
# projects/lapaz-live/backend/.env

# 경기 정보 오버라이드
MATCH_HOME_TEAM=Man Utd
MATCH_AWAY_TEAM=Aston Villa
MATCH_DATE=2026-03-15
MATCH_KICKOFF_TIME=23:00
```

RAG 관련 키(ANTHROPIC, VOYAGE, SUPABASE)는 `lapaz-live/.env`에 이미 설정되어 있으므로 중복 설정 불필요.

배포 환경에서는 `.env` 대신 각 플랫폼의 환경변수 설정 UI를 사용한다.

### `fly.io` 백엔드 권장 값

```bash
ANTHROPIC_API_KEY=...
VOYAGE_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
FOOTBALL_DATA_TOKEN=...
API_FOOTBALL_KEY=...   # 선택
LAPAZ_API_BASE_URL=https://your-backend.fly.dev
CORS_ORIGINS=https://your-frontend.vercel.app,https://your-domain.com
QUESTIONS_DB_PATH=/tmp/questions.db
ENABLE_STARTUP_WARMUP=0
```

### 프론트엔드 권장 값

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend.fly.dev
```

## 4. 환경변수 검증

백엔드 시작 시 필수 환경변수 존재를 확인하는 로직 예시:

```python
import os

REQUIRED_RAG_ENVS = [
    "ANTHROPIC_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "LAPAZ_API_BASE_URL",
]

OPTIONAL_RAG_ENVS = [
    "VOYAGE_API_KEY",  # 없으면 키워드 검색만 사용
]

def validate_env() -> list[str]:
    """누락된 필수 환경변수 목록 반환. 빈 리스트면 OK."""
    missing = [key for key in REQUIRED_RAG_ENVS if not os.getenv(key)]
    if missing:
        print(f"[ERROR] 누락된 필수 환경변수: {missing}")

    for key in OPTIONAL_RAG_ENVS:
        if not os.getenv(key):
            print(f"[WARN] 선택 환경변수 미설정: {key}")

    return missing
```

## 5. .gitignore 확인

`.env` 파일이 커밋되지 않도록 반드시 `.gitignore`에 포함:

```
.env
.env.local
.env.*.local
```

## 6. 배포 직후 체크

1. 백엔드 헬스 확인: `GET /docs`, `GET /api/match/live`, `GET /api/health/data-sources`
2. 프론트에서 질문 전송 후 브라우저 네트워크 탭에 CORS 에러가 없는지 확인
3. `POST /api/ask`에 out-of-scope 질문 1개, 경기 질문 1개를 각각 보내 확인
4. 구조화 컨텍스트가 자기 자신을 올바른 도메인으로 호출하는지 확인
