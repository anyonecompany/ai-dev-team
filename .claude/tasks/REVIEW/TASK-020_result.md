# TASK-020 결과

생성 시간: 2026-02-02T17:33:31.997659

---

# 시스템 설계 문서

## 아키텍처 개요

### 시스템 구성도
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI        │────▶│   Supabase     │
│   (Client)      │     │   Backend        │     │   PostgreSQL    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         │                       ▼                         │
         │              ┌──────────────────┐              │
         └─────────────▶│ Instagram Graph  │              │
                       │      API         │               │
                       └──────────────────┘               │
                                │                          │
                                └──────────────────────────┘
```

### 주요 컴포넌트
1. **Frontend**: Instagram 로그인, 데이터 시각화, 인사이트 대시보드
2. **FastAPI Backend**: API 게이트웨이, 비즈니스 로직, 데이터 처리
3. **Supabase**: 사용자 인증, 데이터 저장, 실시간 동기화
4. **Instagram Graph API**: 인스타그램 데이터 수집

## API 명세

### 인증 관련
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| /auth/instagram/login | GET | Instagram OAuth 로그인 시작 | - | Redirect URL |
| /auth/instagram/callback | GET | OAuth 콜백 처리 | code, state | JWT Token |
| /auth/refresh | POST | 토큰 갱신 | refresh_token | new tokens |
| /auth/logout | POST | 로그아웃 | - | success |

### 사용자 프로필
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| /api/user/profile | GET | 사용자 프로필 조회 | - | UserProfile |
| /api/user/instagram-accounts | GET | 연동된 계정 목록 | - | List[Account] |
| /api/user/sync-status | GET | 동기화 상태 확인 | account_id | SyncStatus |

### 인사이트 데이터
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| /api/insights/overview | GET | 계정 전체 통계 | account_id, period | InsightOverview |
| /api/insights/posts | GET | 게시물 인사이트 | account_id, limit, offset | List[PostInsight] |
| /api/insights/stories | GET | 스토리 인사이트 | account_id, period | List[StoryInsight] |
| /api/insights/audience | GET | 오디언스 분석 | account_id | AudienceData |
| /api/insights/trends | GET | 트렌드 분석 | account_id, metric, period | TrendData |

### 데이터 동기화
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| /api/sync/start | POST | 수동 동기화 시작 | account_id | job_id |
| /api/sync/status/{job_id} | GET | 동기화 상태 조회 | - | JobStatus |
| /api/sync/history | GET | 동기화 이력 | account_id | List[SyncHistory] |

## DB 스키마

### users 테이블
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### instagram_accounts 테이블
```sql
CREATE TABLE instagram_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    instagram_user_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    account_type VARCHAR(50), -- 'BUSINESS', 'CREATOR'
    profile_picture_url TEXT,
    followers_count INTEGER,
    follows_count INTEGER,
    media_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### oauth_tokens 테이블
```sql
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    instagram_account_id UUID REFERENCES instagram_accounts(id),
    access_token TEXT NOT NULL,
    token_type VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE,
    refresh_token TEXT,
    scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### media_insights 테이블
```sql
CREATE TABLE media_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instagram_account_id UUID REFERENCES instagram_accounts(id),
    media_id VARCHAR(255) NOT NULL,
    media_type VARCHAR(50), -- 'IMAGE', 'VIDEO', 'CAROUSEL_ALBUM'
    caption TEXT,
    permalink TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    impressions INTEGER,
    reach INTEGER,
    engagement INTEGER,
    saved INTEGER,
    comments_count INTEGER,
    likes_count INTEGER,
    shares_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(instagram_account_id, media_id)
);
```

### audience_insights 테이블
```sql
CREATE TABLE audience_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instagram_account_id UUID REFERENCES instagram_accounts(id),
    date DATE NOT NULL,
    age_gender_distribution JSONB,
    top_locations_cities JSONB,
    top_locations_countries JSONB,
    follower_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(instagram_account_id, date)
);
```

### sync_jobs 테이블
```sql
CREATE TABLE sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instagram_account_id UUID REFERENCES instagram_accounts(id),
    job_type VARCHAR(50), -- 'FULL', 'INCREMENTAL'
    status VARCHAR(50), -- 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 데이터 파이프라인

### 동기화 플로우
1. **초기 동기화**
   - 사용자 OAuth 인증 완료
   - Instagram Business/Creator 계정 정보 수집
   - 최근 30일 데이터 수집

2. **정기 동기화**
   - 매일 자정 자동 실행 (Cron Job)
   - 증분 데이터만 수집
   - Rate Limit 관리

3. **실시간 업데이트**
   - Webhook 구독 (가능한 경우)
   - 수동 새로고침 옵션

## OAuth 토큰 관리

### 토큰 저장 구조
```python
class TokenManager:
    """
    OAuth 토큰 관리 클래스
    - 암호화된 토큰 저장
    - 자동 갱신 메커니즘
    - 만료 시간 추적
    """
    
    async def store_token(self, user_id: str, token_data: dict):
        # Supabase에 암호화하여 저장
        pass
    
    async def get_valid_token(self, user_id: str) -> str:
        # 유효한 토큰 반환, 필요시 갱신
        pass
    
    async def refresh_token(self, user_id: str):
        # 토큰 갱신 로직
        pass
```

### 보안 고려사항
1. **토큰 암호화**: AES-256 암호화 적용
2. **환경변수 관리**: 
   ```
   INSTAGRAM_APP_ID=xxx
   INSTAGRAM_APP_SECRET=xxx
   ENCRYPTION_KEY=xxx
   ```
3. **토큰 만료 처리**: 만료 1시간 전 자동 갱신
4. **Rate Limit 대응**: 429 에러 시 exponential backoff

## 폴더 구조
```
project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── insights.py
│   │   │   └── sync.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── instagram.py
│   │   │   └── insights.py
│   │   ├── services/
│   │   │   ├── instagram_api.py
│   │   │   ├── token_manager.py
│   │   │   └── data_processor.py
│   │   └── utils/
│   │       └── helpers.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── [프론트엔드 구조]
└── docker-compose.yml
```

## 기술적 위험 및 대응방안

### 1. Instagram API Rate Limit
- **위험**: 시간당 200 콜 제한
- **대응**: 
  - Request 큐잉 시스템 구현
  - 데이터 캐싱 전략
  - 우선순위 기반 요청 관리

### 2. 토큰 만료 및 갱신 실패
- **위험**: 사용자 재인증 필요
- **대응**:
  - 프로액티브 토큰 갱신
  - 사용자 알림 시스템
  - Fallback 메커니즘

### 3. 대용량 데이터 처리
- **위험**: 많은 팔로워 계정의 경우 데이터량 과다
- **대응**:
  - 페이지네이션 구현
  - 백그라운드 작업 큐
  - 데이터 집계 테이블

### 4. Instagram API 변경
- **위험**: API 버전 업데이트, 정책 변경
- **대응**:
  - API 버전 고정
  - 변경사항 모니터링
  - 추상화 레이어 구현

## CLAUDE.md 업데이트 필요 사항
- 기술 스택에 추가: Supabase Auth, Instagram Graph API v18.0
- 환경변수 목록 추가
- API 엔드포인트 규칙 정의