# 아키텍처 의사결정 기록 (ADR)

> 최종 갱신: 2026-03-23
> 출처: git log 200건 분석 기반

기존 기술 스택 선택(Python/FastAPI/Supabase/React/Vite 등)은 `tech-choices.md` 참조.
이 문서는 프로젝트 운영 중 발생한 아키텍처 수준 의사결정을 기록한다.

---

## ADR-001: Railway에서 Fly.io로 백엔드 인프라 마이그레이션
- **날짜**: 2026-03-12
- **커밋**: `aa3d254`
- **결정**: Portfiq 백엔드 배포를 Railway에서 Fly.io로 전환
- **이유**: Railway 무료 티어 크레딧 제한 ($5/월), Fly.io의 더 나은 컨테이너 관리 및 리전 선택
- **결과**: Fly.io 배포 안정화 완료. Flutter 앱 API URL도 Fly.io로 전환 (`e5dd6ca`)

## ADR-002: LLM API를 Anthropic/OpenAI에서 Google Gemini로 전면 전환
- **날짜**: 2026-03-11 ~ 2026-03-12
- **커밋**: `c66afe2`, `5799613`, `aa3d254`
- **결정**: 모든 프로젝트의 AI API를 Google Gemini (Flash/Pro)로 통일. Anthropic SDK 완전 제거
- **이유**: 비용 절감, API 통일로 관리 복잡도 감소. 비싼 모델 불필요 (Flash로 충분)
- **결과**: 뉴스 번역/요약, 브리핑 생성, 임팩트 분석, ETF 비교 모두 Gemini 전환 완료. `anthropic` 패키지 의존성 제거

## ADR-003: Admin 인증을 커스텀 로그인에서 Google OAuth + 이메일 화이트리스트로 전환
- **날짜**: 2026-03-11
- **커밋**: `0460006`
- **결정**: Portfiq Admin 대시보드 인증을 Supabase Google OAuth + 이메일 화이트리스트 방식으로 전환
- **이유**: 커스텀 인증은 보안 취약점 발생 가능성 높음. OAuth는 검증된 인증 흐름 제공
- **결과**: OAuth 콜백 무한 로딩 버그 연쇄 발생 (4건 fix 커밋). PKCE 처리, 전용 콜백 페이지 분리로 최종 안정화

## ADR-004: La Paz Live 듀얼 데이터 아키텍처 (football-data.org + API-Football)
- **날짜**: 2026-03-10
- **커밋**: `a026b0d`
- **결정**: 축구 데이터를 단일 소스 대신 football-data.org + API-Football 듀얼 소스로 구축
- **이유**: 단일 API의 데이터 누락/지연 리스크. 두 소스 교차 검증으로 정확도 향상
- **결과**: 듀얼 아키텍처 구축 완료. 실시간 경기 데이터 안정성 확보

## ADR-005: claude-forge 인프라 선별 도입 (rules, hooks, commands, skills)
- **날짜**: 2026-03-15
- **커밋**: `0f23c6e`
- **결정**: 오픈소스 claude-forge에서 규칙 6개, 훅 4개, 커맨드 8개, 스킬 3개를 선별 도입
- **이유**: 에이전트 작업의 안전성(파괴적 명령 차단), 일관성(코딩 스타일), 생산성(검증 자동화) 확보
- **결과**: deny 패턴으로 `git push --force`, `rm -rf /` 등 자동 차단. 보안 민감 파일 수정 시 리뷰 권고 자동 트리거

## ADR-006: 프로젝트 관리를 Monday.com에서 Notion으로 전환
- **날짜**: 2026-02-09 ~ 2026-03-17
- **커밋**: `7f9e052`, `c29e061`
- **결정**: Monday.com 올인원 보드에서 Notion DB 기반 태스크/의사결정/기술레퍼런스 관리로 전환
- **이유**: Notion API의 유연한 DB 구조, 자동 보고 + Slack 웹훅 연동 용이성
- **결과**: `integrations/notion/reporter.py` 통합 보고 모듈 구축. `report_completion()` 한 번 호출로 태스크+의사결정+기술레퍼런스+Slack 알림 일괄 처리

## ADR-007: 컨텍스트 경제학(ECC) 가이드 도입
- **날짜**: 2026-03-17
- **커밋**: `c29e061`
- **결정**: 에이전트 세션 관리에 컨텍스트 예산 원칙, MCP 10개 제한, codemap 기반 탐색 비용 최소화 적용
- **이유**: 200k 컨텍스트 창이 MCP/도구 수에 따라 실질 70k까지 축소되는 문제. 세션 간 상태 유실 방지
- **결과**: `/session-save`, `/session-restore` 커맨드 추가. 세션 메모리 시스템 구축

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-23 | git log 200건 분석 기반 ADR 7건 신규 작성 |
