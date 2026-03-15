# Git 워크플로우

> 출처: claude-forge git-workflow-v2.md 적응

## 커밋 메시지 형식

```
<type>: <description>

<선택적 본문>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

## PR 작성 시

1. 전체 커밋 히스토리 분석 (최신 커밋만이 아닌 모든 커밋)
2. `git diff [base-branch]...HEAD`로 전체 변경사항 확인
3. 종합적인 PR 요약 작성
4. 테스트 플랜 포함

## 기능 구현 워크플로우

```
/plan → 구현 (TDD) → /code-review → /verify-loop → 커밋 + push
```

1. **설계 먼저** — 3개 파일 이상 변경 시 `/plan` 필수
2. **TDD 접근** — 테스트 먼저 (RED) → 구현 (GREEN) → 리팩토링 (IMPROVE)
3. **코드 리뷰** — 구현 직후 `/code-review`
4. **검증** — `/verify-loop`로 빌드/테스트/린트 통과 확인
5. **커밋** — Conventional Commits 형식

## 브랜치 전략

```bash
# 기능 브랜치
git checkout -b feature/기능명

# 버그 수정
git checkout -b fix/버그설명

# 리팩토링
git checkout -b refactor/대상
```

## 금지

- `--force` push (deny 패턴으로 자동 차단)
- `--no-verify` 훅 우회
- main/master에 직접 커밋 (복잡한 변경 시)
