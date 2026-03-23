# La Paz Live - Deployment Checklist

> Version: 1.0.0
> Date: 2026-03-14
> Topology: Backend on `fly.io`, Frontend on separate host

---

## 1. Backend

- `ANTHROPIC_API_KEY` 설정
- `VOYAGE_API_KEY` 설정
- `SUPABASE_URL` 설정
- `SUPABASE_SERVICE_KEY` 설정
- `FOOTBALL_DATA_TOKEN` 설정
- `LAPAZ_API_BASE_URL=https://<fly-backend-domain>`
- `CORS_ORIGINS=https://<frontend-domain>`
- 필요 시 `CORS_ORIGIN_REGEX=https://.*\.vercel\.app`
- `QUESTIONS_DB_PATH=/tmp/questions.db`
- `ENABLE_STARTUP_WARMUP=0`

## 2. Frontend

- `NEXT_PUBLIC_API_BASE_URL=https://<fly-backend-domain>`
- 프론트 빌드 후 첫 화면에서 `/api/match/live`가 정상 로드되는지 확인
- 질문 전송 후 `/api/ask/stream` 응답이 chunk 단위로 오는지 확인

## 3. Smoke Tests

- `GET https://<fly-backend-domain>/docs`
- `GET https://<fly-backend-domain>/api/match/live`
- `GET https://<fly-backend-domain>/api/health/data-sources`
- `POST https://<fly-backend-domain>/api/ask`
  - out-of-scope 질문 1개
  - 경기 관련 질문 1개

## 4. Failure Patterns

- `CORS error`
  - `CORS_ORIGINS` 또는 `CORS_ORIGIN_REGEX` 누락
- `답변 생성 중 오류`
  - `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` 확인
- `match/preview` 지연
  - `LAPAZ_API_BASE_URL` 오설정 또는 `FOOTBALL_DATA_TOKEN` 문제
- 프론트에서 `localhost:8000` 호출
  - `NEXT_PUBLIC_API_BASE_URL` 미설정

## 5. Pilot Ready Definition

- 프론트 첫 진입 시 경기 정보가 보인다
- 질문 입력 후 1회 이상 스트리밍 응답이 보인다
- 최신 답변이 History에 저장된다
- 운영자 브라우저에서 CORS 오류가 없다
