#!/bin/bash
# Notion 현황 페이지 갱신 CLI
# 사용: ./scripts/update-notion-status.sh [update|version|both] [버전] [설명]

ACTION=${1:-"update"}
VERSION=${2:-""}
DESC=${3:-""}

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"

case "$ACTION" in
    update)
        python3 integrations/notion/status_updater.py update
        ;;
    version)
        if [ -z "$VERSION" ] || [ -z "$DESC" ]; then
            echo "사용법: $0 version v4.0.0 '설명'"
            exit 1
        fi
        python3 integrations/notion/status_updater.py version "$VERSION" "$DESC"
        ;;
    both)
        if [ -z "$VERSION" ] || [ -z "$DESC" ]; then
            echo "사용법: $0 both v4.0.0 '설명'"
            exit 1
        fi
        python3 integrations/notion/status_updater.py both "$VERSION" "$DESC"
        ;;
    *)
        echo "사용법: $0 [update|version|both] [버전] [설명]"
        ;;
esac
