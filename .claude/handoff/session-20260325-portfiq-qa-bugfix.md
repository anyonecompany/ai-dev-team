# 세션 핸드오프: Portfiq QA 이슈 수정 + 인프라 안정화

> 날짜: 2026-03-24 ~ 03-25
> 프로젝트: Portfiq
> 커밋: 549d6cd → a2bc9c2 → fd2c432 → 765a916

## 완료된 작업

### 1. AI 3줄요약 영문 노출 버그 수정 (549d6cd)
- `news_service.py` 4곳: summary_3line 영문 headline fallback → 빈값
- `news_card.dart`: impactReason fallback 대신 Row 숨김
- `feed_screen.dart`: impactReason else 블록 제거
- Supabase raw_data 업데이트 시 summary_3line 포함

### 2. .gitignore 업데이트 (a2bc9c2)
- `supabase/pg_cron_setup.sql` gitignore 추가

### 3. Edge Function translator 안정화 (fd2c432)
- MAX_ARTICLES 20→3, 배치→순차, 기사 간 2초 딜레이
- 429 재시도 제거 (즉시 skip)
- article_translations 이중 체크 추가
- `.env` SUPABASE_SERVICE_KEY 줄바꿈 버그 수정
- Supabase Edge Function v4 배포 완료

### 4. 존재하지 않는 티커 404 반환 (765a916)
- `etf.py:138-155`: is_mock=True + 유니버스 미등록 → 404
- QA Issue #1 (Medium) 해결

### 5. Fly.io 재배포 완료
- portfiq v21 (nrt, started)
- Smoke test PASS: 한글 3줄 요약 정상

## 검증 결과
- ruff check: All passed
- pytest: 전체 통과 (feed/briefing/news 5건, etf/price 4건)
- flutter analyze: No issues found
- Production smoke test: PASS

## 미해결 (P2, Notion 태스크 등록됨)
1. Supabase 기존 영문 summary_3line 데이터 정리
2. ETF sector-concentration API 빈 배열 수정
3. Reuters RSS DNS 실패 대응
4. pg_cron 등록 확인 (Dashboard에서 수동 실행 필요)
5. Gemini API 키 분리 (백엔드 vs Edge Function)

## Notion 보고
- 의사결정 2건: 번역 미완료 빈값 정책, mock 가격 반환 조건
- 기술 레퍼런스 1건: 번역 미완료 상태 처리 패턴
- 후속 태스크 3건: summary_3line 정리, sector-concentration, Reuters RSS

## knowledge 등록
- `mistakes/translation-fallback-english-exposure.md`
- `patterns/translation-pending-state-pattern.md`
