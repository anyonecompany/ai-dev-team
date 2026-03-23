#!/bin/bash
# SessionStart 훅: 세션 시작 시 인프라 상태 간단 체크

MSGS=""

# codemap 신선도 체크
STALE_COUNT=0
for codemap in .claude/knowledge/codemap-portfiq.md .claude/knowledge/codemap-lapaz.md; do
    if [ -f "$codemap" ]; then
        CM_DATE=$(git log -1 --format="%ai" -- "$codemap" 2>/dev/null | cut -d' ' -f1 | tr -d '-')
        TODAY=$(date +%Y%m%d)
        if [ -n "$CM_DATE" ]; then
            DIFF=$(( TODAY - CM_DATE ))
            if [ "$DIFF" -gt 7 ]; then
                STALE_COUNT=$((STALE_COUNT + 1))
            fi
        fi
    fi
done

if [ "$STALE_COUNT" -gt 0 ]; then
    MSGS="${STALE_COUNT}개 codemap이 7일 이상 지남 — /codemap-update 권장"
fi

# 비용 체크 (어제 사용량 기반)
TOOL_LOG="$HOME/.claude/logs/tool-usage.jsonl"
if [ -f "$TOOL_LOG" ]; then
    YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d 2>/dev/null || echo "")
    if [ -n "$YESTERDAY" ]; then
        YESTERDAY_COUNT=$(grep "$YESTERDAY" "$TOOL_LOG" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$YESTERDAY_COUNT" -gt 500 ]; then
            if [ -n "$MSGS" ]; then
                MSGS="${MSGS} | "
            fi
            MSGS="${MSGS}어제 도구 호출 ${YESTERDAY_COUNT}회 — ./scripts/cost-alert.sh로 확인"
        fi
    fi
fi

if [ -n "$MSGS" ]; then
    cat << EOF
{"feedback": "📋 ${MSGS}"}
EOF
fi

exit 0
