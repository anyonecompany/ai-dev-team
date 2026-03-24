---
description: "작업 지시를 받아 태스크를 자동 분해하고 Notion에 등록한 뒤, 하나씩 자동 실행하여 완료할 때까지 반복. 사용자 개입 없이 자율 진행."
---

# /work — 자동 분해 + 자동 실행

$ARGUMENTS

## 프로세스

### Phase 1: 분석 + 태스크 분해

1. 프로젝트 감지:
   ```bash
   ./scripts/load-project-context.sh {프로젝트}
   ```

2. codemap과 CLAUDE.md 참조하여 하위 태스크로 분해:
   - 각 태스크는 1-3 파일 수정 범위 (Small~Medium)
   - 의존성 순서를 고려하여 순번 부여
   - 각 태스크에 완료 조건과 검증 방법 명시

### Phase 2: Notion 등록

```bash
python3 integrations/notion/task_manager.py add \
    "{태스크}" --project "{프로젝트}" --size "{S/M/L}" \
    --priority "{우선순위}" --order {순번} \
    --parent "{상위 작업}" --desc "{완료 조건}"
```

등록 후: `python3 integrations/notion/task_manager.py status`

### Phase 3: 자동 실행 루프

```
LOOP:
  1. python3 integrations/notion/task_manager.py next
  2. 없으면 → Phase 4
  3. 있으면:
     a. update {id} --status "🔄 진행중"
     b. 크기별 실행: S→바로, M→plan+실행, L→discuss+plan+실행
     c. 성공 → update {id} --status "✅ 완료" --result "요약" --commit "해시"
     d. 실패 → 1회 재시도, 재실패 → update --status "⏸️ 보류" --result "에러"
     e. → LOOP
```

### Phase 4: 완료

1. `python3 integrations/notion/task_manager.py status`
2. /retrospective
3. `./scripts/update-notion-status.sh update`
4. /session-save

## 컨텍스트 관리
- 태스크 5개마다 컨텍스트 확인
- 50% 넘으면 /compact → Notion에서 다음 태스크 재조회

## 규율
- lint + test 통과 필수
- 실패 태스크 강제 완료 금지
- DB 스키마 변경은 사용자 확인 필요

## 사용 예시
```
/work Portfiq 푸시 알림 기능 추가
/work ai-dev-team cross-reference 기술 부채 전부 정리
```
