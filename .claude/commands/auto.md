---
allowed-tools: Bash(git:*), Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Bash(python:*), Bash(go:*), Bash(cargo:*), Bash(make:*), Read, Write, Edit, Glob, Grep
description: 계획부터 커밋까지 원버튼 자동 실행. CRITICAL 보안 이슈에서만 중단.
argument-hint: [작업 설명] [--mode feature|bugfix|refactor]
---

# /auto - 원스톱 자동 워크플로우

개별 커맨드를 하나씩 호출하는 대신, 전체 파이프라인을 한 번에 자동 실행합니다.
CRITICAL 보안 이슈에서만 중단하며, 그 외에는 끝까지 진행합니다.

## 0단계: 인자 파싱

| 인자 | 기본값 | 설명 |
|------|--------|------|
| `--mode` | feature | 실행 모드: feature / bugfix / refactor |
| 나머지 텍스트 | - | 작업 설명 (필수) |

작업 설명이 없으면:
```
사용법: /auto [작업 설명]
예시:
  /auto 로그인 페이지 만들기
  /auto --mode bugfix 결제 금액이 0원으로 표시되는 버그
  /auto --mode refactor 인증 모듈 정리
```

## 1단계: 모드별 파이프라인

### feature 모드 (기본)
```
plan → tdd → code-review → verify-loop → commit + push
```
1. **plan**: 구현 계획 수립 → 자동 확정
2. **구현**: 테스트 먼저 작성 후 구현. RED → GREEN → IMPROVE
3. **code-review**: 보안+품질 검사. CRITICAL/HIGH → 자동 수정
4. **verify-loop**: 빌드/테스트/린트 자동 검증 (최대 3회)
5. **commit**: 커밋 메시지 자동 생성 + push

### bugfix 모드
```
탐색 → tdd → verify-loop → commit + push
```

### refactor 모드
```
분석 → 리팩토링 → code-review → verify-loop → commit + push
```

## 2단계: 환경 확인
1. Git 레포 확인 (`git rev-parse --is-inside-work-tree`)
2. 프로젝트 타입 감지 (package.json / pyproject.toml / go.mod / Cargo.toml)
3. 패키지 매니저 감지

## 3단계: 파이프라인 실행

### 전환 규칙
- 각 단계 완료 후 즉시 다음 단계 진행
- 사용자 확인 요청 안 함
- CRITICAL 보안 이슈에서만 중단

### 에러 처리
- **Fixable**: 린트, import, 타입 단순 오류 → 자동 수정 후 계속
- **Non-fixable**: 최대 3회 재시도 후 실패 보고
- **CRITICAL 보안**: 즉시 중단, 사용자 보고

## 4단계: 결과 요약

### 성공
```
══════════════════════════════════════════════════
  Auto Complete - [mode] 모드
══════════════════════════════════════════════════
  작업: [설명]
  [1] Plan         DONE
  [2] 구현         DONE   [N]개 테스트
  [3] Code Review  DONE   CRITICAL 0 / HIGH 0
  [4] Verify       PASS   빌드+테스트+린트 통과
  [5] Commit       DONE   [hash]
══════════════════════════════════════════════════
```

### 부분 실패
```
══════════════════════════════════════════════════
  Auto Incomplete - [mode] 모드
══════════════════════════════════════════════════
  실패 상세: [에러 목록]
  수동 수정 후: /verify-loop → 커밋
══════════════════════════════════════════════════
```

## Notion 보고

파이프라인 완료 시 자동 보고:
```python
from integrations.notion.reporter import report_task_done
report_task_done("auto: [작업설명]", "✅ 완료", "[결과 요약]")
```
