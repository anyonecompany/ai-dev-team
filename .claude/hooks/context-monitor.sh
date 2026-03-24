#!/bin/bash
# PostToolUse 훅: 컨텍스트 사용량 모니터 (비동기)
# 도구 호출 횟수를 대리 지표로 사용

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
COUNT_FILE="/tmp/context_count_${SESSION_ID}"

if [ -f "$COUNT_FILE" ]; then
    COUNT=$(( $(cat "$COUNT_FILE") + 1 ))
else
    COUNT=1
fi
echo "$COUNT" > "$COUNT_FILE"

if [ "$COUNT" -eq 100 ]; then
    cat << 'EOF'
{"feedback": "컨텍스트 ~50% 추정 (도구 100회). /compact 권장. .planning/ 파일에 상태 저장됨."}
EOF
elif [ "$COUNT" -eq 140 ]; then
    cat << 'EOF'
{"feedback": "컨텍스트 ~70% 추정 (도구 140회). /compact 또는 /session-save -> 새 세션 강력 권장."}
EOF
fi

exit 0
