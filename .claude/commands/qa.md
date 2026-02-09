# /qa - QA 전체 실행

대상 프로젝트에 전체 QA를 실행하고 결과를 Monday.com과 Slack에 공유한다.

## 사용법
```
/qa                    # 가장 최근 수정된 프로젝트 대상
/qa {project-name}     # 특정 프로젝트 대상
```

## 절차

### 1. 프로젝트 감지
- 인자가 있으면 `projects/{project-name}*` 에서 찾기
- 없으면 `projects/` 하위에서 가장 최근 수정된 폴더

### 2. 프로젝트 유형 감지
- `package.json` → Node.js/React
- `requirements.txt` 또는 `pyproject.toml` → Python
- 둘 다 → Fullstack (둘 다 실행)

### 3. 검증 실행

**Python:**
```bash
ruff check . 2>&1
mypy . 2>&1 || pyright .
pytest --tb=short 2>&1
```

**Node.js/React:**
```bash
npm run lint 2>&1 || npx eslint . 2>&1
npx tsc --noEmit 2>&1
npm test 2>&1
npm run build 2>&1
```

### 4. 결과 종합
각 항목별 PASS/FAIL/SKIP 판정

### 5. 연동 (Python으로 실행)
```python
import asyncio, sys, os
sys.path.insert(0, os.path.expanduser("~/ai-dev-team"))
from dotenv import load_dotenv; load_dotenv(os.path.expanduser("~/ai-dev-team/.env"))

from integrations.slack.slack_notifier import notify_qa_result
from integrations.monday.monday_sync import sync_project_qa

asyncio.run(notify_qa_result("{project_name}", {passed}, "{details}"))
asyncio.run(sync_project_qa("{project_name}", {results_dict}, "{details}"))
```

### 6. 리포트 저장
`.claude/reports/qa-{project-name}-{YYYYMMDD-HHmm}.md`
