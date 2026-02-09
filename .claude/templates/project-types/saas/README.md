# __PROJECT_NAME_TITLE__

> 자동 생성됨 - __DATE__
> 템플릿: saas

## 개요

__PROJECT_NAME__ SaaS 풀스택 애플리케이션입니다.
인증, 구독 결제, 대시보드가 포함되어 있습니다.

## 기술 스택

### Backend
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth
- **Payment**: Stripe (skeleton)
- **Language**: Python 3.11+

### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Build**: Vite
- **State**: Zustand (+ persist)
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
npm install
npm run dev
```

### 3. 접속

- **Landing**: http://localhost:5173
- **Dashboard**: http://localhost:5173/dashboard (로그인 필요)
- **API Docs**: http://localhost:8000/docs

## 페이지 구성

### 공개 페이지
- `/` - 랜딩 페이지 (Hero, Features, Pricing, CTA)
- `/login` - 로그인
- `/register` - 회원가입

### 인증 필요 페이지
- `/dashboard` - 대시보드 (통계, 최근 활동)

## API 엔드포인트

### 인증
| Method | Path | 설명 |
|--------|------|------|
| POST | /api/auth/register | 회원가입 |
| POST | /api/auth/login | 로그인 |
| POST | /api/auth/refresh | 토큰 갱신 |
| POST | /api/auth/logout | 로그아웃 |
| GET | /api/auth/me | 현재 사용자 |

### 결제
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/payment/plans | 가격 플랜 조회 |
| POST | /api/payment/create-checkout | 결제 세션 생성 |
| POST | /api/payment/webhook | Stripe 웹훅 |

### 대시보드
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/dashboard/stats | 통계 조회 |
| GET | /api/dashboard/chart/users | 사용자 차트 |
| GET | /api/dashboard/chart/revenue | 매출 차트 |
| GET | /api/dashboard/recent-activity | 최근 활동 |

## 환경변수

### Backend (.env)
```env
# 서버
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Stripe (선택)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 다음 단계

1. Supabase에서 프로젝트 생성 및 환경변수 설정
2. `backend/routers/auth.py`에서 Supabase Auth 테스트
3. Stripe 계정 생성 및 `backend/routers/payment.py` 구현
4. `backend/routers/dashboard.py`에서 실제 데이터 조회 구현
5. 프론트엔드 UI 커스터마이징

## 라이센스

Private
