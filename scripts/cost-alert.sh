#!/bin/bash
# 비용 알림: 세션 내 도구 호출이 임계치를 넘으면 경고
# 사용: ./scripts/cost-alert.sh [임계치 — 기본 500]

THRESHOLD=${1:-500}
LOG_FILE="$HOME/.claude/logs/tool-usage.jsonl"
TODAY=$(date +%Y-%m-%d)

if [ ! -f "$LOG_FILE" ]; then
    echo "로그 파일 없음"
    exit 0
fi

TODAY_COUNT=$(grep "$TODAY" "$LOG_FILE" 2>/dev/null | wc -l | tr -d ' ')

echo "━━━ 비용 알림 ━━━"
echo "오늘 도구 호출: ${TODAY_COUNT}회 (임계치: ${THRESHOLD}회)"

if [ "$TODAY_COUNT" -gt "$THRESHOLD" ]; then
    echo "🔴 경고: 오늘 도구 호출이 임계치(${THRESHOLD})를 초과했습니다!"
    echo ""
    echo "도구별 분포:"
    grep "$TODAY" "$LOG_FILE" | jq -r '.tool' | sort | uniq -c | sort -rn | head -5
    echo ""
    echo "권장 조치:"
    echo "  1. /compact 실행하여 컨텍스트 정리"
    echo "  2. Read 비율이 높으면 codemap 갱신"
    echo "  3. 반복 작업이 있으면 스킬/스크립트로 자동화"
elif [ "$TODAY_COUNT" -gt $(( THRESHOLD * 80 / 100 )) ]; then
    echo "🟡 주의: 임계치의 80% 도달"
else
    echo "🟢 정상 범위"
fi

echo ""
echo "━━━ 최근 7일 추이 ━━━"
for i in $(seq 6 -1 0); do
    DAY=$(date -v-${i}d +%Y-%m-%d 2>/dev/null || date -d "$i days ago" +%Y-%m-%d 2>/dev/null || echo "")
    if [ -n "$DAY" ]; then
        COUNT=$(grep "$DAY" "$LOG_FILE" 2>/dev/null | wc -l | tr -d ' ')
        BAR=$(printf '%*s' $((COUNT / 10)) '' | tr ' ' '█')
        printf "  %s: %4d회 %s\n" "$DAY" "$COUNT" "$BAR"
    fi
done
