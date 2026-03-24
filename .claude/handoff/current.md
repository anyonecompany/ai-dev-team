# AI 개발팀 현재 상태

> 최종 갱신: 2026-03-24

---

## 최신 업데이트: 인프라 고도화 (2026-03-24)

### 작업 개요

에이전트 팀 인프라 전반을 고도화하여 규율 시스템 통합, 문서 정확성 확보, README 현행화를 수행했습니다.

### 주요 산출물

| 산출물 | 경로 | 설명 |
|--------|------|------|
| 에이전트 규율 참조 | `.claude/agents/*.md` (12개) | 전 에이전트에 workflow-discipline 규칙 참조 추가 |
| README 전면 재작성 | `README.md` | 현행 인프라 수치 반영 (커맨드 31, 스킬 10, 훅 12, 에이전트 12) |
| Knowledge README | `.claude/knowledge/README.md` | v3.0.0 — cross-reference 반영, 수치 정확화 |
| Codemap 인덱스 | `.claude/knowledge/codemap-index.md` | 갱신일 2026-03-24 업데이트 |
| Handoff 문서 | `.claude/handoff/current.md` | 이 문서 |
| STATE.md | `.planning/STATE.md` | 현재 상태 갱신 |

### 변경된 파일 목록

**수정:**
- `.claude/agents/PM-Planner.md` — 규율 섹션 추가
- `.claude/agents/Architect.md` — 규율 섹션 추가
- `.claude/agents/BE-Developer.md` — 규율 섹션 추가
- `.claude/agents/FE-Developer.md` — 규율 섹션 추가
- `.claude/agents/AI-Engineer.md` — 규율 섹션 추가
- `.claude/agents/QA-DevOps.md` — 규율 섹션 추가
- `.claude/agents/Security-Developer.md` — 규율 섹션 추가
- `.claude/agents/Orchestrator.md` — 규율 섹션 추가
- `.claude/agents/Designer.md` — 규율 섹션 추가
- `.claude/agents/CTO-Agent.md` — 규율 섹션 추가
- `.claude/agents/Tech-Lead.md` — 규율 섹션 추가
- `.claude/agents/QA-Engineer.md` — 규율 섹션 추가
- `README.md` — 전면 재작성
- `.claude/knowledge/README.md` — v3.0.0 갱신
- `.claude/knowledge/codemap-index.md` — 갱신일 업데이트
- `.planning/STATE.md` — 현재 상태 갱신

---

## 현재 인프라 수치

| 항목 | 수량 |
|------|------|
| 에이전트 | 12 (Opus 4, Sonnet 7, Haiku 1) |
| 커맨드 | 31 |
| 스킬 | 10 |
| 훅 | 12 (7 이벤트) |
| 규칙 | 8 (workflow-discipline 포함) |
| 스크립트 | 17 |
| GitHub Actions 워크플로우 | 8 |
| Knowledge ADR | 7 |
| Knowledge 실수 패턴 | 7 |
| Knowledge 코드 패턴 | 6 |

---

## 활성 프로젝트 상태

| 프로젝트 | 상태 | 배포 |
|----------|------|------|
| Portfiq | 진행중 | portfiq.fly.dev |
| La Paz Live | 진행중 | Vercel + Fly.io |
| La Paz Crawl | 운영중 | GitHub Actions (일일 크롤링) |
| Tactical GNN | 탐색 | - |
| AdaptFit AI | 탐색 | - |

---

## 미완료/다음 할 일

1. **Codemap 갱신**: codemap-portfiq, codemap-lapaz, codemap-others는 2026-03-23 기준 — 대규모 변경 시 `/codemap-update` 필요
2. **workflow-discipline.md 내용 확인**: 에이전트 12개가 참조하는 규칙 파일의 내용이 최신인지 확인 필요
3. **Portfiq 미해결 버그**: 감성 중립만 표시, 글씨 깨짐, 어드민 대시보드 에러
4. **La Paz Live**: 질문 DB Supabase 마이그레이션 필요 (SQLite 다중 인스턴스 문제)

---

## 이전 업데이트 이력

- 2026-03-23: Knowledge Library v2.0.0 — git log 분석 기반 전면 개편
- 2026-03-14: claude-forge 3-Phase 선별 도입
- 2026-02-09: Agent Teams 설정 및 운영 가이드 추가
- 2026-02-03: 운영 체계 고도화 (운영 원칙, 오더 템플릿, 에이전트 프로필 표준화)
