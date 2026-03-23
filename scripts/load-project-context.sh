#!/bin/bash
# 프로젝트 컨텍스트 로더
# 사용: ./scripts/load-project-context.sh portfiq
# 출력: 해당 프로젝트의 codemap + CLAUDE.md 요약

PROJECT=${1:-""}

if [ -z "$PROJECT" ]; then
    echo "사용법: $0 <project-name>"
    echo "사용 가능: portfiq, lapaz, adaptfitai, foundloop, seoroyeon"
    exit 1
fi

CODEMAP=""
CLAUDEMD=""

case "$PROJECT" in
    portfiq)
        CODEMAP=".claude/knowledge/codemap-portfiq.md"
        CLAUDEMD="projects/portfiq/CLAUDE.md"
        ;;
    lapaz|la-paz|lapaz-live)
        CODEMAP=".claude/knowledge/codemap-lapaz.md"
        CLAUDEMD="projects/la-paz/CLAUDE.md"
        ;;
    *)
        CODEMAP=".claude/knowledge/codemap-others.md"
        CLAUDEMD="projects/${PROJECT}/CLAUDE.md"
        ;;
esac

echo "━━━ 프로젝트: $PROJECT ━━━"

if [ -f "$CODEMAP" ]; then
    echo ""
    echo "📋 Codemap (요약):"
    sed -n '/^## 아키텍처/,/^## /p' "$CODEMAP" | head -20
    echo "..."
    sed -n '/^## 핵심 진입점/,/^## /p' "$CODEMAP" | head -15
else
    echo "⚠️ Codemap 없음: $CODEMAP"
fi

if [ -f "$CLAUDEMD" ]; then
    echo ""
    echo "📋 CLAUDE.md (요약):"
    head -40 "$CLAUDEMD"
else
    echo "⚠️ CLAUDE.md 없음: $CLAUDEMD"
fi

echo ""
echo "━━━ 최근 변경 ━━━"
git log --oneline -5 -- "projects/${PROJECT}/" 2>/dev/null || echo "git 이력 없음"
