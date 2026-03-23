#!/bin/bash
# SubagentStart/SubagentStop 훅: 에이전트 활동 로깅

INPUT=$(cat)

LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR"

EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // "unknown"')
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.agent_type // "unknown"')
SESSION=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TIMESTAMP=$(date -Iseconds)

jq -n \
  --arg ts "$TIMESTAMP" \
  --arg event "$EVENT" \
  --arg agent "$AGENT_NAME" \
  --arg session "$SESSION" \
  '{timestamp: $ts, event: $event, agent: $agent, session: $session}' \
  >> "$LOG_DIR/agent-activity.jsonl"

exit 0
