#!/bin/bash
# 에이전트 성능 벤치마크 리포트
# 사용: ./scripts/agent-benchmark.sh

AGENT_LOG="$HOME/.claude/logs/agent-activity.jsonl"
TOOL_LOG="$HOME/.claude/logs/tool-usage.jsonl"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  에이전트 성능 벤치마크"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "$AGENT_LOG" ]; then
    echo ""
    echo "⚠️ 에이전트 활동 로그 없음. 에이전트 사용 후 생성됩니다."
    echo "   /orchestrate 또는 서브에이전트 사용 시 자동 기록."
fi

if [ -f "$AGENT_LOG" ]; then
    echo ""
    echo "📊 에이전트별 호출 횟수:"
    jq -r 'select(.event == "SubagentStart") | .agent' "$AGENT_LOG" 2>/dev/null | \
      sort | uniq -c | sort -rn

    echo ""
    echo "📊 최근 에이전트 활동 (최근 10건):"
    tail -10 "$AGENT_LOG" 2>/dev/null | \
      jq -r '"\(.timestamp[:16]) | \(.event) | \(.agent)"' 2>/dev/null
fi

if [ -f "$TOOL_LOG" ]; then
    echo ""
    echo "━━━ 도구 사용 효율 ━━━"
    TOTAL=$(wc -l < "$TOOL_LOG" | tr -d ' ')
    echo "총 호출: ${TOTAL}회"

    echo ""
    echo "📊 도구별 호출 TOP 10:"
    jq -r '.tool' "$TOOL_LOG" 2>/dev/null | sort | uniq -c | sort -rn | head -10

    echo ""
    echo "📊 Read vs Write 비율:"
    READ_COUNT=$(jq -r 'select(.tool == "Read") | .tool' "$TOOL_LOG" 2>/dev/null | wc -l | tr -d ' ')
    WRITE_COUNT=$(jq -r 'select(.tool == "Write" or .tool == "Edit") | .tool' "$TOOL_LOG" 2>/dev/null | wc -l | tr -d ' ')
    echo "  Read: ${READ_COUNT} | Write+Edit: ${WRITE_COUNT}"
    if [ "$WRITE_COUNT" -gt 0 ] && [ "$READ_COUNT" -gt $(( WRITE_COUNT * 5 )) ]; then
        echo "  ⚠️ 탐색 비중 높음 — codemap/CLAUDE.md 갱신 검토"
    fi
fi

echo ""
echo "━━━ 개선 제안 ━━━"
echo "• Read 비율이 높으면: codemap/CLAUDE.md 갱신 또는 스킬 보강"
echo "• 특정 에이전트가 과다 호출되면: 해당 에이전트의 스킬/컨텍스트 확인"
echo "• 에이전트 활동이 없으면: /orchestrate 활용 권장"
