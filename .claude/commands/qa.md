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

### 3. 정적 검증

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

### 4. 서버 스모크 테스트 (런타임 검증)

정적 검증만으로는 실제 서버 기동 시 발생하는 문제(DB 초기화 누락, import 순서, 환경 설정 등)를 잡을 수 없다.
**반드시 실제 서버를 기동하고 API를 호출하여 런타임 동작을 검증한다.**

#### Python (FastAPI) 스모크 테스트:

```bash
# 1. 기존 DB 파일 백업 후 클린 상태로 테스트
cp todos.db todos.db.bak 2>/dev/null; rm -f todos.db

# 2. 서버 기동 (백그라운드, 임시 포트 사용)
timeout 30 python3 -m uvicorn app.main:app --port 9111 &
SERVER_PID=$!
sleep 3

# 3. 헬스체크
curl -sf http://localhost:9111/health || echo "FAIL: 헬스체크 실패"

# 4. CRUD 스모크 테스트
# - POST: 생성
CREATED=$(curl -sf -X POST http://localhost:9111/api/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"smoke test"}')
echo "POST 응답: $CREATED"

# - ID 추출 후 GET 단건 조회
TODO_ID=$(echo $CREATED | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
curl -sf http://localhost:9111/api/todos/$TODO_ID || echo "FAIL: GET 단건 조회 실패"

# - GET 목록 조회
curl -sf http://localhost:9111/api/todos || echo "FAIL: GET 목록 조회 실패"

# - PATCH 수정
curl -sf -X PATCH http://localhost:9111/api/todos/$TODO_ID \
  -H 'Content-Type: application/json' \
  -d '{"title":"updated"}' || echo "FAIL: PATCH 수정 실패"

# - PATCH 토글 (엔드포인트가 있는 경우)
curl -sf -X PATCH http://localhost:9111/api/todos/$TODO_ID/toggle || echo "FAIL: PATCH 토글 실패"

# - DELETE 삭제
curl -sf -X DELETE http://localhost:9111/api/todos/$TODO_ID || echo "FAIL: DELETE 삭제 실패"

# 5. 서버 종료
kill $SERVER_PID 2>/dev/null; wait $SERVER_PID 2>/dev/null

# 6. DB 복원
rm -f todos.db; mv todos.db.bak todos.db 2>/dev/null
```

#### Node.js/React 스모크 테스트:

```bash
# 1. 빌드 결과 확인 (index.html 존재 여부)
ls dist/index.html || echo "FAIL: 빌드 결과물 없음"

# 2. 프리뷰 서버 기동
npx vite preview --port 9112 &
PREVIEW_PID=$!
sleep 3

# 3. 프론트엔드 접속 확인
curl -sf http://localhost:9112/ | grep -q '<div id="root">' || echo "FAIL: 프론트엔드 페이지 로드 실패"

# 4. 서버 종료
kill $PREVIEW_PID 2>/dev/null; wait $PREVIEW_PID 2>/dev/null
```

#### 스모크 테스트 판정 기준:
- **PASS**: 서버 기동 성공 + 헬스체크 통과 + 전체 CRUD 정상 응답
- **FAIL**: 서버 기동 실패, 헬스체크 실패, 또는 CRUD 중 하나라도 에러 응답 (4xx/5xx)
- **SKIP**: 해당 유형 없음 (예: 프론트엔드 전용 프로젝트에서 백엔드 스모크 테스트)

### 5. 결과 종합
각 항목별 PASS/FAIL/SKIP 판정:
- 린트
- 타입 체크
- 단위 테스트
- 빌드
- **서버 스모크 테스트** (신규)

### 6. 연동 (Python으로 실행)
```python
import asyncio, sys, os
sys.path.insert(0, os.path.expanduser("~/ai-dev-team"))
from dotenv import load_dotenv; load_dotenv(os.path.expanduser("~/ai-dev-team/.env"))

from integrations.slack.slack_notifier import notify_qa_result
from integrations.monday.monday_sync import sync_project_qa

asyncio.run(notify_qa_result("{project_name}", {passed}, "{details}"))
asyncio.run(sync_project_qa("{project_name}", {results_dict}, "{details}"))
```

### 7. 리포트 저장
`.claude/reports/qa-{project-name}-{YYYYMMDD-HHmm}.md`
