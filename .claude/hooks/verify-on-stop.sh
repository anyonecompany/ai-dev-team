#!/bin/bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')

# 무한루프 방지
if [ -f "/tmp/stop_hook_${SESSION_ID}" ]; then
    rm -f "/tmp/stop_hook_${SESSION_ID}"
    exit 0
fi
touch "/tmp/stop_hook_${SESSION_ID}"

MSGS="작업 완료 전: 1) lint/테스트 통과 2) 메모리 저장 3) /retrospective"

# phase-loop 미완료 체크
if [ -f ".planning/STATE.md" ]; then
    CURRENT=$(grep -A1 "## 현재 작업" .planning/STATE.md 2>/dev/null | tail -1)
    if [ -n "$CURRENT" ] && [ "$CURRENT" != "없음" ]; then
        MSGS="${MSGS} | phase-loop 미완료: ${CURRENT}"
    fi
fi

# 미커밋 변경 체크
UNCOMMITTED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
if [ "$UNCOMMITTED" -gt 0 ]; then
    MSGS="${MSGS} | 미커밋 ${UNCOMMITTED}건"
fi

cat << EOF
{"feedback": "${MSGS}"}
EOF
