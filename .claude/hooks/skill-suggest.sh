#!/bin/bash
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""' | tr '[:upper:]' '[:lower:]')

SUGGESTIONS=""

echo "$PROMPT" | grep -qE "(portfiq|포트픽|etf|briefing|브리핑|portfolio|포트폴리오|gemini|projects/portfiq)" && SUGGESTIONS="${SUGGESTIONS}portfiq-dev "
echo "$PROMPT" | grep -qE "(la.?paz|라파즈|football|축구|match|경기|live|실시간|projects/la.?paz)" && SUGGESTIONS="${SUGGESTIONS}lapaz-dev "
echo "$PROMPT" | grep -qE "(security|보안|auth|인증|token|secret|취약|vulnerability)" && SUGGESTIONS="${SUGGESTIONS}security-review "
echo "$PROMPT" | grep -qE "(deploy|배포|ci.?cd|fly.?io|vercel|railway|release)" && SUGGESTIONS="${SUGGESTIONS}deployment "
echo "$PROMPT" | grep -qE "(디자인|design|ui|ux|스타일|style|컬러|color|폰트|font|레이아웃|layout|glassmorphism|theme|테마)" && SUGGESTIONS="${SUGGESTIONS}ui-ux-pro-max "

SUGGESTIONS=$(echo "$SUGGESTIONS" | tr ' ' '\n' | sort -u | tr '\n' ' ' | xargs)

if [ -n "$SUGGESTIONS" ]; then
    cat << EOF
{"feedback": "관련 스킬 감지: ${SUGGESTIONS}"}
EOF
fi
exit 0
