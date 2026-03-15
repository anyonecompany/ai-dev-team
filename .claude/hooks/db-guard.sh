#!/bin/bash
# DB Guard - PreToolUse Hook
# 위험한 SQL 패턴 차단: DROP, TRUNCATE, DELETE without WHERE, ALTER DROP
#
# 출처: claude-forge → ai-dev-team 적응
# Hook trigger: PreToolUse, matcher: Bash
# Exit codes: 0 = 허용, 2 = 차단

INPUT=$(cat)

QUERY=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
ti = data.get('tool_input', {})
cmd = ti.get('command', '')
# SQL 명령어를 포함할 수 있는 bash 명령 감지
print(cmd)
" 2>/dev/null)

if [[ -z "$QUERY" ]]; then
    exit 0
fi

QUERY_UPPER=$(echo "$QUERY" | tr '[:lower:]' '[:upper:]')

# Block DROP TABLE/DATABASE/SCHEMA
if echo "$QUERY_UPPER" | grep -qE '\bDROP\s+(TABLE|DATABASE|SCHEMA)\b'; then
    echo "BLOCKED: DROP statement detected" >&2
    echo "Query: ${QUERY:0:200}" >&2
    exit 2
fi

# Block TRUNCATE
if echo "$QUERY_UPPER" | grep -qE '\bTRUNCATE\b'; then
    echo "BLOCKED: TRUNCATE statement detected" >&2
    echo "Query: ${QUERY:0:200}" >&2
    exit 2
fi

# Block DELETE without WHERE
if echo "$QUERY_UPPER" | grep -qE '\bDELETE\s+FROM\b' && ! echo "$QUERY_UPPER" | grep -qE '\bWHERE\b'; then
    echo "BLOCKED: DELETE without WHERE clause" >&2
    echo "Query: ${QUERY:0:200}" >&2
    exit 2
fi

# Block ALTER TABLE ... DROP COLUMN
if echo "$QUERY_UPPER" | grep -qE '\bALTER\s+TABLE\b.*\bDROP\b'; then
    echo "BLOCKED: ALTER TABLE DROP detected" >&2
    echo "Query: ${QUERY:0:200}" >&2
    exit 2
fi

exit 0
