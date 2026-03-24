# 세션 핸드오프: AI 3줄요약 영문 노출 버그 수정

> 날짜: 2026-03-24
> 프로젝트: Portfiq
> 커밋: 549d6cd (anyonecompany/portfiq main)

## 완료된 작업

### 버그 1 — summary_3line 영문 fallback 제거
- `news_service.py` 4곳에서 `f"• {headline}"` (영문) → `""` (빈값)으로 교체
  - `:452` `_translate_batch()` fallback
  - `:523` Gemini 파싱 실패 fallback
  - `:856` `_classify_impacts()` fallback
  - `:1193-1195` Supabase 로드 fallback
- 번역 완료 후 Supabase `news` 테이블 업데이트 시 `raw_data`(summary_3line 포함)도 함께 갱신하도록 수정

### 버그 1 연장 — Flutter UI 영문 fallback 제거
- `news_card.dart`: summary3line 비어있으면 impactReason fallback 대신 Row 자체 숨김
- `feed_screen.dart`: impactReason else 블록 제거 (summary3line 없으면 표시 안 함)

### 버그 2 — ETF 필터링 연결 확인 (수정 불필요)
- `routers/feed.py:31`에서 이미 `get_signal_feed(device_id)` 호출 중
- 시그널 피드 없을 때만 `news_service` fallback

### Fly.io 배포 완료
- 버전 21, 이미지: `portfiq:deployment-01KMF96JCE6CDBF826PYHDBYQ3`
- 머신: `0800e2db640718` (nrt, started)

### Smoke Test 결과
- 번역 완료 후: headline 한글, summary_3line 한글 3줄 요약, sentiment 한글 — **영문 노출 0건**
- 번역 미완료 시: summary_3line 빈값("") — **영문 fallback 0건**

## 검증 결과
- `ruff check`: All checks passed
- `pytest -k "feed or briefing or news"`: 5 passed, 0 failed
- `flutter analyze`: No issues found
- Production smoke test: PASS

## 후속 확인 완료
1. **translated_summary** → Edge Function `translator.ts:174`에서 정상 저장 중
2. **user_signal_feeds** → `matcher.ts:216-225`에서 device_etfs 기반 정상 적재 중
3. **Fly.io** → 재배포 완료, started 상태

## 미해결 (P2)
- Supabase `news` 테이블 기존 영문 summary_3line 데이터 정리 (Notion 태스크 등록됨)

## Notion 보고
- 의사결정: 번역 미완료 시 빈값 유지 정책
- 기술 레퍼런스: 번역 미완료 상태 처리 패턴
- 후속 태스크: Supabase 기존 영문 summary_3line 데이터 정리

## knowledge 등록
- `mistakes/translation-fallback-english-exposure.md`
- `patterns/translation-pending-state-pattern.md`
