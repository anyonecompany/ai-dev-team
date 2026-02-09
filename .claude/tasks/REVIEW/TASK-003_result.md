# TASK-003 결과

생성 시간: 2026-02-02T17:23:12.079750

---

# 시스템 아키텍처 설계 문서

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              클라이언트 계층                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │   Web App    │  │  Mobile App  │  │   API 연동   │                       │
│  │  (Frontend)  │  │   (Future)   │  │   (Third)    │                       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                       │
└─────────┼─────────────────┼─────────────────┼───────────────────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway 계층                                │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                         FastAPI Application                         │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │     │
│  │  │   Auth   │  │ Instagram│  │ Analytics│  │  Reco-   │           │     │
│  │  │  Router  │  │  Router  │  │  Router  │  │ mmend    │           │     │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Instagram API  │ │    Supabase     │ │  Background     │
│  (Graph API)    │ │   (PostgreSQL)  │ │  Workers        │
│                 │ │                 │ │                 │
│  - 미디어 조회  │ │  - Users        │ │  - 데이터 수집  │
│  - 인사이트    │ │  - Posts        │ │  - 분석 배치    │
│  - 계정 정보   │ │  - Analytics    │ │  - 추천 갱신    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 2. 폴더/파일 구조

```
instagram-analytics/
├── .claude/
│   ├── agents/                    # 에이전트 정의
│   ├── handoff/
│   │   └── current.md            # 현재 핸드오프 상태
│   ├── tasks/
│   │   ├── TODO.md
│   │   └── DONE/
│   └── context/
│       └── tech-debt.md
├── CLAUDE.md                      # 프로젝트 중앙 제어
├── .env.example                   # 환경변수 템플릿
├── .gitignore
├── README.md
│
├── app/                           # FastAPI 애플리케이션
│   ├── __init__.py
│   ├── main.py                   # 앱 진입점
│   ├── config.py                 # 설정 관리
│   │
│   ├── api/                      # API 라우터
│   │   ├── __init__.py
│   │   ├── deps.py               # 의존성 주입
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py           # 인증 엔드포인트
│   │       ├── instagram.py      # Instagram 연동
│   │       ├── analytics.py      # 분석 데이터
│   │       └── recommendations.py # 추천 API
│   │
│   ├── core/                     # 핵심 모듈
│   │   ├── __init__.py
│   │   ├── security.py           # 보안/JWT
│   │   └── exceptions.py         # 커스텀 예외
│   │
│   ├── services/                 # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── instagram_service.py  # Instagram API 래퍼
│   │   ├── analytics_service.py  # 분석 로직
│   │   └── recommendation_service.py # 추천 알고리즘
│   │
│   ├── models/                   # Pydantic 모델
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── analytics.py
│   │   └── recommendation.py
│   │
│   └── db/                       # 데이터베이스
│       ├── __init__.py
│       ├── supabase.py           # Supabase 클라이언트
│       └── repositories/         # 데이터 접근 계층
│           ├── __init__.py
│           ├── user_repo.py
│           ├── post_repo.py
│           └── analytics_repo.py
│
├── workers/                       # 백그라운드 작업
│   ├── __init__.py
│   ├── data_collector.py         # Instagram 데이터 수집
│   ├── analytics_processor.py    # 분석 배치 처리
│   └── scheduler.py              # 작업 스케줄러
│
├── tests/                         # 테스트
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_workers/
│
└── requirements.txt
```

---

## 3. API 명세

### 3.1 인증 (Auth)

| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/api/v1/auth/instagram/connect` | POST | Instagram OAuth 시작 | `{ redirect_uri: string }` | `{ auth_url: string }` |
| `/api/v1/auth/instagram/callback` | GET | OAuth 콜백 처리 | `code: string, state: string` | `{ access_token, user }` |
| `/api/v1/auth/refresh` | POST | 토큰 갱신 | `{ refresh_token }` | `{ access_token }` |
| `/api/v1/auth/me` | GET | 현재 사용자 정보 | - | `User` |

### 3.2 Instagram 데이터

| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/api/v1/instagram/account` | GET | 계정 정보 조회 | - | `InstagramAccount` |
| `/api/v1/instagram/media` | GET | 미디어 목록 | `?limit=25&cursor=` | `{ data: Media[], next_cursor }` |
| `/api/v1/instagram/media/{id}` | GET | 미디어 상세 | - | `MediaDetail` |
| `/api/v1/instagram/media/{id}/insights` | GET | 미디어 인사이트 | - | `MediaInsights` |
| `/api/v1/instagram/sync` | POST | 수동 데이터 동기화 | - | `{ status, synced_count }` |

### 3.3 분석 (Analytics)

| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/api/v1/analytics/overview` | GET | 대시보드 개요 | `?period=7d` | `OverviewStats` |
| `/api/v1/analytics/engagement` | GET | 인게이지먼트 분석 | `?from=&to=` | `EngagementData` |
| `/api/v1/analytics/audience` | GET | 오디언스 분석 | - | `AudienceData` |
| `/api/v1/analytics/content` | GET | 콘텐츠 성과 분석 | `?sort_by=engagement` | `ContentAnalysis[]` |
| `/api/v1/analytics/trends` | GET | 트렌드 분석 | `?period=30d` | `TrendData` |

### 3.4 추천 (Recommendations)

| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/api/v1/recommendations/posting-time` | GET | 최적 포스팅 시간 | - | `PostingTimeReco[]` |
| `/api/v1/recommendations/content` | GET | 콘텐츠 추천 | - | `ContentReco[]` |
| `/api/v1/recommendations/hashtags` | GET | 해시태그 추천 | `?content_type=` | `HashtagReco[]` |
| `/api/v1/recommendations/actions` | GET | 실행 가능한 액션 | - | `ActionItem[]` |

---

## 4. 데이터베이스 스키마

### 4.1 ERD 다이어그램

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │ instagram_      │       │     posts       │
├─────────────────┤       │ accounts        │       ├─────────────────┤
│ id (PK)         │       ├─────────────────┤       │ id (PK)         │
│ email           │───1:1─│ id (PK)         │───1:N─│ instagram_      │
│ created_at      │       │ user_id (FK)    │       │ account_id (FK) │
│ updated_at      │       │ ig_user_id      │       │ ig_media_id     │
└─────────────────┘       │ username        │       │ media_type      │
                          │ access_token    │       │ caption         │
                          │ token_expires   │       │ permalink       │
                          └─────────────────┘       │ timestamp       │
                                                    │ raw_data        │
                                                    └────────┬────────┘
                                                             │
                          ┌──────────────────────────────────┤
                          │                                  │
                          ▼                                  ▼
              ┌─────────────────┐              ┌─────────────────┐
              │ post_insights   │              │ post_analytics  │
              ├─────────────────┤              ├─────────────────┤
              │ id (PK)         │              │ id (PK)         │
              │ post_id (FK)    │              │ post_id (FK)    │
              │ likes           │              │ engagement_rate │
              │ comments        │              │ reach_rate      │
              │ shares          │              │ performance_    │
              │ saves           │              │ score           │
              │ reach           │              │ calculated_at   │
              │ impressions     │              └─────────────────┘
              │ collected_at    │
              └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│ recommendations │       │ sync_logs       │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ instagram_      │       │ instagram_      │
│ account_id (FK) │       │ account_id (FK) │
│ type            │       │ sync_type       │
│ content         │       │ status          │
│ priority        │       │ items_synced    │
│ is_dismissed    │       │ error_message   │
│ created_at      │       │ started_at      │
│ expires_at      │       │ completed_at    │
└─────────────────┘       └─────────────────┘
```

### 4.2 테이블 정의

```sql
-- 사용자 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Instagram 계정 연동
CREATE TABLE instagram_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ig_user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(30) NOT NULL,
    access_token TEXT NOT NULL,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    profile_picture_url TEXT,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    media_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 포스트 데이터
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instagram_account_id UUID NOT NULL REFERENCES instagram_accounts(id) ON DELETE CASCADE,
    ig_media_id VARCHAR(50) UNIQUE NOT NULL,
    media_type VARCHAR(20) NOT NULL, -- IMAGE, VIDEO, CAROUSEL_ALBUM
    media_url TEXT,
    thumbnail_url TEXT,
    caption TEXT,
    permalink TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_data JSONB, -- Instagram API 원본 응답 저장
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 포스트 인사이트 (시계열 데이터)
CREATE TABLE post_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT