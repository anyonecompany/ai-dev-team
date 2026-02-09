# QA 전체 실행

현재 프로젝트(또는 지정된 프로젝트)에 대해 전체 QA를 실행한다.

## 절차

1. 프로젝트 폴더 확인 (projects/ 하위)
2. 프로젝트 유형 감지 (package.json → Node.js, requirements.txt → Python, 등)
3. 유형별 검증 실행:

### Python 프로젝트
```bash
# 린트
ruff check . || flake8 .
# 타입 체크
mypy . || pyright .
# 테스트
pytest --tb=short
```

### Node.js/React 프로젝트
```bash
# 린트
npm run lint || npx eslint .
# 타입 체크
npx tsc --noEmit
# 테스트
npm test
# 빌드
npm run build
```

4. 결과를 종합하여 보고
5. 실패 항목이 있으면 원인 분석 및 수정 제안
6. integrations/slack/slack_notifier.py 를 통해 Slack에 결과 알림
7. integrations/monday/monday_sync.py 를 통해 Monday.com에 상태 업데이트
