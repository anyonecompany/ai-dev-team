#!/bin/bash
# PostToolUse 훅: UI 파일 수정 시 디자인 시스템 참조 넛지
# Write/Edit 도구로 UI 관련 파일이 수정되면 MASTER.md 참조를 상기시킴

INPUT=$(cat)

# Write/Edit 도구만 대상
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
if [[ "$TOOL" != *"Write"* ]] && [[ "$TOOL" != *"Edit"* ]] && [[ "$TOOL" != *"write"* ]] && [[ "$TOOL" != *"edit"* ]] && [[ "$TOOL" != *"str_replace"* ]] && [[ "$TOOL" != *"create"* ]]; then
    exit 0
fi

# 수정된 파일 경로 추출
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.path // .tool_input.file_path // ""')

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# UI 파일 확장자 확인
case "$FILE_PATH" in
    *.dart|*.tsx|*.jsx|*.css|*.scss|*.vue)
        # 프로젝트 감지
        PROJECT=""
        if echo "$FILE_PATH" | grep -qi "portfiq"; then
            PROJECT="portfiq"
        elif echo "$FILE_PATH" | grep -qi "la.paz\|lapaz"; then
            PROJECT="la-paz"
        fi

        # 디자인 시스템 존재 확인
        if [ -n "$PROJECT" ] && [ -f "design-system/$PROJECT/MASTER.md" ]; then
            # 5분 쿨다운
            COOLDOWN_FILE="/tmp/design-nudge-${PROJECT}"
            if [ -f "$COOLDOWN_FILE" ]; then
                LAST=$(cat "$COOLDOWN_FILE")
                NOW=$(date +%s)
                DIFF=$((NOW - LAST))
                if [ "$DIFF" -lt 300 ]; then
                    exit 0
                fi
            fi
            date +%s > "$COOLDOWN_FILE"

            cat << EOF
{
  "feedback": "🎨 UI 파일 수정 감지 ($PROJECT). design-system/$PROJECT/MASTER.md의 컬러/타이포/스페이싱 규칙을 따르고 있는지 확인하세요."
}
EOF
        fi
        ;;
esac

exit 0
