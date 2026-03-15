---
name: verification-engine
description: 통합 검증 엔진 - 증거 기반 검증 루프
version: 2.0.0
---

# 검증 엔진 (Verification Engine)

`/handoff-verify`, `/verify-loop` 커맨드의 핵심 로직.

## 철의 법칙

```
실행 증거 없이 완료를 선언할 수 없다.
```

## 게이트 함수

```
1. IDENTIFY — 증명할 명령은?
2. RUN      — 전체 실행 (새로, 완전히)
3. READ     — 전체 출력, exit code 확인
4. VERIFY   — 출력이 주장을 확인하는가?
5. CLAIM    — 이제서야 결과 선언
```

## 검증 파이프라인

```
[1] 환경 파악 → 프로젝트 타입, PM 감지
[2] 빌드 검증 → npm build / go build / cargo build
[3] 타입 검사 → tsc --noEmit / mypy / go vet
[4] 린트 검사 → eslint / ruff / clippy
[5] 테스트    → npm test / pytest / go test
[6] 코드 리뷰 → 변경 파일 + 의존성 분석
[7] 보안 검토 → (--security 시) OWASP 패턴 검사
```

## Fixable 자동 수정

| 유형 | 수정 방법 |
|------|----------|
| import 누락 | 소스 검색 → import 추가 |
| unused import | import 행 제거 |
| 린트 (auto-fixable) | `eslint --fix` / `ruff --fix` |
| 타입 단순 오류 | 타입 추론 수정 |
| 포맷팅 | prettier / black |
| missing return type | 반환값에서 추론 |

## Non-fixable (보고만)

- 로직 오류
- 아키텍처 문제
- 테스트 로직 자체의 오류
- 보안 취약점 (security-pipeline 처리)

## 연동

- `/handoff-verify` → 이 엔진으로 검증
- `/verify-loop` → 이 엔진으로 루프 검증
- `/auto` → 파이프라인 중 검증 단계에서 사용
- `/commit` 전 → 사전 검증 게이트
