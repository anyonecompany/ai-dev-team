#!/bin/bash
# UserPromptSubmit 훅: 워크플로우 규율 강제
# PLAN 없이 orchestrate 차단, Large에서 discuss 넛지, verify 없이 qa 넛지

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""')

# /orchestrate → PLAN.md 확인
if echo "$PROMPT" | grep -qi "^/orchestrate"; then
    PLAN_COUNT=$(find .planning -name "*-PLAN.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$PLAN_COUNT" -eq 0 ]; then
        cat << 'EOF'
{"feedback": "PLAN.md 없이 /orchestrate 실행 불가. 올바른 순서: /discuss -> /plan -> /orchestrate. Small 작업이면 /quick 또는 /auto 사용."}
EOF
        exit 0
    fi
fi

# /plan (Large) → CONTEXT.md 넛지
if echo "$PROMPT" | grep -qi "^/plan"; then
    if echo "$PROMPT" | grep -qi "전체\|아키텍처\|MVP\|리팩토링\|대규모\|전면\|complete\|full"; then
        CONTEXT_COUNT=$(find .planning -name "*-CONTEXT.md" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$CONTEXT_COUNT" -eq 0 ]; then
            cat << 'EOF'
{"feedback": "Large 작업 감지. /discuss를 먼저 실행하여 결정 사항을 잠그면 /plan 품질이 향상됨. 건너뛰려면 그대로 진행 가능."}
EOF
            exit 0
        fi
    fi
fi

# /qa → verify-loop 넛지
if echo "$PROMPT" | grep -qi "^/qa$\|^/qa "; then
    UAT_COUNT=$(find .planning -name "*-UAT.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$UAT_COUNT" -eq 0 ]; then
        cat << 'EOF'
{"feedback": "/verify-loop을 먼저 실행하여 자동 검증 통과 후 /qa 실행 권장."}
EOF
        exit 0
    fi
fi

exit 0
