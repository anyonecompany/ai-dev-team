#!/bin/bash
# 외부 서비스(Notion/Slack) 보고 CLI
# 사용: ./scripts/report-to-external.sh <event_type> <json_data>
# 예시: ./scripts/report-to-external.sh qa_report '{"project":"portfiq","verdict":"GO"}'
#
# 이벤트: qa_report, retrospective, session_save, ci_fix, benchmark
# 환경변수 미설정 시 에러 없이 스킵됨

set -euo pipefail

EVENT_TYPE="${1:-}"
JSON_DATA="${2:-\{\}}"

if [ -z "$EVENT_TYPE" ]; then
    echo "사용법: $0 <event_type> '<json_data>'"
    echo "이벤트: qa_report, retrospective, session_save, ci_fix, benchmark"
    exit 1
fi

# 프로젝트 루트로 이동
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# JSON을 임시파일로 전달 (셸 이스케이프 문제 방지)
TMPFILE=$(mktemp)
printf '%s' "$JSON_DATA" > "$TMPFILE"
trap 'rm -f "$TMPFILE"' EXIT

python3 - "$EVENT_TYPE" "$TMPFILE" "$ROOT_DIR" <<'PYEOF'
import sys, json, os
from pathlib import Path

event_type = sys.argv[1]
tmpfile = sys.argv[2]
root_dir = sys.argv[3]

sys.path.insert(0, os.path.join(root_dir, 'integrations', 'shared'))
sys.path.insert(0, os.path.join(root_dir, 'integrations'))

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(Path(root_dir) / '.env')
except ImportError:
    pass

from report_dispatcher import dispatch_report

with open(tmpfile) as f:
    data = json.load(f)

result = dispatch_report(event_type, data)
print(json.dumps(result))
PYEOF
