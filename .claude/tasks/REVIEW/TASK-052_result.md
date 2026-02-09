# TASK-052 결과

생성 시간: 2026-02-02T18:01:31.015158

---

## 시스템 아키텍처 설계 문서

---

### 아키텍처 개요

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   Instagram     │
│   (React)       │     │   (FastAPI)     │     │   Graph API     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Supabase      │
                        │   (PostgreSQL)  │
                        └─────────────────┘
```

#### 주요 컴포넌트
- **Frontend**: 사용자 인터페이스 및 데이터 시각화
- **Backend API**: 비즈니스 로직 및 IG API 연동
- **Supabase**: 데이터 저장 및 인증
- **Instagram Graph API**: 미디어 및 인사이트 데이터 소스

### API 명세

#### 인증 엔드포인트
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/auth/instagram` | GET | IG OAuth 리다이렉트 | - | Redirect URL |
| `/auth/callback` | GET | OAuth 콜백 처리 | code, state | `{access_token, user_id}` |
| `/auth/refresh` | POST | 토큰 갱신 | refresh_token | `{access_token}` |

#### 미디어 엔드포인트
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/media/sync` | POST | IG 미디어 동기화 | user_id | `{synced_count}` |
| `/media` | GET | 미디어 목록 조회 | page, limit | `{media[], total}` |
| `/media/{id}` | GET | 미디어 상세 조회 | - | Media Object |

#### 인사이트 엔드포인트
| 엔드포인트 | 메서드 | 설명 | 요청 | 응답 |
|-----------|--------|------|------|------|
| `/insights/media/{id}` | GET | 미디어 인사이트 | period | Insights Object |
| `/insights/account` | GET | 계정 인사이트 | period | Account Insights |
| `/insights/trending` | GET | 트렌딩 분석 | - | Trending Data |

### DB 스키마

```sql
-- 사용자 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instagram_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    profile_picture_url TEXT,
    access_token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 미디어 테이블
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    instagram_media_id VARCHAR(50) UNIQUE NOT NULL,
    media_type VARCHAR(20) NOT NULL, -- IMAGE, VIDEO, CAROUSEL_ALBUM
    media_url TEXT NOT NULL,
    thumbnail_url TEXT,
    caption TEXT,
    permalink TEXT,
    posted_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인사이트 테이블
CREATE TABLE insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    engagement INTEGER DEFAULT 0,
    saved INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(media_id, recorded_at)
);

-- 계정 인사이트 테이블
CREATE TABLE account_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    follower_count INTEGER,
    following_count INTEGER,
    media_count INTEGER,
    profile_views INTEGER,
    website_clicks INTEGER,
    recorded_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, recorded_at)
);

-- 인덱스
CREATE INDEX idx_media_user_id ON media(user_id);
CREATE INDEX idx_media_posted_at ON media(posted_at DESC);
CREATE INDEX idx_insights_media_id ON insights(media_id);
CREATE INDEX idx_insights_recorded_at ON insights(recorded_at DESC);
```

### 기술적 위험 및 대응방안

1. **IG API 레이트 리밋**
   - 위험: API 호출 제한 초과
   - 대응: Redis 기반 레이트 리미터 구현, 배치 처리

2. **토큰 만료 관리**
   - 위험: 만료된 토큰으로 인한 서비스 중단
   - 대응: 자동 토큰 갱신 스케줄러, 만료 알림

3. **대용량 데이터 동기화**
   - 위험: 타임아웃 및 메모리 부족
   - 대응: 페이지네이션, 백그라운드 작업 큐

4. **데이터 일관성**
   - 위험: IG와 로컬 DB 데이터 불일치
   - 대응: 정기 동기화, 트랜잭션 처리

### 폴더 구조
```
project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── media.py
│   │   │   └── insights.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── media.py
│   │   │   └── insights.py
│   │   ├── services/
│   │   │   ├── instagram.py
│   │   │   └── analytics.py
│   │   └── db/
│   │       └── supabase.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── [구조 별도 정의]
└── .claude/
    └── CLAUDE.md (업데이트 필요)
```

---

### CLAUDE.md 업데이트 필요 사항
- 기술 스택에 Redis 추가 (레이트 리미팅용)
- API 버전 관리 규칙 추가
- Instagram Graph API 버전 명시