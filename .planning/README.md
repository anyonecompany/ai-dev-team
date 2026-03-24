# .planning/ — 영속 상태 디렉토리

GSD 패턴에서 영감. 모든 작업 상태를 파일로 영속화하여 컨텍스트 rot을 방지한다.

## 파일 구조

```
.planning/
├── README.md           ← 이 파일
├── STATE.md            ← 현재 진행 상태 (자동 갱신)
├── {작업명}-CONTEXT.md ← /discuss 출력 (결정 사항)
├── {작업명}-PLAN.md    ← /plan 출력 (실행 계획)
└── {작업명}-UAT.md     ← /verify-loop 출력 (검증 결과)
```

## 사용법

- /phase-loop 실행 시 자동 생성
- /discuss 실행 시 CONTEXT.md 생성
- /plan 실행 시 PLAN.md 생성
- /compact 후에도 이 파일들을 읽으면 컨텍스트 복원
- /session-restore 시 STATE.md 참조
