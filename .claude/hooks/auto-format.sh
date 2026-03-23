#!/bin/bash
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""')

if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
    exit 0
fi

case "$FILE_PATH" in
    *.py)
        command -v ruff &>/dev/null && ruff format "$FILE_PATH" 2>/dev/null && ruff check --fix "$FILE_PATH" 2>/dev/null
        ;;
    *.ts|*.tsx|*.js|*.jsx)
        command -v prettier &>/dev/null && prettier --write "$FILE_PATH" 2>/dev/null
        ;;
    *.dart)
        command -v dart &>/dev/null && dart format "$FILE_PATH" 2>/dev/null
        ;;
esac
exit 0
