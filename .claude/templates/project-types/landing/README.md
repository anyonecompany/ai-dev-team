# __PROJECT_NAME_TITLE__

> 자동 생성됨 - __DATE__
> 템플릿: landing

## 개요

__PROJECT_NAME__ 랜딩 페이지 + 결제 통합 프로젝트입니다.

## 기술 스택

### Backend
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Payment**: Stripe (skeleton)
- **Language**: Python 3.11+

### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Build**: Vite
- **Style**: Tailwind CSS

## 시작하기

### 1. Backend 설정

```bash
cd backend
cp .env.example .env
# .env 파일을 열어 환경변수 설정 (STRIPE_SECRET_KEY 등)

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

- **Landing Page**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## 페이지 구성

- **Hero**: 메인 헤드라인 + CTA 버튼
- **Features**: 6개 기능 소개 카드
- **Pricing**: 3단계 가격표 (Starter, Pro, Enterprise)
- **CTA**: 하단 콜투액션

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 헬스 체크 |
| GET | /api/payment/plans | 가격 플랜 조회 |
| POST | /api/payment/create-checkout | 결제 세션 생성 |
| POST | /api/payment/webhook | Stripe 웹훅 |

## Stripe 연동

1. Stripe 대시보드에서 API 키 발급
2. `.env`에 설정:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```
3. `backend/routers/payment.py`의 TODO 주석 해제 및 구현

## 라이센스

Private
