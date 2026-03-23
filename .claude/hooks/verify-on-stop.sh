#!/bin/bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')

# 무한루프 방지
if [ -f "/tmp/stop_hook_${SESSION_ID}" ]; then
    rm -f "/tmp/stop_hook_${SESSION_ID}"
    exit 0
fi
touch "/tmp/stop_hook_${SESSION_ID}"

cat << 'EOF'
{
  "feedback": "작업 완료 전 확인: 1) lint/테스트 통과 2) 메모리에 학습 저장 3) 새로운 실수/패턴/결정이 있었으면 knowledge/에 기록 (또는 /retrospective 실행). 모두 완료했으면 진행."
}
EOF
