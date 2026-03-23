---
description: "작업 회고. 완료된 작업에서 의사결정, 실수, 패턴을 추출하여 knowledge/에 자동 기록. 작업 완료 후 또는 /session-save 전에 실행."
---

# 자동 회고

이번 세션에서 수행한 작업을 분석하여 knowledge/에 기록할 항목을 추출하라.

## 1. 의사결정 추출

이번 세션에서 내린 기술적/아키텍처적 결정이 있는지 확인:
- 라이브러리 선택, 패턴 적용, 구조 변경 등
- 있으면 .claude/knowledge/decisions/README.md에 ADR 추가

형식:
```
## ADR-{다음 번호}: {제목}
- 날짜: {오늘}
- 결정: {무엇을 결정했나}
- 이유: {왜 그렇게 결정했나}
- 결과: {어떤 영향이 있나}
- 관련 커밋: {해시}
```

## 2. 실수/이슈 추출

이번 세션에서 발생한 에러, 실수, 예상 밖 동작이 있는지 확인:
- 빌드 실패, 테스트 실패, 런타임 에러 등
- 있으면 .claude/knowledge/mistakes/README.md에 추가

형식:
```
## M-{다음 번호}: {증상 한줄}
- 프로젝트: {프로젝트명}
- 증상: {무슨 일이 일어났나}
- 원인: {왜 발생했나}
- 해결: {어떻게 고쳤나}
- 예방: {다음에 어떻게 방지할 수 있나}
```

## 3. 패턴 추출

이번 세션에서 반복 사용하거나 새로 발견한 코드 패턴이 있는지 확인:
- 있으면 .claude/knowledge/patterns/README.md에 추가

형식:
```
## P-{다음 번호}: {패턴명}
- 구조: {어떤 구조인가}
- 적용처: {어디에 적용하면 좋은가}
- 주의사항: {사용 시 주의점}
```

## 4. 스킬 Gotchas 업데이트

실수나 이슈 중 특정 프로젝트와 관련된 것이 있으면
해당 프로젝트 스킬의 Gotchas 섹션에도 추가:
- portfiq 관련 → .claude/skills/portfiq-dev/SKILL.md의 Gotchas
- lapaz 관련 → .claude/skills/lapaz-dev/SKILL.md의 Gotchas

## 실행 규칙
- 추출할 내용이 없으면 "이번 세션에서 새로운 학습 항목 없음" 이라고 보고
- 기존 항목과 중복이면 추가하지 않음
- 번호(ADR-N, M-N, P-N)는 기존 파일에서 마지막 번호 확인 후 +1
- 추가 후 `git add .claude/knowledge/ && git commit -m "chore: auto-retrospective {날짜}"`
