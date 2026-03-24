# /session-save

현재 작업 세션의 상태를 저장합니다.
컨텍스트 한계 도달 전, 또는 긴 작업의 중간 체크포인트로 사용합니다.

## 실행 순서

### 1. 자동 회고 (retrospective 연동)

먼저 이번 세션에서 수행한 작업을 분석하여 knowledge/에 기록할 항목을 추출하라:
- 새로운 기술 결정 → .claude/knowledge/decisions/README.md에 ADR 추가
- 발생한 실수/에러 → .claude/knowledge/mistakes/README.md에 추가
- 발견한 코드 패턴 → .claude/knowledge/patterns/README.md에 추가
- 추출할 내용이 없으면 스킵

### 2. 핸드오프 문서 갱신

.claude/handoff/current.md를 아래 정보로 갱신하라:

```bash
# git 상태 캡처
git status --short
git branch --show-current
git log --oneline -5
git diff --stat
git diff --name-only
```

포함 정보:
1. **작업 요약**: 이번 세션에서 한 일 (2-3문장)
2. **완료된 작업**: 커밋된 변경사항 기반 목록
3. **미완료/진행중 작업**: unstaged/staged 변경사항 또는 TODO 기반
4. **다음 세션에서 할 일**: 구체적으로 (파일명, 함수명 포함, 우선순위)
5. **변경 파일**: git diff --name-only 결과
6. **브랜치**: 현재 브랜치
7. **블로커/주의사항**: 에러나 실패 사항이 있었으면 기록

### 3. 핸드오프 히스토리 백업

```bash
mkdir -p .claude/handoff/history
cp .claude/handoff/current.md ".claude/handoff/history/$(date +%Y%m%d_%H%M%S).md"
```

### 4. 세션 상태 파일 생성

`context-compact` 스킬을 실행하여:
1. `.claude/handoff/session-{timestamp}.md` 생성
2. 완료/미완료/실패 항목 기록
3. 다음 단계 명시
4. 코드맵 갱신 (변경사항 있을 경우)
5. 복원 명령어 안내

### 5. 상태 파일 갱신

.planning/STATE.md도 함께 갱신하라:
- 현재 작업, 마지막 완료, 다음 단계
- /phase-loop 사용 중이면: 현재 어떤 단계에 있는지

### 6. 커밋 (선택)

핸드오프 문서 변경이 있으면:
```bash
git add .claude/handoff/ .claude/knowledge/
git commit -m "chore: session handoff $(date +%Y-%m-%d_%H:%M)"
```

## 외부 보고

핸드오프 저장 후 Slack에 자동 보고:
```bash
./scripts/report-to-external.sh session_save '{
  "summary": "{이번 세션 작업 요약}",
  "next_actions": "{다음 할 일}",
  "branch": "{현재 브랜치}",
  "changed_files": {변경 파일 수}
}'
```
