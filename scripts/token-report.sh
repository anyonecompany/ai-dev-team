#!/bin/bash
# 토큰 사용량 리포트
# 사용: ./scripts/token-report.sh [today|week|all]

PERIOD=${1:-"today"}
LOG_FILE="$HOME/.claude/logs/tool-usage.jsonl"

if [ ! -f "$LOG_FILE" ]; then
    echo "⚠️ 로그 파일 없음. 도구 사용 후 생성됩니다."
    exit 0
fi

case "$PERIOD" in
    today)
        FILTER_DATE=$(date +%Y-%m-%d)
        TITLE="오늘"
        ;;
    week)
        FILTER_DATE=$(date -v-7d +%Y-%m-%d 2>/dev/null || date -d '7 days ago' +%Y-%m-%d)
        TITLE="최근 7일"
        ;;
    all)
        FILTER_DATE="1970-01-01"
        TITLE="전체"
        ;;
esac

echo "━━━ 도구 사용량 리포트 ($TITLE) ━━━"
echo ""

echo "📊 도구별 호출 횟수:"
grep "$FILTER_DATE" "$LOG_FILE" 2>/dev/null | \
  jq -r '.tool' | sort | uniq -c | sort -rn | head -15

echo ""
echo "📊 세션별 호출 횟수:"
grep "$FILTER_DATE" "$LOG_FILE" 2>/dev/null | \
  jq -r '.session' | sort | uniq -c | sort -rn | head -10

echo ""
echo "📊 시간대별 활동:"
grep "$FILTER_DATE" "$LOG_FILE" 2>/dev/null | \
  jq -r '.timestamp[:13]' | sort | uniq -c | head -24

echo ""
TOTAL=$(grep "$FILTER_DATE" "$LOG_FILE" 2>/dev/null | wc -l)
echo "총 도구 호출: $TOTAL 회"
