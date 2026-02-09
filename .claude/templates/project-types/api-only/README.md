# __PROJECT_NAME_TITLE__

> 자동 생성됨 - __DATE__
> 템플릿: api-only

## 개요

__PROJECT_NAME__ 백엔드 API 서버입니다.

## 기술 스택

- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Logging**: structlog
- **Language**: Python 3.11+

## 시작하기

### 1. 환경 설정

```bash
cd backend
cp .env.example .env
# .env 파일을 열어 환경변수 설정
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
python main.py
```

또는 직접 uvicorn 실행:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Docker 실행

```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d
```

## 프로젝트 구조

```
backend/
├── main.py              # FastAPI 앱 진입점
├── core/
│   ├── config.py        # 환경변수 설정
│   ├── database.py      # Supabase 연결
│   └── logging.py       # structlog 설정
├── routers/
│   └── health.py        # 헬스체크 엔드포인트
├── schemas/             # Pydantic 스키마
├── services/            # 비즈니스 로직
├── middleware/          # 미들웨어
└── requirements.txt     # Python 의존성
```

## 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| HOST | 서버 호스트 | 0.0.0.0 |
| PORT | 서버 포트 | 8000 |
| DEBUG | 디버그 모드 | true |
| SUPABASE_URL | Supabase 프로젝트 URL | - |
| SUPABASE_KEY | Supabase anon key | - |

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | / | 루트 (서버 정보) |
| GET | /health | 헬스 체크 |
| GET | /health/detailed | 상세 헬스 체크 |
| GET | /docs | Swagger UI |

## 라이센스

Private
