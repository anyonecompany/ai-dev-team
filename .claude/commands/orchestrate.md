---
allowed-tools: Bash(git:*), Read, Write, Glob, Grep
description: Agent Teams 기반 병렬 오케스트레이션
argument-hint: [--type feature|bugfix|refactor|review] [--parallel N] [--dry-run]
---

# /orchestrate - Agent Teams 병렬 오케스트레이션

Agent Teams API로 여러 에이전트가 동시에 작업합니다.

## 전제조건

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (settings.local.json에 설정됨)
- tmux 세션 안에서 실행 권장

## 파라미터

| 플래그 | 기본값 | 설명 |
|--------|--------|------|
| `--dry-run` | false | 계획만 출력 |
| `--type` | auto | feature / bugfix / refactor / review |
| `--parallel` | 3 | 동시 팀원 수 (최대 3) |

## Type별 팀 구성

### feature (3명)
- Implementer 1: 핵심 기능 구현
- Implementer 2: 보조 기능 구현
- Tester: 테스트 작성 + 리뷰

### bugfix (2명)
- Investigator: 버그 원인 분석
- Fixer: 수정 + 테스트

### refactor (3명)
- Analyzer: 코드 분석
- Implementer: 리팩토링 실행
- Verifier: 테스트 + 검증

### review (3명)
- Security Reviewer: 보안 분석
- Performance Reviewer: 성능 분석
- Quality Reviewer: 코드 품질 분석

## 실행 절차

1. **도메인 감지**: package.json / pyproject.toml / go.mod 등
2. **태스크 파싱**: 계획에서 미완료 태스크 추출
3. **의존성 분석**: 명시적 + 파일 기반 + 모듈 기반 의존성 → DAG
4. **Wave 그룹화**: 병렬 실행 가능 그룹으로 분류
5. **팀원 생성 및 작업 배정**
6. **Wave별 순차 실행** (Wave 내부는 병렬)
7. **결과 수집 및 리포트**

## 파일 소유권 (CRITICAL)

같은 파일을 2명이 편집하지 않도록 반드시 분리:

| 에이전트 | 담당 |
|---------|------|
| BE-Developer | `backend/`, `api/`, `models/`, `services/` |
| FE-Developer | `frontend/`, `src/`, `components/`, `pages/` |
| QA-DevOps | `tests/`, `__tests__/` |

## Notion 보고

오케스트레이션 완료 시:
```python
report_task_done("orchestrate: [작업]", "✅ 완료", "팀원 N명, Wave M개, 태스크 K개 완료")
```

## 프로젝트 컨텍스트 자동 주입

/orchestrate 실행 시 아래 순서로 프로젝트를 감지하고 컨텍스트를 주입하라:

### 1. 프로젝트 감지
사용자의 작업 지시에서 프로젝트를 추론:
- "portfiq", "포트픽", "ETF", "브리핑" → portfiq
- "la paz", "라파즈", "축구", "실시간" → lapaz
- "서로연" → seoroyeon
- "adaptfit" → adaptfitai
- 파일 경로 언급 시 → 해당 프로젝트
- 감지 불가 시 → 사용자에게 확인

### 2. 컨텍스트 로드
감지된 프로젝트에 따라 아래를 읽어라:
- `.claude/knowledge/codemap-{프로젝트}.md`
- `projects/{프로젝트}/CLAUDE.md`
- 관련 스킬 (portfiq → portfiq-dev, lapaz → lapaz-dev)

컨텍스트 로딩 스크립트:
```bash
./scripts/load-project-context.sh {프로젝트명}
```

### 3. 에이전트별 컨텍스트 전달
각 teammate/서브에이전트에게 위임할 때 다음을 포함:
- **PURPOSE**: 이 태스크를 왜 하는지 (전체 목표와의 관계)
- **SCOPE**: 수정 가능/금지 범위 (CLAUDE.md에서 추출)
- **ENTRY POINTS**: 작업 시작점 (codemap에서 추출)
- **DEPENDENCIES**: 다른 에이전트 작업과의 의존성
- **RETURN FORMAT**: summary만 (코드 덤프 금지)

### 4. 에이전트 매핑 규칙
| 작업 유형 | 주담당 에이전트 | 스킬 프리로드 |
|---|---|---|
| 백엔드 API | BE-Developer | {프로젝트}-dev, code-quality |
| 프론트엔드 | FE-Developer | {프로젝트}-dev, code-quality |
| AI/ML | AI-Engineer | {프로젝트}-dev |
| 테스트/배포 | QA-DevOps | code-quality, deployment |
| 보안 | Security-Developer | security-review |

## 사용 예시

```bash
/orchestrate --dry-run
/orchestrate --type feature
/orchestrate --type bugfix --parallel 2
/orchestrate --type review
```
