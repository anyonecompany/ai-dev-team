# Portfiq API 규칙

## URL 구조
```
/api/v1/{domain}/{action}
```

## 라우터 등록 패턴
```python
# backend/main.py
app.include_router(etf_router, prefix="/api/v1/etf", tags=["etf"])
```

새 라우터 추가 시:
1. `backend/routers/{domain}.py` 파일 생성
2. `main.py`에 `include_router()` 등록
3. 스키마는 `models/schemas.py`에 추가

## 인증
- 일반 API: 인증 없음 (device_id 기반)
- Admin API: JWT 인증 (`middleware/admin_auth.py`)
- Admin 허용 이메일: `config.py` ADMIN_ALLOWED_EMAILS

## 응답 패턴
- 성공: 200 (조회), 201 (생성), 202 (비동기 수신)
- 실패: HTTPException with 사용자 친화적 메시지
- 레이트 리미팅: SlowAPI (`middleware/rate_limit.py`)

## 기존 라우터 목록
| 라우터 | prefix | 주요 엔드포인트 수 |
|--------|--------|------------------|
| etf | /api/v1/etf | 12+ |
| etf_analysis | /api/v1/etf | 3 |
| holdings | /api/v1/holdings | 1 |
| feed | /api/v1/feed | 3 |
| briefing | /api/v1/briefing | 3 |
| analytics | /api/v1/analytics | 1 |
| devices | /api/v1/devices | 2 |
| calendar | /api/v1/calendar | 3 |
| admin | /api/v1/admin | 12+ (JWT 필수) |
