# 워크플로우 규율 규칙

## 작업 크기별 필수 워크플로우

### Small (1-2파일)
- /quick 또는 /auto. 게이트 없음.

### Medium (3-5파일)
- 최소: /plan → 실행 → /verify-loop
- 권장: /discuss → /plan → 실행 → /verify-loop → /retrospective

### Large (5파일+, 아키텍처, MVP)
- **필수**: /discuss → /plan → /orchestrate → /verify-loop → /qa
- CONTEXT.md 없이 /plan 금지 (넛지)
- PLAN.md 없이 /orchestrate 금지 (차단)
- Nyquist 검증 통과 필수
- /qa 전 /verify-loop 통과 필수

## 컨텍스트 관리
- 도구 100회 → /compact 권장
- 도구 140회 → /compact 강제 또는 새 세션
- Large 작업 → 서브에이전트 위임, 메인 세션 직접 구현 자제

## 커밋 규율
- 테스트 실패 상태 커밋 금지 (hotfix 제외)
- 미커밋 변경으로 세션 종료 금지
- 태스크별 atomic commit

## 검증 규율
- 모든 코드 변경에 관련 테스트 실행
- 테스트 없는 계획은 Nyquist 불합격
