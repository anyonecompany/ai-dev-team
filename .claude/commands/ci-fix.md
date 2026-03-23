---
description: "CI/CD 실패 자동 진단 및 수정. GitHub Actions 실패 시 사용. 파이프라인 에러 분석, 수정, 재검증 루프."
---

# CI 실패 자동 수정

$ARGUMENTS

## 실행 절차

### Phase 1: 진단
1. GitHub Actions 최근 실패 로그를 확인하라:
   ```bash
   gh run list --limit 5 --status failure 2>/dev/null || echo "gh CLI 없음 — 수동으로 실패 로그를 제공하라"
   ```

2. 사용자가 실패 로그를 붙여넣으면 해당 에러를 분석

3. 에러 유형 분류:
   - 타입 에러 → /build-fix 위임
   - 테스트 실패 → 해당 테스트 파일 분석 후 수정
   - 린트 에러 → 자동 포맷팅 적용
   - 의존성 에러 → requirements.txt / pubspec.yaml 확인
   - 배포 에러 → 환경변수/설정 확인

### Phase 2: 수정
1. 에러 유형에 맞는 수정 적용
2. 수정 범위를 최소화 (CI 실패 원인만 해결)
3. 관련 없는 파일 수정 금지

### Phase 3: 검증
1. 로컬에서 CI와 동일한 검증 실행:
   ```bash
   # Portfiq 백엔드
   cd projects/portfiq/backend && ruff check . && python -m pytest 2>/dev/null

   # Portfiq Flutter
   cd projects/portfiq/apps/mobile && flutter analyze && flutter test 2>/dev/null

   # La Paz
   cd projects/la-paz && ruff check . && python -m pytest 2>/dev/null
   ```

2. 통과하면 커밋 + push
3. 실패하면 Phase 2로 돌아가 재수정 (최대 3회)

### Phase 4: 회고
수정 완료 후 .claude/knowledge/mistakes/README.md에 이번 CI 실패를 기록:
- 증상, 원인, 수정 방법, 예방책

## gh CLI 없을 때

사용자가 실패 로그를 직접 붙여넣을 수 있다.
또는 GitHub Actions 로그 URL을 제공하면 web fetch로 확인.

사용 방법:
1. `/ci-fix` — 자동 진단 시도
2. `/ci-fix {에러 메시지 또는 URL}` — 특정 에러에 대한 수정
