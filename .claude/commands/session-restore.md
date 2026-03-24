# /session-restore [timestamp or filepath]

저장된 세션 상태를 로드하여 작업을 이어갑니다.

## 사용법
- `/session-restore` — 가장 최근 세션 파일 자동 로드
- `/session-restore 2025-01-20-1430` — 특정 타임스탬프 세션 로드
- `/session-restore path/to/file.md` — 직접 경로 지정

## 실행 순서

### 1. 핸드오프 복원

.claude/handoff/current.md를 읽어라. 없으면 .claude/handoff/history/에서 가장 최근 파일을 사용.

### 2. 요약 출력

사용자에게 아래를 보여라:
- **이전 세션 요약**: 작업 요약 섹션
- **이어서 할 일**: 다음 세션에서 할 일 섹션
- **블로커/주의사항**: 있으면 표시

### 3. 프로젝트 컨텍스트 자동 로드

변경된 파일 경로에서 프로젝트를 추론하여 해당 codemap을 참조하라:
- `projects/portfiq` → `.claude/knowledge/codemap-portfiq.md`
- `projects/la-paz` 또는 `lapaz` → `.claude/knowledge/codemap-lapaz.md`
- 기타 → `.claude/knowledge/codemap-others.md`

해당 프로젝트의 CLAUDE.md도 함께 참조.

### 4. 현재 상태 비교

```bash
git status --short
git log --oneline -5
```

핸드오프 시점과 현재 상태 차이를 보고하라.

### 5. 상태 파일 복원

.planning/STATE.md도 확인하라.
/phase-loop이 중단된 경우:
- STATE.md에서 현재 단계를 확인
- 해당 단계의 CONTEXT.md 또는 PLAN.md를 읽고 이어서 진행

### 6. 작업 재개 확인

"바로 시작하시겠습니까?" 라고 물어라.

## 핸드오프 문서가 없을 때

1. `.claude/handoff/` 에서 해당 세션 파일 로드
2. 세션 파일도 없으면 git log --oneline -10 을 보여주고
3. 최근 변경 기반으로 컨텍스트를 재구성하라
4. "어디서부터 이어갈까요?" 확인 후 즉시 작업 재개
