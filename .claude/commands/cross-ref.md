---
description: "프로젝트간 cross-reference 조회 및 갱신. 공유 패턴, 공통 이슈, 재사용 코드 확인."
---

# Cross-Reference 조회/갱신

$ARGUMENTS

## 조회 모드 (기본)
.claude/knowledge/cross-reference.md를 읽고 요약하라.
사용자가 특정 항목을 묻는 경우 해당 섹션만 출력.

## 갱신 모드 (/cross-ref update)
인자에 "update"가 포함되면:
1. 각 프로젝트의 현재 코드를 재분석
2. cross-reference.md를 갱신
3. 새로 발견된 공통 패턴/이슈 추가
4. git commit -m "chore: refresh cross-reference $(date +%Y-%m-%d)"

## 비교 모드 (/cross-ref compare {패턴명})
특정 패턴이 각 프로젝트에서 어떻게 구현되어 있는지 비교 분석.
