---
allowed-tools: Bash(git:*), Read, Grep
description: 간단한 수정용 빠른 커밋+push
argument-hint: [커밋 메시지]
---

# /quick-commit - 빠른 커밋

## 동작

1. **메시지 확인** — 없으면 에러
2. **변경사항 확인** — `git status --short`, `git diff --stat`
3. **규모 체크** — 3파일 초과 / 20줄 초과 시 경고:
   ```
   변경이 큽니다. /handoff-verify → 커밋 권장.
   그래도 진행하려면 "계속"이라고 입력하세요.
   ```
4. **빠른 검증** — `git diff`로 명백한 오류 체크
5. **커밋 실행**:
   ```bash
   git add -A
   git commit -m "{메시지}"
   git push
   ```

## 사용 예시

```bash
/quick-commit "fix: 오타 수정"
/quick-commit "chore: 의존성 업데이트"
```
