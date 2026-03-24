#!/bin/bash
# Notion 태스크 큐 CLI 래퍼
# 사용: ./scripts/notion-tasks.sh [add|next|update|status] [args...]

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"
python3 integrations/notion/task_manager.py "$@"
