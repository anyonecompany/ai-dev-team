#!/bin/bash
# Codemap 신선도 체크
# 각 codemap의 마지막 갱신일과 해당 프로젝트의 마지막 커밋일을 비교

echo "━━━ Codemap 신선도 체크 ━━━"

check_freshness() {
    local project=$1
    local codemap=$2
    local project_path=$3

    if [ ! -f "$codemap" ]; then
        echo "⚠️  $project: codemap 없음 ($codemap)"
        return
    fi

    CODEMAP_DATE=$(git log -1 --format="%ai" -- "$codemap" 2>/dev/null | cut -d' ' -f1)
    PROJECT_DATE=$(git log -1 --format="%ai" -- "$project_path" 2>/dev/null | cut -d' ' -f1)

    if [ -z "$CODEMAP_DATE" ] || [ -z "$PROJECT_DATE" ]; then
        echo "ℹ️  $project: 날짜 비교 불가"
        return
    fi

    CM_NUM=$(echo "$CODEMAP_DATE" | tr -d '-')
    PJ_NUM=$(echo "$PROJECT_DATE" | tr -d '-')
    DIFF=$(( PJ_NUM - CM_NUM ))

    if [ "$DIFF" -gt 3 ]; then
        echo "🔴 $project: codemap 오래됨 (codemap: $CODEMAP_DATE, 프로젝트: $PROJECT_DATE, ${DIFF}일 차이)"
        echo "   → /codemap-update $project 실행 권장"
    elif [ "$DIFF" -gt 0 ]; then
        echo "🟡 $project: codemap 약간 오래됨 (${DIFF}일 차이)"
    else
        echo "🟢 $project: codemap 최신 상태"
    fi
}

check_freshness "portfiq" ".claude/knowledge/codemap-portfiq.md" "projects/portfiq/"
check_freshness "lapaz" ".claude/knowledge/codemap-lapaz.md" "projects/lapaz-live/"
check_freshness "others" ".claude/knowledge/codemap-others.md" "projects/"

echo ""
echo "━━━ Knowledge 현황 ━━━"
ADR_COUNT=$(grep -c "^## ADR-" .claude/knowledge/decisions/README.md 2>/dev/null || echo 0)
MISTAKE_COUNT=$(grep -c "^## M-" .claude/knowledge/mistakes/README.md 2>/dev/null || echo 0)
PATTERN_COUNT=$(grep -c "^## P-" .claude/knowledge/patterns/README.md 2>/dev/null || echo 0)
echo "ADR: ${ADR_COUNT}건 | 실수: ${MISTAKE_COUNT}건 | 패턴: ${PATTERN_COUNT}건"
