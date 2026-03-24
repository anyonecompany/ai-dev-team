---
description: "게이트 루프 워크플로우. Medium/Large 작업을 discuss→plan→execute→verify 순서로 진행. 각 단계 통과해야 다음 진행. GSD 패턴 기반."
---

# Phase Loop — 게이트 워크플로우

$ARGUMENTS

## 개요

이 커맨드는 작업을 5단계 게이트 루프로 진행한다.
각 단계를 통과해야만 다음 단계로 넘어간다.
통과 실패 시 해당 단계를 반복한다 (최대 3회).

## 단계 흐름

```
┌─────────────────────────────────────────────────┐
│  Phase Loop — 게이트 워크플로우                  │
│                                                  │
│  ① /discuss         ← 결정 사항 잠금            │
│     ↓ [CONTEXT.md 생성됨?] → 통과               │
│  ② /plan            ← 실행 계획 수립            │
│     ↓ [PLAN.md Nyquist 통과?] → 통과            │
│  ③ /orchestrate     ← 병렬 실행                 │
│     ↓ [빌드/lint 성공?] → 통과                   │
│  ④ /verify-loop     ← 자동 검증 (최대 3회)      │
│     ↓ [테스트 전체 통과?] → 통과                 │
│  ⑤ /qa              ← 최종 QA                   │
│     ↓ [GO 판정?] → 완료                          │
│                                                  │
│  /retrospective → /session-save                  │
└─────────────────────────────────────────────────┘
```

## 실행 규칙

### ① Discuss (결정 잠금)
- /discuss 커맨드를 실행하여 작업의 선호도와 결정 사항을 확정
- 출력: .planning/{작업명}-CONTEXT.md
- 게이트: CONTEXT.md가 생성되고 "확정 사항" 섹션이 있으면 통과
- 미통과 시: 추가 질문으로 불명확한 항목 해소

### ② Plan (실행 계획)
- /plan 커맨드를 실행하되, CONTEXT.md를 입력으로 참조
- 출력: .planning/{작업명}-PLAN.md
- 게이트: Nyquist 검증 통과 (테스트 루프 + 완료 조건 + 수정 범위)
- 미통과 시: 계획 보완 후 재검증

### ③ Execute (병렬 실행)
- /orchestrate 커맨드로 Agent Teams 병렬 실행
- PLAN.md를 각 에이전트에 분배
- 게이트: 빌드 성공 + lint 통과
- 미통과 시: /build-fix 실행 후 재확인

### ④ Verify (자동 검증)
- /verify-loop 커맨드로 자동 재검증 (최대 3회)
- 게이트: 전체 테스트 통과
- 미통과 시: 실패 테스트 수정 → 재검증 (3회 후에도 실패 시 수동 표시)

### ⑤ QA (최종 품질)
- /qa 커맨드로 최종 QA
- 게이트: GO 또는 CONDITIONAL GO 판정
- NO GO 시: 이전 단계로 돌아가 해당 이슈 수정

### 완료
- /retrospective → knowledge/ 자동 축적
- /session-save → 핸드오프 + STATE.md 갱신

## 컨텍스트 관리

각 단계 사이에서 컨텍스트가 50%를 넘으면 /compact 실행.
상태 파일(.planning/)에 모든 결정이 기록되어 있으므로
/compact 후에도 .planning/ 파일을 읽으면 컨텍스트 복원 가능.

## 사용 예시

```
/phase-loop Portfiq 푸시 알림 기능 추가
```
