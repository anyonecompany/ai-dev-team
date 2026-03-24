---
description: "빠른 실행. 단순 버그, 오타, 작은 수정에 사용. /phase-loop의 경량 버전. discuss/plan 스킵하고 바로 실행+검증."
---

# Quick — 경량 실행

$ARGUMENTS

## 용도

/phase-loop은 Medium/Large 작업용.
/quick은 Small 작업용:
- 오타/문구 수정
- 단일 파일 버그
- 작은 스타일 변경
- 간단한 설정 변경

## 프로세스

1. 작업 내용 파악 (파일 1-2개 이내인지 확인)
2. 바로 수정
3. lint + 테스트 실행
4. 통과하면 커밋

```
실행 → lint → test → commit
```

## 판단 기준

작업 크기가 모호할 때:
- 파일 1-2개 → /quick
- 파일 3-5개 → /plan → 수동 실행 → /verify-loop
- 파일 5개+ → /phase-loop

너무 큰 작업에 /quick을 쓰면 품질이 떨어진다.
확실하지 않으면 /phase-loop을 쓰라.
