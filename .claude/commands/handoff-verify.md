---
allowed-tools: Bash(git:*), Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Read, Write, Edit, Glob, Grep
description: 빌드/테스트/린트를 한 번에 자동 검증 (서브에이전트 fresh context)
argument-hint: [--once] [--loop N] [--security] [--skip-handoff]
---

# /handoff-verify - 핸드오프 + 자동 검증

## 파라미터

| 플래그 | 기본값 | 설명 |
|--------|--------|------|
| `--once` | false | 단발 검증 (루프 없음) |
| `--loop N` | 5 | 최대 재시도 횟수 |
| `--security` | false | 보안 리뷰 포함 |
| `--skip-handoff` | false | handoff.md 생성 건너뛰기 |

## 실행 흐름

### 1단계: 환경 수집
- `git status --short`, `git diff --name-only`
- 프로젝트 타입 감지 (Node.js / Python / Go / Rust)
- 패키지 매니저 감지

### 2단계: Handoff 문서 생성 (--skip-handoff 시 생략)
`.claude/handoff.md`에 변경 의도, 변경 파일, 테스트 필요사항 자동 기록

### 3단계: 검증 파이프라인

프로젝트 타입별:
- **Node.js**: `tsc --noEmit` → `eslint` → `npm run build` → `npm test`
- **Python**: `python3 -m py_compile` → `ruff check` → `pytest`
- **Go**: `go vet` → `go build ./...` → `go test ./...`

### 4단계: 실패 시 자동 수정 (루프)

**Fixable 에러:**
- import 누락 → 자동 추가
- 린트 포맷 → `eslint --fix`
- 미사용 import → 자동 제거
- 타입 단순 오류 → 추론 수정

**Non-fixable 에러:**
- 로직 오류 → 보고만
- 아키텍처 문제 → 보고만

### 5단계: 결과

```
통과:
  ✅ Handoff-Verify 완료
  다음: 커밋 + push

실패 (N회 소진):
  ❌ 반복 실패 에러 목록
  권장: 수동 수정 후 /handoff-verify --skip-handoff
```

## 다음 단계

| 검증 후 | 액션 |
|:--------|:-----|
| 커밋 | 수동 커밋 + push |
| 빠른 커밋 | `/quick-commit "메시지"` |
| 전체 QA | `/qa` |
