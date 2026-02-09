# __PROJECT_NAME_TITLE__

> 자동 생성됨 - __DATE__
> 템플릿: fullstack

## 개요

__PROJECT_NAME__ 풀스택 웹 애플리케이션입니다.

## 기술 스택

### Backend
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Logging**: structlog
- **Language**: Python 3.11+

### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Build**: Vite
- **State**: Zustand
- **Style**: Tailwind CSS

## 시작하기

### 1. Backend 설정

```bash
cd backend
cp .env.example .env
# .env 파일을 열어 환경변수 설정

pip install -r requirements.txt
python main.py
```

### 2. Frontend 설정 (새 터미널)

```bash
cd frontend
cp .env.example .env

npm install
npm run dev
```

### 3. 접속

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Docker 실행

```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d
```

## 프로젝트 구조

```
__PROJECT_NAME__/
├── backend/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── core/
│   │   ├── config.py        # 환경변수 설정
│   │   ├── database.py      # Supabase 연결
│   │   └── logging.py       # structlog 설정
│   ├── routers/             # API 라우터
│   ├── schemas/             # Pydantic 스키마
│   ├── services/            # 비즈니스 로직
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # 메인 앱 컴포넌트
│   │   ├── api/             # API 클라이언트
│   │   ├── components/      # 재사용 컴포넌트
│   │   ├── pages/           # 페이지 컴포넌트
│   │   ├── hooks/           # 커스텀 훅
│   │   └── types/           # TypeScript 타입
│   ├── vite.config.ts       # Vite 설정
│   └── package.json
└── docker-compose.yml
```

## 환경변수

### Backend (.env)
| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| HOST | 서버 호스트 | 0.0.0.0 |
| PORT | 서버 포트 | 8000 |
| DEBUG | 디버그 모드 | true |
| SUPABASE_URL | Supabase 프로젝트 URL | - |
| SUPABASE_KEY | Supabase anon key | - |

### Frontend (.env)
| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| VITE_API_URL | API 서버 URL | http://localhost:8000 |

## 라이센스

Private
