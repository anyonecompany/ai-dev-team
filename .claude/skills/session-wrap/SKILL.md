---
name: session-wrap
description: |
  세션 종료 전 자동 정리. 문서 업데이트, 학습 포인트, 후속 작업을 탐지하고 사용자에게 선택지를 제시.
  트리거: /session-wrap, 세션 마무리, 작업 마무리
argument-hint: '[--dry-run] [--skip-docs] [--skip-followup]'
---

# /session-wrap 스킬

## 파이프라인

```
[Phase 0] 컨텍스트 수집
  ├─ git diff --stat (이번 세션 변경사항)
  └─ 최근 커밋 10개

[Phase 1] 분석 (병렬)
  ├─ 문서 업데이트 필요 곳 탐지
  ├─ 학습 포인트 추출
  └─ 후속 작업 제안

[Phase 2] 사용자 선택

[Phase 3] 선택 항목 실행 + Notion 보고

[Phase 4] 리포트 출력
```

## Phase 0: 컨텍스트 수집

```bash
git diff --stat HEAD~5..HEAD
git diff --name-only HEAD~5..HEAD
git log --oneline -10
```

## Phase 1: 분석

3가지 관점에서 병렬 분석:

### 문서 업데이트 (--skip-docs 시 생략)
- 변경된 코드에 대응하는 문서가 있는지
- README, API 문서, 설정 가이드 업데이트 필요 여부

### 학습 포인트
- 이번 세션에서 배운 패턴/실수
- 반복되는 에러 패턴 → rules 추가 후보
- 새로운 기술 결정 → Notion 의사결정 DB 기록 후보

### 후속 작업 (--skip-followup 시 생략)
- TODO/FIXME 주석 발견
- 미완성 기능
- 테스트 커버리지 부족 영역
- 성능 개선 기회

## Phase 2: 선택

```
## 세션 정리 항목

### 자동 실행 - N건
1. [docs] README.md 타임스탬프 갱신
2. [docs] API 문서 엔드포인트 추가

### 선택 필요 - M건
3. [ ] [followup] auth 리팩토링 제안
4. [ ] [learning] "에러 핸들링 패턴" rules 추가

### 참고 - K건
5. [info] 변경 파일 12개, 커밋 5개

실행할 항목? (all / auto-only / 1,3 / none):
```

## Phase 3: 실행 + Notion 보고

선택된 항목 실행 후:

```python
from integrations.notion.reporter import report_completion

report_completion(
    task_name="session-wrap",
    status="✅ 완료",
    summary="문서 N건 업데이트, 후속 태스크 M건 생성",
    project_name="[프로젝트명]",
    new_tasks=[{"task_name": "후속 작업명", "priority": "🟡 P1", "done_criteria": "완료 조건"}]
)
```

## Phase 4: 리포트

```
Session Wrap 완료
  문서 업데이트: N건
  학습 포인트: M건
  후속 태스크: K건 (Notion에 등록됨)
```
