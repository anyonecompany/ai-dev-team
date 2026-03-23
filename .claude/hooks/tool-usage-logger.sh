#!/bin/bash
# PostToolUse 훅: 도구 사용 이력 로깅 (비동기)
# 세션별, 도구별 사용 패턴을 기록하여 비용 분석에 활용

INPUT=$(cat)

LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR"

TOOL=$(echo "$INPUT" | jq -r '.tool_name // "unknown"')
SESSION=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TIMESTAMP=$(date -Iseconds)

# 도구 입력의 크기 (토큰 대리 지표)
INPUT_SIZE=$(echo "$INPUT" | jq -r '.tool_input // {}' | wc -c)

# JSONL 형식으로 로깅
jq -n \
  --arg ts "$TIMESTAMP" \
  --arg tool "$TOOL" \
  --arg session "$SESSION" \
  --argjson size "$INPUT_SIZE" \
  '{timestamp: $ts, tool: $tool, session: $session, input_bytes: $size}' \
  >> "$LOG_DIR/tool-usage.jsonl"

exit 0
