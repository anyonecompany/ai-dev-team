# 세션 핸드오프: Portfiq 통합 QA 전체 수정 완료

> 날짜: 2026-03-24 ~ 03-25
> 프로젝트: Portfiq
> 최종 커밋: c07c506 (anyonecompany/portfiq main)

## 전체 QA 판정: PASS (완전)

## 이번 세션 커밋 (5건)

| 커밋 | 내용 |
|------|------|
| `549d6cd` | AI 3줄요약 영문 노출 수정 (news_service.py 4곳 + news_card.dart + feed_screen.dart) |
| `a2bc9c2` | .gitignore — pg_cron_setup.sql 추가 |
| `fd2c432` | Edge Function translator 안정화 (MAX=3, 순차, 2초 딜레이, 429 skip) |
| `765a916` | 미등록 티커 가격 조회 404 반환 (etf.py) |
| `c07c506` | 통합 QA 이슈 4건 (ETF 가격, sector-concentration, Firebase hang, Reuters RSS) |

## QA 이슈 5건 전체 수정

| # | 심각도 | 이슈 | 수정 파일 | 커밋 |
|---|--------|------|----------|------|
| 1 | High | 미등록 ETF 가격 미표시 ($-) | my_etf_provider.dart:149-200 | c07c506 |
| 2 | Medium | sector-concentration 빈 배열 | etf_analysis_service.py | c07c506 |
| 3 | Medium | 미등록 티커 mock 가격 | etf.py:138-155 | 765a916 |
| 4 | Low | 웹 Firebase hang | main_local.dart:44-47, push_service.dart:22-24 | c07c506 |
| 5 | Low | Reuters RSS DNS 실패 | news_service.py:183 | c07c506 |

## 추가 수정 (QA 외)

| 작업 | 수정 파일 | 커밋 |
|------|----------|------|
| AI 요약 영문 노출 제거 | news_service.py, news_card.dart, feed_screen.dart | 549d6cd |
| Edge Function translator 안정화 | supabase/functions/news-pipeline/translator.ts | fd2c432 |
| .env SUPABASE_SERVICE_KEY 줄바꿈 수정 | .env | fd2c432 |

## 배포 상태

| 대상 | 상태 |
|------|------|
| Fly.io (portfiq.fly.dev) | v21, started, smoke test PASS |
| Supabase Edge Function (news-pipeline) | v4, ACTIVE |
| GitHub (anyonecompany/portfiq) | main up to date (c07c506) |

## 검증 결과

- `ruff check`: All passed
- `pytest`: 전체 통과
- `flutter analyze`: No issues found
- Production smoke test: 한글 3줄 요약 정상, 영문 노출 0건

## 미해결 (P2, Notion 태스크 등록됨)

1. Supabase 기존 영문 summary_3line 데이터 정리
2. pg_cron 등록 확인 (Dashboard 수동 실행 필요)
3. Gemini API 키 분리 (백엔드 vs Edge Function)

## 온보딩 현황 (탐색 결과)

- 4단계 플로우: ETF 선택 → 로딩 → 첫 피드 → 푸시 권한
- 기본 ETF: `kDefaultEtfs = ['QQQ', 'VOO', 'SCHD']` (constants.dart)
- 인기 ETF 6개 선택지: QQQ, VOO, SCHD, TQQQ, SOXL, JEPI

## knowledge 등록

- `mistakes/translation-fallback-english-exposure.md`
- `patterns/translation-pending-state-pattern.md`
