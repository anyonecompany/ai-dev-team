---
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(rm:*), Bash(cp:*), Read, Write
description: 작업 상태 저장/복원 (git patch 기반)
argument-hint: save|restore|list|diff|delete ["이름"] [--tag 태그]
---

# /checkpoint - 작업 상태 저장/복원

## 서브커맨드

| 커맨드 | 설명 | 필수 인자 |
|--------|------|----------|
| `save` | 현재 상태 저장 | "이름" |
| `restore` | 저장된 상태 복원 | "이름" |
| `list` | 체크포인트 목록 | 없음 |
| `diff` | 체크포인트 vs 현재 비교 | "이름" |
| `delete` | 체크포인트 삭제 | "이름" |

## 저장 경로

```
.claude/checkpoints/{name}/
  metadata.json      # 브랜치, 커밋, 통계
  staged.patch       # staged 변경
  unstaged.patch     # unstaged 변경
  untracked/         # untracked 파일 복사본
```

## save 동작

1. `git diff --cached > staged.patch`
2. `git diff > unstaged.patch`
3. untracked 파일 복사
4. metadata.json 생성 (name, timestamp, branch, commit, stats, tags)

## restore 동작

1. 현재 상태를 `pre-restore-{timestamp}`로 자동 백업
2. `git apply staged.patch` + `git add -A`
3. `git apply unstaged.patch`
4. untracked 파일 복원
5. 복원 검증

## 사용 예시

```bash
/checkpoint save "기능완료"
/checkpoint save "pre-refactor" --tag stable
/checkpoint list
/checkpoint diff "기능완료"
/checkpoint restore "기능완료"
/checkpoint delete "pre-refactor"
```
