#!/bin/bash
# Nyquist 검증: PLAN.md의 품질 게이트 체크
# 사용: ./scripts/nyquist-check.sh .planning/{작업명}-PLAN.md

PLAN_FILE=${1:-""}

if [ -z "$PLAN_FILE" ] || [ ! -f "$PLAN_FILE" ]; then
    echo "사용법: $0 <PLAN.md 파일 경로>"
    exit 1
fi

echo "━━━ Nyquist 검증: $(basename $PLAN_FILE) ━━━"

PASS=true

# 1. 테스트 피드백 루프
if grep -qi "pytest\|flutter test\|npm test\|ruff\|lint\|테스트.*실행\|검증.*명령" "$PLAN_FILE"; then
    echo "✅ 테스트 피드백 루프 존재"
else
    echo "❌ 테스트 피드백 루프 없음 — 검증 방법을 추가하세요"
    PASS=false
fi

# 2. 완료 조건
if grep -qi "완료 조건\|completion\|done when\|\- \[ \]" "$PLAN_FILE"; then
    echo "✅ 완료 조건 존재"
else
    echo "❌ 완료 조건 없음"
    PASS=false
fi

# 3. 수정 범위
if grep -qi "수정 가능\|수정 금지\|범위\|scope\|modified\|untouched" "$PLAN_FILE"; then
    echo "✅ 수정 범위 명시"
else
    echo "❌ 수정 범위 없음"
    PASS=false
fi

# 4. 롤백 (권장)
if grep -qi "rollback\|되돌\|revert" "$PLAN_FILE"; then
    echo "✅ 롤백 방안 있음"
else
    echo "⚠️ 롤백 방안 없음 (권장)"
fi

echo ""
if [ "$PASS" = true ]; then
    echo "🟢 Nyquist 검증 통과"
else
    echo "🔴 Nyquist 검증 실패 — 계획 보완 필요"
fi
