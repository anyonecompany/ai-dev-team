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
  "feedback": "작업 완료 전 확인: 1) 변경 파일 lint 에러 없는지 2) 테스트 통과하는지 3) 메모리에 학습 내용 저장했는지. 하나라도 안 했으면 수행하라."
}
EOF
