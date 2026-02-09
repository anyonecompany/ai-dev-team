# TASK-021 결과

생성 시간: 2026-02-02T17:33:44.579108

---

# BE-Developer 시작

## 현재 상황 확인

먼저 필수 문서들을 확인하겠습니다.

### 1. 핸드오프 문서 확인
`.claude/handoff/current.md` 파일을 확인해주세요.

### 2. TODO 태스크 확인  
`.claude/tasks/TODO.md` 파일을 확인해주세요.

### 3. 프로젝트 구조 확인
현재 프로젝트의 폴더 구조를 보여주세요. 특히:
- `requirements.txt` 또는 `pyproject.toml`
- `.env.example` 
- 기존 FastAPI 앱 구조
- Supabase 설정

## Instagram OAuth API 개발을 위한 사전 확인사항

Instagram Graph API 연동을 위해 다음 정보가 필요합니다:

1. **Instagram App 정보**
   - App ID
   - App Secret
   - Redirect URI
   
2. **Supabase 스키마**
   - 사용자 테이블 구조
   - OAuth 토큰 저장 테이블
   - Instagram 데이터 저장 테이블

3. **필요한 Python 패키지**
   - `httpx` (API 호출)
   - `python-jose` (JWT 토큰 처리)
   - `supabase-py` (데이터베이스)

현재 상황을 파악한 후, 다음과 같은 구조로 개발을 진행할 예정입니다:

```
app/
├── routers/
│   └── instagram.py          # Instagram OAuth & API 라우터
├── services/
│   ├── instagram_auth.py     # OAuth 인증 서비스
│   ├── instagram_api.py      # Instagram Graph API 클라이언트
│   └── rate_limiter.py       # 레이트 리미팅 처리
├── models/
│   └── instagram.py          # Pydantic 모델들
└── database/
    └── instagram_repository.py # DB 접근 레이어
```

위의 문서들을 공유해주시면 구체적인 구현을 시작하겠습니다.